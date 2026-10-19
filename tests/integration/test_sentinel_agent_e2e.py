"""
Integration & End-to-End Tests for VoiceShield Autonomous Sentinel AI Agent.

Tests cover:
1. Multi-turn call state accumulation (history progression over chunks).
2. End-to-end WebSocket inference protocol embedding Sentinel Agent decisions.
3. Fast-path REST deliberation API validation.
4. Active advisory countermeasure trigger verification (ALLOW, CHALLENGE, ALERT_AND_ANCHOR).
5. Dynamic Sentinel Agent config REST APIs (GET & PUT /api/config/agent).
6. Whisper ASR transcription API (POST /api/transcribe).
"""
import asyncio
import json
import io
import wave
import numpy as np
import pytest
from fastapi.testclient import TestClient

from ml.server.app import app
from ml.agent.sentinel import SentinelAgent, SentinelVerdict
from ml.pipeline.results import build_score_response
from ml.server.protocol import parse_metadata, ChunkMetadata, validate_audio_payload


client = TestClient(app)


class TestSentinelIntegration:
    """Tests the interaction of the Agent with the inference and results pipeline."""

    def test_pipeline_results_builder_embeds_agent(self):
        """Verify build_score_response automatically executes the Sentinel Agent."""
        mock_inference_result = {
            "audio_duration_ms": 3000,
            "total_latency_ms": 42.5,
            "real_time_factor": 0.014,
            "dhwani": {"synthetic_probability": 0.88},
            "indic": {"synthetic_probability": 0.85},
            "prosody": {"overall_prosody_risk": 0.90},
            "custom_deepfake": None,
            "speaker_verification": {"status": "MATCH", "speaker_id": "target_user"},
            "audio_quality": {"snr_db": 28.0},
        }

        score_doc = build_score_response(
            session_id="session_integ_test_1",
            sequence=1,
            timestamp_ms=1700000000000,
            inference_result=mock_inference_result,
            caller_id="+919876543210",
            transcript="Urgent customs police inquiry, pay 20000 rupees now or be arrested",
        )

        assert "agent" in score_doc
        agent_data = score_doc["agent"]
        assert agent_data["action"] == "ALERT_AND_ANCHOR"
        assert agent_data["verdict"] in ("THREAT_DETECTED", "ATTACK_CONFIRMED")
        assert agent_data["composite_threat_score"] >= 75.0
        assert agent_data["caller_reputation"] == "MALICIOUS"
        assert len(agent_data["trace"]) == 4

    def test_multiturn_agent_history_accumulation(self):
        """
        Verify that an attacker trying to probe with low acoustic score initially,
        then escalating to social engineering, causes cumulative threat escalation.
        """
        agent = SentinelAgent()
        sess_id = "multiturn_scam_call_007"

        # Chunk 1: Pleasant greeting, clean acoustic
        v1 = agent.run_cycle(
            session_id=sess_id,
            window_seq=1,
            acoustic_score=15.0,
            transcript="Hello, am I speaking with Mr. Sharma?",
            caller_id="+919876543210",  # Malicious caller registry
        )
        assert v1.action in ("MONITOR", "CHALLENGE")

        # Chunk 2: Attacker escalates urgency
        v2 = agent.run_cycle(
            session_id=sess_id,
            window_seq=2,
            acoustic_score=55.0,
            transcript="This is urgent regarding your bank account deactivation.",
            caller_id="+919876543210",
        )
        assert v2.action in ("CHALLENGE", "ALERT_AND_ANCHOR")

        # Chunk 3: Attacker demands immediate credential extraction
        v3 = agent.run_cycle(
            session_id=sess_id,
            window_seq=3,
            acoustic_score=80.0,
            transcript="Share the OTP right now or legal arrest action will be taken immediately!",
            caller_id="+919876543210",
        )
        assert v3.action == "ALERT_AND_ANCHOR"
        assert v3.verdict in ("ATTACK_CONFIRMED", "THREAT_DETECTED")
        assert v3.intervention_details["urgency"] == "CRITICAL"
        assert v3.intervention_details["call_terminated"] is False


