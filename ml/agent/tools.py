"""
Tool definitions and registry for the VoiceShield Sentinel AI Agent.

Following standard Agentic Architecture (ReAct / Tool Execution):
The Sentinel Agent uses tools to gather threat intelligence, inspect acoustic evidence,
run semantic intent analysis, and execute advisory intervention countermeasures.
"""
from __future__ import annotations

import re
import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Dict[str, Any]
    summary: str


class ThreatIntelRegistry:
    """
    Threat Intelligence lookup service.
    Simulates external OSINT / Telecom registry & scam pattern databases.
    """
    KNOWN_SCAM_PREFIXES = ["+1800", "+919800", "+91140", "+44800", "+91000"]
    HIGH_RISK_NUMBERS = {
        "+919876543210": {"reputation": "MALICIOUS", "reported_scams": 42, "category": "Bank Impersonation (SBI/HDFC)"},
        "+18005550199": {"reputation": "MALICIOUS", "reported_scams": 128, "category": "IRS Tax Fraud / Arrest Threat"},
        "+919123456789": {"reputation": "SUSPICIOUS", "reported_scams": 5, "category": "FedEx / Courier Customs Extortion"},
    }

    @classmethod
    def lookup(cls, caller_id: Optional[str]) -> Dict[str, Any]:
        if not caller_id or caller_id.strip() == "" or caller_id == "unknown":
            return {
                "caller_id": caller_id,
                "reputation": "UNKNOWN",
                "risk_multiplier": 1.1,
                "category": "Unregistered / Anonymous caller",
                "notes": "Anonymous caller identity increases suspicion threshold.",
            }

        cleaned = caller_id.strip().replace(" ", "").replace("-", "")
        if cleaned in cls.HIGH_RISK_NUMBERS:
            record = cls.HIGH_RISK_NUMBERS[cleaned]
            return {
                "caller_id": caller_id,
                "reputation": record["reputation"],
                "risk_multiplier": 2.0,
                "category": record["category"],
                "reported_scams": record["reported_scams"],
                "notes": f"Flagged in national scam database: {record['category']}",
            }

        for prefix in cls.KNOWN_SCAM_PREFIXES:
            if cleaned.startswith(prefix):
                return {
                    "caller_id": caller_id,
                    "reputation": "SUSPICIOUS_PREFIX",
                    "risk_multiplier": 1.4,
                    "category": "Robocall / VoIP Pool Prefix",
                    "notes": f"Caller prefix {prefix} matches known automated VoIP telemarketing pool.",
                }

        return {
            "caller_id": caller_id,
            "reputation": "CLEAN",
            "risk_multiplier": 0.8,
            "category": "Legitimate / Unreported",
            "notes": "No scam reports found in threat registry.",
        }


