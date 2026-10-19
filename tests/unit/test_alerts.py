import sys
from pathlib import Path

# Add project root and backend to sys.path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.services.prevention_service import trigger_prevention
from ml.agent.tools import SentinelToolRegistry


class TestBackendAlertsAndPrevention:
    def test_trigger_prevention_high(self):
        res = trigger_prevention(85, "HIGH")
        assert res["status"] == "TRANSACTION_HELD"
        assert "MFA" in res["verification_required"]
        assert "SUPERVISOR_APPROVAL" in res["verification_required"]

    def test_trigger_prevention_medium(self):
        res = trigger_prevention(55, "MEDIUM")
        assert res["status"] == "WARNING"
        assert "MFA" in res["verification_required"]
        assert "SUPERVISOR_APPROVAL" not in res["verification_required"]

    def test_trigger_prevention_low(self):
        res = trigger_prevention(15, "LOW")
        assert res["status"] == "ALLOWED"
        assert len(res["verification_required"]) == 0


class TestSentinelCountermeasureDispatch:
    def test_dispatch_allow(self):
        result = SentinelToolRegistry.execute_countermeasure_dispatch(
            action="ALLOW",
            reason="Conversational context benign.",
            session_id="test_sess_allow",
        )
        assert result.success is True
        assert result.data["action"] == "ALLOW"
        assert result.data["urgency"] == "LOW"
        assert result.data["call_terminated"] is False

    def test_dispatch_challenge(self):
        result = SentinelToolRegistry.execute_countermeasure_dispatch(
            action="CHALLENGE",
            reason="Anomalous prosody and elevated risk.",
            session_id="test_sess_challenge",
        )
        assert result.success is True
        assert result.data["action"] == "CHALLENGE"
        assert result.data["urgency"] == "HIGH"
        assert "challenge_prompt" in result.data

    def test_dispatch_alert_and_anchor(self):
        result = SentinelToolRegistry.execute_countermeasure_dispatch(
            action="ALERT_AND_ANCHOR",
            reason="Confirmed high threat synthetic impersonation.",
            session_id="test_sess_alert",
        )
        assert result.success is True
        assert result.data["action"] == "ALERT_AND_ANCHOR"
        assert result.data["urgency"] == "CRITICAL"
        assert result.data["evidence_anchor"]["anchored_on_chain"] is True
        assert result.data["call_terminated"] is False

    def test_dispatch_terminate_and_anchor_advisory(self):
        result = SentinelToolRegistry.execute_countermeasure_dispatch(
            action="TERMINATE_AND_ANCHOR",
            reason="Critical fraud threshold reached.",
            session_id="test_sess_term",
        )
        assert result.success is True
        assert result.data["action"] == "TERMINATE_AND_ANCHOR"
        assert result.data["urgency"] == "CRITICAL"
        assert result.data["call_terminated"] is False