class TestSentinelEndToEndAPI:
    """Tests the full HTTP & REST API layer."""

    def test_e2e_benign_deliberation_api(self):
        response = client.post(
            "/api/agent/deliberate",
            json={
                "session_id": "e2e_benign_session",
                "window_seq": 1,
                "acoustic_score": 12.0,
                "transcript": "Good morning professor, sending you the project draft for review.",
                "caller_id": "+919988776655",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        verdict = data["verdict"]
        assert verdict["action"] == "ALLOW"
        assert verdict["verdict"] == "SAFE"
        assert verdict["composite_threat_score"] < 25.0

    def test_e2e_social_engineering_challenge_api(self):
        response = client.post(
            "/api/agent/deliberate",
            json={
                "session_id": "e2e_challenge_session",
                "window_seq": 1,
                "acoustic_score": 35.0,
                "transcript": "Please wire the deposit right now to avoid service termination.",
                "caller_id": None,
            },
        )
        assert response.status_code == 200
        data = response.json()
        verdict = data["verdict"]
        assert verdict["action"] in ("CHALLENGE", "MONITOR")
        if verdict["action"] == "CHALLENGE":
            assert "challenge_prompt" in verdict["intervention_details"]

    def test_e2e_critical_attack_advisory_alert_api(self):
        response = client.post(
            "/api/agent/deliberate",
            json={
                "session_id": "e2e_critical_session",
                "window_seq": 1,
                "acoustic_score": 88.0,
                "transcript": "Narcotics police raid warrant issued. Give OTP immediately do not disconnect.",
                "caller_id": "+919876543210",
            },
        )
        assert response.status_code == 200
        data = response.json()
        verdict = data["verdict"]
        assert verdict["action"] == "ALERT_AND_ANCHOR"
        assert verdict["composite_threat_score"] >= 75.0
        assert verdict["intervention_details"]["call_terminated"] is False

    def test_e2e_agent_config_get_and_put(self):
        # 1. GET config
        res_get = client.get("/api/config/agent")
        assert res_get.status_code == 200
        cfg = res_get.json()["config"]
        assert "acoustic_weight" in cfg
        assert "semantic_weight" in cfg

        # 2. PUT valid config
        res_put = client.put(
            "/api/config/agent",
            json={
                "acoustic_weight": 0.60,
                "semantic_weight": 0.40,
                "challenge_threshold": 45.0,
                "critical_alert_threshold": 80.0,
            },
        )
        assert res_put.status_code == 200
        updated = res_put.json()["config"]
        assert updated["acoustic_weight"] == 0.60
        assert updated["semantic_weight"] == 0.40

        # Reset to defaults
        client.put(
            "/api/config/agent",
            json={
                "acoustic_weight": 0.50,
                "semantic_weight": 0.50,
                "challenge_threshold": 50.0,
                "critical_alert_threshold": 75.0,
            },
        )

    def test_e2e_transcribe_endpoint(self):
        # Generate a small in-memory 16kHz WAV file of 0.5s silence
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(8000, dtype=np.int16).tobytes())
        wav_bytes = wav_buffer.getvalue()

        response = client.post(
            "/api/transcribe",
            files={"audio": ("test_silence.wav", wav_bytes, "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transcript" in data
        assert "detectedLanguage" in data


class TestGatewayProtocolAgentCompatibility:
    """Ensures metadata framing for agent-assisted chunks functions as specified."""

    def test_parse_metadata_with_agent_fields(self):
        raw_json = json.dumps({
            "type": "audio.chunk",
            "session_id": "session_proto_agent_1",
            "sequence": 4,
            "timestamp_ms": 1728000000,
            "duration_ms": 3000,
            "sample_rate": 48000,
            "channels": 1,
            "encoding": "pcm_s16le",
            "bytes": 288000,
            "caller_id": "+919876543210",
            "transcript": "Urgent verification call",
        })
        meta = parse_metadata(raw_json)
        assert meta.caller_id == "+919876543210"
        assert meta.transcript == "Urgent verification call"
        assert meta.sequence == 4