class SemanticFraudAnalyzer:
    """
    Advanced Scam Intent & Social-Engineering Scoring Engine.
    Detects 6 distinct psychological manipulation categories, Digital Arrest,
    and Hindi/Hinglish cybercrime lexicons.
    Includes a contextual negation and cyber-safety filter to prevent false positives
    on defensive advisory speech (e.g. 'never share OTP', 'do not tell password').
    """

    # Defensive/educational warning phrases to exclude from triggering false positive fraud scores
    NEGATION_SAFETY_PATTERNS = [
        r"\b(never|do not|don't|not|never ever|refuse to|warn|caution|alert)\s+(?:to\s+)?(share|give|disclose|tell|send|provide)\s+(?:any\s+|your\s+|the\s+)?(?:personal\s+)?(otp|password|pin|cvv|code|account details)\b",
        r"\b(bank|official|police|rbi|cbi)\s+(?:awareness|advisory|notice|will not|does not|never asks?|won't)\b",
        r"\b(beware of|stay alert against|protect yourself from|avoid)\s+(fraud|scam|scammers|fake calls|digital arrest)\b",
        r"\b(kisi ko|kabhi bhi)\s+(otp|pin|password)\s+(mat|na)\s+(de|batao|share karo)\b",
    ]

    # Category patterns with weighted scores
    INTENT_CATEGORIES = [
        # 1. Authority Impersonation & Digital Arrest Extortion
        {
            "category": "Authority Impersonation & Digital Arrest",
            "weight": 40,
            "patterns": [
                r"\b(digital arrest|digitally arrested|virtual court|virtual arrest)\b",
                r"\b(police officer|cbi|enforcement directorate|ed department|customs officer|narcotics bureau|crime branch|cyber cell)\b",
                r"\b(supreme court|high court|chief magistrate|arrest warrant|fir registered|non-bailable warrant)\b",
                r"\b(thaana|thana|police aayegi|giraftari|hiraasat|kotwali|kanooni karwayi)\b",
                r"\b(bank manager|bank vigilance|rbi governor|income tax department|irs|customs seized)\b",
            ],
        },
        # 2. Urgency & Panic Inducement
        {
            "category": "Urgency & Panic Inducement",
            "weight": 25,
            "patterns": [
                r"\b(immediately|right now|within (\d+) (minute|hour)s?|urgently|at once)\b",
                r"\b(account suspended|sim blocked|passport seized|electricity cut off|connection terminated)\b",
                r"\b(jaldi karo|abhi ke abhi|turant|varna block ho jayega|last chance|aakhri mauka)\b",
                r"\b(arrest within (\d+) hours?|police team dispatched|house raid)\b",
            ],
        },
        # 3. Credential & Identity Harvesting
        {
            "category": "Credential & Identity Harvesting",
            "weight": 40,
            "patterns": [
                r"\b(otp|one time password|verification code|secret pin|cvv|netbanking password)\b",
                r"\b(aadhaar number|pan card verification|biometric update|debit card digits)\b",
                r"\b(otp bataiye|otp bhejiye|code share karo|pin enter karo|kavach code)\b",
            ],
        },
        # 4. Financial Redirection & Extortion Demands
        {
            "category": "Financial Redirection & Extortion",
            "weight": 35,
            "patterns": [
                r"\b(safe custody account|government reserve account|security deposit|clearance fee)\b",
                r"\b(wire transfer|upi transfer|send money|deposit amount|rtgs|imps|crypto wallet)\b",
                r"\b(paise transfer karo|rbi account mein daalo|penalty pay karo|fine bhariye)\b",
                r"\b(refund claim link|click the apk link|download anydesk|install quicksupport)\b",
            ],
        },
        # 5. Isolation, Coercion & Secrecy Demands
        {
            "category": "Isolation & Coercion",
            "weight": 30,
            "patterns": [
                r"\b(don't disconnect|stay on video call|do not cut the call|keep camera on)\b",
                r"\b(confidential inquiry|national security investigation|do not tell family|do not inform anyone)\b",
                r"\b(phone mat kaatna|kisi se baat mat karna|chupchap suno|akela kamre mein jao)\b",
                r"\b(isolate yourself|switch on skype|maintain absolute secrecy)\b",
            ],
        },
        # 6. Courier / Parcel / Illegal Goods Pretext
        {
            "category": "Contraband / Courier Pretext",
            "weight": 30,
            "patterns": [
                r"\b(fedex parcel|dhl courier|package from taiwan|parcel from cambodia)\b",
                r"\b(drugs found|narcotics in package|illegal passports|contraband materials)\b",
                r"\b(parcel pakda gaya|drugs mile hain|illegal saaman|taiwan se courier)\b",
            ],
        },
    ]

    @classmethod
    def check_negation_or_safety_context(cls, text: str) -> bool:
        """Returns True if the transcript is educational/advisory or warning against scams."""
        lower = text.lower()
        for pattern in cls.NEGATION_SAFETY_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    @classmethod
    def analyze(cls, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "semantic_score": 0.0,
                "intent_categories": [],
                "triggers": [],
                "matched_cues": [],
                "explanation": "No speech transcript available.",
            }

        lower = text.lower()

        # If whole statement is an educational or protective warning against scams
        is_safe_advisory = cls.check_negation_or_safety_context(lower)

        matched_categories: set[str] = set()
        matched_cues: List[str] = []
        raw_score = 0.0

        for cat_spec in cls.INTENT_CATEGORIES:
            cat_name = cat_spec["category"]
            weight = cat_spec["weight"]
            cat_matched = False

            for pattern in cat_spec["patterns"]:
                matches = re.findall(pattern, lower)
                if matches:
                    cat_matched = True
                    for m in matches:
                        match_str = m[0] if isinstance(m, tuple) else m
                        if match_str and match_str not in matched_cues:
                            matched_cues.append(f"{cat_name}: '{match_str}'")

            if cat_matched:
                matched_categories.add(cat_name)
                raw_score += weight

        # If protective negation was detected, heavily discount or clear credential matches
        if is_safe_advisory and raw_score > 0:
            if len(matched_categories) <= 2:
                # E.g. "Bank alerts: Never share OTP or password with anyone"
                return {
                    "semantic_score": 0.0,
                    "intent_categories": [],
                    "triggers": [],
                    "matched_cues": [],
                    "explanation": "Defensive / educational fraud advisory pattern recognized. Neutralized.",
                }
            else:
                # Mixed, scale down by 80%
                raw_score = raw_score * 0.20

        # Multi-category compounding: 3 or more extortion categories amplify risk
        if len(matched_categories) >= 3:
            raw_score *= 1.25

        normalized_score = min(100.0, round(raw_score, 1))
        cats_list = sorted(list(matched_categories))

        if cats_list:
            explanation = f"Detected {len(cats_list)} scam intent indicator(s): {', '.join(cats_list)}."
        else:
            explanation = "Transcript neutral. No scam manipulation cues identified."

        return {
            "semantic_score": normalized_score,
            "intent_categories": cats_list,
            "triggers": matched_cues,
            "matched_cues": matched_cues,
            "explanation": explanation,
        }


