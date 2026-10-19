import sys
from pathlib import Path

# Add project root and backend to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.services.risk_service import calculate_risk
from ml.pipeline.fusion import fuse, validate_weights, set_weights, DEFAULT_WEIGHTS


class TestBackendRiskService:
    def test_calculate_risk_low(self):
        res = calculate_risk(
            deepfake_prob=0.1,
            speaker_match=0.9,  # mismatch = 0.1
            prosody_anomaly=0.1,
            context_risk=0.1,
        )
        assert res["risk_level"] == "LOW"
        assert res["recommended_action"] == "CONTINUE"
        assert res["risk_score"] < 40
        assert "fusion_breakdown" in res

    def test_calculate_risk_medium(self):
        res = calculate_risk(
            deepfake_prob=0.5,
            speaker_match=0.5,  # mismatch = 0.5
            prosody_anomaly=0.4,
            context_risk=0.5,
        )
        assert res["risk_level"] == "MEDIUM"
        assert res["recommended_action"] == "WARNING_SECONDARY_VERIFICATION"
        assert 40 <= res["risk_score"] < 75

    def test_calculate_risk_high(self):
        res = calculate_risk(
            deepfake_prob=0.95,
            speaker_match=0.1,  # mismatch = 0.9
            prosody_anomaly=0.8,
            context_risk=0.9,
        )
        assert res["risk_level"] == "HIGH"
        assert res["recommended_action"] == "BLOCK_AND_ESCALATE"
        assert res["risk_score"] >= 75


class TestPipelineFusion:
    def test_validate_default_weights(self):
        validated = validate_weights(DEFAULT_WEIGHTS)
        assert sum(validated.values()) == 1.0

    def test_fuse_clean_inference(self):
        set_weights({"indic": 0.5, "dhwani": 0.5, "customDeepfake": 0.0, "prosody": 0.0})
        inference = {
            "dhwani": {"synthetic_probability": 0.10},
            "indic": {"synthetic_probability": 0.12},
            "prosody": {"overall_prosody_risk": 0.08},
            "audio_quality": {"eligible": True, "reasons": []},
        }
        fusion, detectors, risk = fuse(inference)
        assert fusion is not None
        assert fusion["aiGeneratedScore"] < 0.20
        assert risk["level"] == "LOW"
        assert risk["status"] == "scored"

    def test_fuse_high_risk_disagreement(self):
        inference = {
            "dhwani": {"synthetic_probability": 0.95},
            "indic": {"synthetic_probability": 0.10},
            "audio_quality": {"eligible": True, "reasons": []},
        }
        fusion, detectors, risk = fuse(inference)
        assert fusion is not None
        assert "detector_disagreement" in risk["reasons"]
        assert risk["level"] == "REVIEW"
