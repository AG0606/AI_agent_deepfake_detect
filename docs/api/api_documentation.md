# VoiceShield AI — ML Server & Sentinel Agent API Documentation

The VoiceShield ML Inference Service provides real-time acoustic deepfake detection, speech transcription, prosody analysis, speaker verification, and the Autonomous Sentinel AI Agent. It exposes high-performance FastAPI REST routes and a low-latency bidirectional WebSocket endpoint (port `8011`).

---

## 1. System Health & Readiness

### GET `/health`
Returns process liveness and model availability flags.

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "voiceshield-ml-service",
  "version": "1.0.0",
  "uptime_s": 142.5,
  "models": {
    "indic": true,
    "dhwani": true,
    "custom_deepfake": false,
    "prosody": true,
    "speaker": true
  }
}
```

### GET `/ready`
Readiness probe for load balancers. Returns 200 only if at least one deepfake detector is operational; returns 503 if unavailable.

---

## 2. Autonomous Sentinel AI Agent

### POST `/api/agent/deliberate`
Invokes the Sense → Reason → Act cycle of the Sentinel Agent for an incoming call segment.

**Request Body:**
```json
{
  "session_id": "call-sess-98231",
  "window_seq": 3,
  "acoustic_score": 85.5,
  "transcript": "This is CBI customs digital arrest. Pay clearance fine immediately.",
  "caller_id": "+919876543210"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "verdict": {
    "session_id": "call-sess-98231",
    "window_seq": 3,
    "timestamp_ms": 1728000000000,
    "verdict": "ATTACK_CONFIRMED",
    "action": "ALERT_AND_ANCHOR",
    "composite_threat_score": 88.4,
    "acoustic_score": 85.5,
    "semantic_score": 80.0,
    "caller_reputation": "MALICIOUS",
    "reasoning_summary": "Critical threat detected (88.4/100 >= 75.0). Acoustic synthetic evidence (85.5%) and scam intent (80.0%) corroboration.",
    "trace": [
      {
        "step": 1,
        "thought": "Evaluating caller identity [+919876543210] against threat intelligence registry.",
        "tool_executed": "threat_intel_lookup",
        "tool_output": "Reputation: MALICIOUS, Multiplier: 2.0"
      },
      {
        "step": 2,
        "thought": "Perceiving acoustic evidence from multi-model neural ensemble (sequence 3).",
        "tool_executed": "acoustic_verification",
        "tool_output": "Acoustic Deepfake Score: 85.5% (HIGH confidence)"
      },
      {
        "step": 3,
        "thought": "Analyzing conversational scam intent & psychological manipulation (68 chars transcribed).",
        "tool_executed": "semantic_fraud_analysis",
        "tool_output": "Semantic Scam Risk: 80.0% (Authority Impersonation & Digital Arrest, Financial Redirection & Extortion)"
      },
      {
        "step": 4,
        "thought": "Deliberated state: Action selected: ALERT_AND_ANCHOR (Advisory Mode - Call Protected).",
        "tool_executed": "countermeasure_dispatch",
        "tool_output": "Dispatched advisory ALERT_AND_ANCHOR action"
      }
    ],
    "intervention_details": {
      "session_id": "call-sess-98231",
      "action": "ALERT_AND_ANCHOR",
      "reason": "Critical threat detected...",
      "urgency": "CRITICAL",
      "is_advisory_only": true,
      "call_terminated": false,
      "evidence_anchor": {
        "anchored_on_chain": true,
        "advisory": "High probability synthetic impersonation / extortion detected. Evidence commitment anchored."
      }
    },
    "weights_applied": {
      "acoustic": 0.5,
      "semantic": 0.5,
      "intel_multiplier": 2.0
    }
  }
}
```

### GET `/api/config/agent`
Retrieves Sentinel agent thresholds and dynamic weights.

### PUT `/api/config/agent`
Updates Sentinel thresholds and weights in memory with bounds validation.

**Request Body:**
```json
{
  "acoustic_weight": 0.60,
  "semantic_weight": 0.40,
  "challenge_threshold": 45.0,
  "critical_alert_threshold": 80.0
}
```

---

## 3. Acoustic Fusion Policy

### GET `/api/config/fusion`
Returns configured detector weights for the `voiceshield-evidence-v1` policy.

### PUT `/api/config/fusion`
Updates fusion weights (must sum to 1.0).

---

## 4. Audio Transcription & Pipeline

### POST `/api/transcribe`
Transcribes an uploaded audio file using Whisper ASR.
- Content-Type: `multipart/form-data`
- Field: `audio` (file)

### POST `/api/inference/pipeline`
Executes full windowed multi-model inference and pooling on an audio file (up to 60s).

### POST `/api/inference/{model_name}`
Executes a single model adapter (`indic`, `dhwani`, `custom-deepfake`, `prosody`, `speaker`).

### GET `/api/models`
Returns individual model load status, version, and diagnostic reason.

---

## 5. Speaker Enrollment

### POST `/api/speaker/enroll`
Enrolls a reference voice sample into the ECAPA speaker database (`models/enrolled_speakers.npz`).
- Form field: `speaker_id`
- Form field: `audio` (file)

### POST `/api/speaker/enroll-directory`
Recursively scans and enrolls all `.wav` audio files in a given directory path.

---

## 6. Real-Time Telephony WebSocket (`ws://localhost:8011/`)

The Media Gateway connects via WebSocket. For each 3-second audio window, the Gateway sends two frames:

1. **Text Frame (JSON metadata):**
```json
{
  "type": "audio.chunk",
  "session_id": "call_123456",
  "sequence": 1,
  "timestamp_ms": 1728000000000,
  "duration_ms": 3000,
  "sample_rate": 48000,
  "channels": 1,
  "encoding": "pcm_s16le",
  "bytes": 288000,
  "caller_id": "+919876543210",
  "transcript": "Optional streaming transcript"
}
```

2. **Binary Frame:**
Raw 48kHz mono 16-bit PCM bytes (288,000 bytes).

3. **Server Response Frame (JSON):**
```json
{
  "type": "score",
  "window_seq": 1,
  "metadata": {
    "session_id": "call_123456",
    "sequence": 1
  },
  "backend": "1.0.0",
  "audio": {
    "input_sample_rate": 48000,
    "model_sample_rate": 16000,
    "duration_ms": 3000,
    "timestamp_ms": 1728000000000
  },
  "inference_ms": 85,
  "real_time_factor": 0.028,
  "signals": {
    "deepfake_probability": 0.88,
    "indic": { "synthetic_probability": 0.85, "genuine_probability": 0.15 },
    "dhwani": { "synthetic_probability": 0.89, "genuine_probability": 0.11 },
    "prosody_analysis": { "overall_prosody_risk": 0.72 },
    "speaker_match": { "status": "no_enrollment" }
  },
  "fusion": {
    "aiGeneratedScore": 0.88,
    "method": "weighted_mean",
    "policy_version": "voiceshield-evidence-v1"
  },
  "risk": {
    "score": 88.0,
    "level": "HIGH",
    "recommended_action": "SECONDARY_VERIFICATION"
  },
  "agent": {
    "action": "ALERT_AND_ANCHOR",
    "verdict": "THREAT_DETECTED",
    "composite_threat_score": 88.4,
    "intervention_details": {
      "urgency": "CRITICAL",
      "call_terminated": false,
      "is_advisory_only": true
    }
  }
}
```
