"""
Unit and algorithmic tests for the VoiceShield Sentinel AI Agent.
"""
import pytest
from ml.agent.sentinel import SentinelAgent, SentinelVerdict
from ml.agent.tools import ThreatIntelRegistry, SemanticFraudAnalyzer, SentinelToolRegistry
from ml.agent.config import SentinelConfig, SentinelConfigManager


class TestSentinelTools:
    def test_threat_intel_known_scam_number(self):
        result = ThreatIntelRegistry.lookup("+919876543210")
        assert result["reputation"] == "MALICIOUS"
        assert result["risk_multiplier"] == 2.0
        assert "Bank Impersonation" in result["category"]

    def test_threat_intel_clean_number(self):
        result = ThreatIntelRegistry.lookup("+919988776655")
        assert result["reputation"] == "CLEAN"
        assert result["risk_multiplier"] == 0.8

    def test_threat_intel_anonymous_caller(self):
        result = ThreatIntelRegistry.lookup(None)
        assert result["reputation"] == "UNKNOWN"
        assert result["risk_multiplier"] == 1.1

    def test_semantic_digital_arrest_and_extortion(self):
        transcript = "This is CBI officer calling. You are under digital arrest. Transfer money to safe custody account immediately or police aayegi."
        result = SemanticFraudAnalyzer.analyze(transcript)
        assert result["semantic_score"] >= 65.0
        assert "Authority Impersonation & Digital Arrest" in result["intent_categories"]
        assert "Financial Redirection & Extortion" in result["intent_categories"]

    def test_semantic_hinglish_and_credential_harvesting(self):
        transcript = "Thaana kotwali se warrant hai. Jaldi se apna OTP aur bank PIN share karo turant."
        result = SemanticFraudAnalyzer.analyze(transcript)
        assert result["semantic_score"] >= 70.0
        assert "Credential & Identity Harvesting" in result["intent_categories"]
        assert "Authority Impersonation & Digital Arrest" in result["intent_categories"]

    def test_semantic_defensive_negation_filter(self):
        # Educational bank warnings should not produce a false positive scam score
        transcript = "Bank awareness notice: Never share your OTP, password or UPI PIN with anyone claiming to be police."
        result = SemanticFraudAnalyzer.analyze(transcript)
        assert result["semantic_score"] == 0.0
        assert len(result["intent_categories"]) == 0

    def test_semantic_clean_transcript(self):
        transcript = "Hi grandma, hope you are doing well. We are coming to visit this Sunday for dinner."
        result = SemanticFraudAnalyzer.analyze(transcript)
        assert result["semantic_score"] == 0.0
        assert len(result["intent_categories"]) == 0


class TestSentinelAgentCycle:
    def test_benign_call_allows_traffic(self):
        agent = SentinelAgent()
        verdict: SentinelVerdict = agent.run_cycle(
            session_id="test_benign_1",
            window_seq=1,
            acoustic_score=10.0,
            transcript="Hello, just checking what time the library opens today.",
            caller_id="+919988776655",
        )
        assert verdict.action == "ALLOW"
        assert verdict.verdict == "SAFE"
        assert verdict.composite_threat_score < 25.0
        assert len(verdict.trace) == 4
        assert verdict.caller_reputation == "CLEAN"

    def test_critical_threat_triggers_alert_and_anchor_never_drops_call(self):
        agent = SentinelAgent()
        verdict: SentinelVerdict = agent.run_cycle(
            session_id="test_scam_critical",
            window_seq=1,
            acoustic_score=85.0,  # High synthetic voice score
            transcript="This is CBI customs digital arrest. Transfer 50000 to safe account or be arrested immediately.",
            caller_id="+919876543210",  # Malicious caller registry
        )
        # Invariant: Action is ALERT_AND_ANCHOR, call is NOT dropped
        assert verdict.action == "ALERT_AND_ANCHOR"
        assert verdict.verdict in ("ATTACK_CONFIRMED", "THREAT_DETECTED")
        assert verdict.composite_threat_score >= 75.0
        assert verdict.intervention_details["call_terminated"] is False
        assert verdict.intervention_details["is_advisory_only"] is True

    def test_ambiguous_call_triggers_cognitive_challenge(self):
        agent = SentinelAgent()
        verdict: SentinelVerdict = agent.run_cycle(
            session_id="test_ambiguous",
            window_seq=1,
            acoustic_score=62.0,
            transcript="I am calling regarding a refund on your account.",
            caller_id=None,
        )
        assert verdict.action == "CHALLENGE"
        assert "challenge_prompt" in verdict.intervention_details

    def test_adaptive_weight_when_no_transcript(self):
        agent = SentinelAgent()
        # When transcript is empty, acoustic weight should adapt to 1.0 (no dilution)
        verdict = agent.run_cycle(
            session_id="test_silent_chunk",
            window_seq=1,
            acoustic_score=90.0,
            transcript="",
            caller_id=None,
        )
        assert verdict.weights_applied["acoustic"] == 1.0
        assert verdict.weights_applied["semantic"] == 0.0
        assert verdict.composite_threat_score >= 80.0

    def test_dynamic_weight_tuning(self):
        agent = SentinelAgent()
        # High acoustic score but zero semantic
        custom_config = SentinelConfig(
            acoustic_weight=0.90,
            semantic_weight=0.10,
            challenge_threshold=40.0,
            critical_alert_threshold=70.0,
        )
        verdict = agent.run_cycle(
            session_id="test_weight_tuning",
            window_seq=1,
            acoustic_score=80.0,
            transcript="Neutral conversational text.",
            caller_id=None,
            override_config=custom_config,
        )
        assert verdict.composite_threat_score >= 70.0
        assert verdict.action == "ALERT_AND_ANCHOR"