class SentinelToolRegistry:
    """
    Unified Tool Execution interface for the Sentinel Agent.
    """

    @staticmethod
    def execute_threat_intel_lookup(caller_id: Optional[str]) -> ToolResult:
        data = ThreatIntelRegistry.lookup(caller_id)
        return ToolResult(
            tool_name="threat_intel_lookup",
            success=True,
            data=data,
            summary=f"Reputation: {data['reputation']}, Multiplier: {data['risk_multiplier']}",
        )

    @staticmethod
    def execute_semantic_analysis(transcript: str) -> ToolResult:
        data = SemanticFraudAnalyzer.analyze(transcript)
        return ToolResult(
            tool_name="semantic_fraud_analysis",
            success=True,
            data=data,
            summary=f"Semantic Scam Risk: {data['semantic_score']}% ({', '.join(data['intent_categories']) if data['intent_categories'] else 'Neutral'})",
        )

    @staticmethod
    def execute_acoustic_verification(acoustic_score: Optional[float], detector_breakdown: Dict[str, Any]) -> ToolResult:
        """
        Interprets acoustic multi-model ensemble (Dhwani, Indic RawNet, Prosody).
        """
        score = acoustic_score if (acoustic_score is not None and math.isfinite(acoustic_score)) else 0.0
        # If score is given as a normalized probability [0.0, 1.0], convert to [0.0, 100.0] percentage
        if 0.0 < score <= 1.0:
            score = score * 100.0

        is_synthetic = score >= 50.0
        confidence = "HIGH" if (score >= 75.0 or score <= 25.0) else "MODERATE"

        return ToolResult(
            tool_name="acoustic_verification",
            success=True,
            data={
                "acoustic_score": round(score, 2),
                "is_synthetic": is_synthetic,
                "confidence": confidence,
                "detectors": detector_breakdown,
            },
            summary=f"Acoustic Deepfake Score: {round(score, 1)}% ({confidence} confidence)",
        )

    @staticmethod
    def execute_countermeasure_dispatch(action: str, reason: str, session_id: str) -> ToolResult:
        """
        Dispatches targeted advisory countermeasure intervention:
        - ALLOW: Safe conversation, no intervention.
        - MONITOR: Mild anomalies or suspicious caller, sustain background telemetry.
        - CHALLENGE: High suspicion, recommends an active cognitive/voice challenge.
        - ALERT_AND_ANCHOR: High threat score; raises critical advisory warning and anchors
          forensic evidence to the cryptographic audit trail, NEVER disconnecting the call.
        """
        valid_actions = {"ALLOW", "MONITOR", "CHALLENGE", "ALERT_AND_ANCHOR", "TERMINATE_AND_ANCHOR"}
        if action not in valid_actions:
            action = "MONITOR"

        payload = {
            "session_id": session_id,
            "action": action,
            "reason": reason,
            "urgency": "CRITICAL" if action in ("ALERT_AND_ANCHOR", "TERMINATE_AND_ANCHOR") else "HIGH" if action == "CHALLENGE" else "LOW",
            "is_advisory_only": True,
            "call_terminated": False,
        }

        if action == "CHALLENGE":
            payload["challenge_prompt"] = (
                "Identity Challenge Suggested: Ask the caller to answer a shared pre-arranged secret "
                "or repeat a randomized phrase with natural prosodic inflection."
            )
        elif action in ("ALERT_AND_ANCHOR", "TERMINATE_AND_ANCHOR"):
            payload["evidence_anchor"] = {
                "anchored_on_chain": True,
                "advisory": "High probability synthetic impersonation / extortion detected. Evidence commitment anchored.",
            }

        return ToolResult(
            tool_name="countermeasure_dispatch",
            success=True,
            data=payload,
            summary=f"Dispatched advisory {action} action: {reason}",
        )
