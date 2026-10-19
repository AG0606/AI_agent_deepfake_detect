"""
VoiceShield Sentinel Agent Core.

Autonomous Sense-Reason-Act loop for real-time cyber-fraud & deepfake telephony defense.
Combines acoustic neural ensemble models, advanced conversational scam intent scoring,
and OSINT caller threat intelligence.

Safety Invariant:
  The agent operates strictly in ADVISORY MODE. It NEVER drops or terminates telephony calls.
  High threat actions trigger high-visibility alerts (ALERT_AND_ANCHOR) and cryptographic
  blockchain commitments.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from ml.agent.tools import SentinelToolRegistry, ToolResult
from ml.agent.config import sentinel_config_manager, SentinelConfig


class DecisionTrace(BaseModel):
    step: int
    thought: str
    tool_executed: str
    tool_output: str


class SentinelVerdict(BaseModel):
    session_id: str
    window_seq: int
    timestamp_ms: int
    verdict: str  # SAFE | SUSPICIOUS | THREAT_DETECTED | ATTACK_CONFIRMED
    action: str   # ALLOW | MONITOR | CHALLENGE | ALERT_AND_ANCHOR (NEVER drops call)
    composite_threat_score: float  # 0.0 to 100.0
    acoustic_score: float
    semantic_score: float
    caller_reputation: str
    reasoning_summary: str
    trace: List[DecisionTrace]
    intervention_details: Dict[str, Any]
    weights_applied: Dict[str, float] = Field(default_factory=dict)


class SentinelAgent:
    """
    Autonomous Anti-Fraud Sentinel Agent.

    Action space:
      a_t in {ALLOW, MONITOR, CHALLENGE, ALERT_AND_ANCHOR}
    """

    def __init__(self):
        self.session_history: Dict[str, List[Dict[str, Any]]] = {}

    def run_cycle(
        self,
        session_id: str,
        window_seq: int,
        acoustic_score: Optional[float],
        detector_breakdown: Optional[Dict[str, Any]] = None,
        transcript: Optional[str] = None,
        caller_id: Optional[str] = None,
        timestamp_ms: Optional[int] = None,
        override_config: Optional[SentinelConfig] = None,
    ) -> SentinelVerdict:
        """
        Executes one full Sense-Reason-Act cycle for an incoming call chunk.
        """
        config = override_config or sentinel_config_manager.get_config()
        ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
        trace: List[DecisionTrace] = []
        step = 1

        # ── Step 1: SENSE - Query Threat Intelligence ─────────────────
        thought_1 = f"Evaluating caller identity [{caller_id or 'anonymous'}] against threat intelligence registry."
        threat_res = SentinelToolRegistry.execute_threat_intel_lookup(caller_id)
        trace.append(DecisionTrace(
            step=step,
            thought=thought_1,
            tool_executed=threat_res.tool_name,
            tool_output=threat_res.summary,
        ))
        step += 1

        # ── Step 2: SENSE - Acoustic Deepfake Perception ──────────────
        thought_2 = f"Perceiving acoustic evidence from multi-model neural ensemble (sequence {window_seq})."
        acoustic_res = SentinelToolRegistry.execute_acoustic_verification(
            acoustic_score=acoustic_score,
            detector_breakdown=detector_breakdown or {},
        )
        trace.append(DecisionTrace(
            step=step,
            thought=thought_2,
            tool_executed=acoustic_res.tool_name,
            tool_output=acoustic_res.summary,
        ))
        step += 1

        # ── Step 3: SENSE - Conversational Semantic Intent ────────────
        text = transcript or ""
        thought_3 = f"Analyzing conversational scam intent & psychological manipulation ({len(text)} chars transcribed)."
        semantic_res = SentinelToolRegistry.execute_semantic_analysis(text)
        trace.append(DecisionTrace(
            step=step,
            thought=thought_3,
            tool_executed=semantic_res.tool_name,
            tool_output=semantic_res.summary,
        ))
        step += 1

        # ── Step 4: REASON - Multi-Modal Dynamic Deliberation ─────────
        raw_ac = acoustic_res.data.get("acoustic_score", 0.0)
        raw_sem = semantic_res.data.get("semantic_score", 0.0)
        risk_mult = threat_res.data.get("risk_multiplier", 1.0)
        caller_rep = threat_res.data.get("reputation", "UNKNOWN")

        # Dynamic weight adaptation:
        # If no transcript or speech is present, adapt acoustic weight to 1.0 to avoid dilution
        if not text.strip():
            w_ac = 1.0
            w_sem = 0.0
        else:
            w_ac = config.acoustic_weight
            w_sem = config.semantic_weight

        base_threat = (w_ac * raw_ac) + (w_sem * raw_sem)
        effective_mult = 1.0 + (risk_mult - 1.0) * config.caller_intel_weight
        effective_mult = max(0.5, effective_mult)
        composite_score = min(100.0, round(base_threat * effective_mult, 1))

        # Check cumulative history
        history = self.session_history.setdefault(session_id, [])
        history.append({
            "seq": window_seq,
            "composite": composite_score,
            "acoustic": raw_ac,
            "semantic": raw_sem,
        })

        recent_window = history[-3:]
        avg_recent_threat = sum(h["composite"] for h in recent_window) / len(recent_window)

        # Policy & Action selection (ADVISORY ONLY)
        crit_thresh = config.critical_alert_threshold
        chal_thresh = config.challenge_threshold

        if composite_score >= crit_thresh or avg_recent_threat >= crit_thresh:
            action = "ALERT_AND_ANCHOR"
            verdict = "ATTACK_CONFIRMED" if (raw_ac >= 65.0 and raw_sem >= 30.0) else "THREAT_DETECTED"
            reason = (
                f"Critical threat detected ({composite_score}/100 >= {crit_thresh}). "
                f"Acoustic synthetic evidence ({raw_ac}%) and scam intent ({raw_sem}%) corroboration. "
                f"Dispatching advisory warning and anchoring evidence on ledger."
            )
        elif composite_score >= chal_thresh or raw_ac >= 60.0 or raw_sem >= 40.0:
            action = "CHALLENGE"
            verdict = "SUSPICIOUS"
            reason = (
                f"Elevated risk score ({composite_score}/100 >= {chal_thresh}). "
                f"Suggesting active cognitive voice challenge to verify caller."
            )
        elif composite_score >= 25.0 or caller_rep in ("MALICIOUS", "SUSPICIOUS", "SUSPICIOUS_PREFIX"):
            action = "MONITOR"
            verdict = "SUSPICIOUS"
            reason = f"Moderate suspicion ({composite_score}/100). Sustaining telemetry monitoring."
        else:
            action = "ALLOW"
            verdict = "SAFE"
            reason = f"Normal conversational metrics ({composite_score}/100). No intervention needed."

        thought_4 = (
            f"Deliberated state: Acoustic={raw_ac}% (w={w_ac}), Semantic={raw_sem}% (w={w_sem}), "
            f"IntelMultiplier={round(effective_mult, 2)}x -> Composite={composite_score}%. "
            f"Action selected: {action} (Advisory Mode - Call Protected)."
        )

        # ── Step 5: ACT - Dispatch Advisory Countermeasure ─────────────
        dispatch_res = SentinelToolRegistry.execute_countermeasure_dispatch(
            action=action,
            reason=reason,
            session_id=session_id,
        )
        trace.append(DecisionTrace(
            step=step,
            thought=thought_4,
            tool_executed=dispatch_res.tool_name,
            tool_output=dispatch_res.summary,
        ))

        return SentinelVerdict(
            session_id=session_id,
            window_seq=window_seq,
            timestamp_ms=ts,
            verdict=verdict,
            action=action,
            composite_threat_score=composite_score,
            acoustic_score=raw_ac,
            semantic_score=raw_sem,
            caller_reputation=caller_rep,
            reasoning_summary=reason,
            trace=trace,
            intervention_details=dispatch_res.data,
            weights_applied={"acoustic": w_ac, "semantic": w_sem, "intel_multiplier": round(effective_mult, 2)},
        )

    def reset_session(self, session_id: str) -> None:
        self.session_history.pop(session_id, None)


sentinel_agent = SentinelAgent()
