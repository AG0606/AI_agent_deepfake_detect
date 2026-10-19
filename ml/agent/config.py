"""
Configuration management for the Sentinel AI Agent.
Thread-safe parameter updates with bounds checking and weight normalization.
"""
from __future__ import annotations

import threading
from typing import Dict, Any
from pydantic import BaseModel, Field, model_validator


class SentinelConfig(BaseModel):
    acoustic_weight: float = Field(default=0.50, ge=0.0, le=1.0, description="Weight for acoustic deepfake probability")
    semantic_weight: float = Field(default=0.50, ge=0.0, le=1.0, description="Weight for conversational scam intent")
    caller_intel_weight: float = Field(default=1.0, ge=0.1, le=3.0, description="Base multiplier for caller intelligence")
    challenge_threshold: float = Field(default=50.0, ge=10.0, le=90.0, description="Threshold to trigger cognitive voice challenge")
    critical_alert_threshold: float = Field(default=75.0, ge=30.0, le=99.0, description="Threshold to trigger ALERT_AND_ANCHOR")

    @model_validator(mode="after")
    def validate_weights_and_thresholds(self) -> SentinelConfig:
        total_weight = self.acoustic_weight + self.semantic_weight
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"acoustic_weight ({self.acoustic_weight}) and semantic_weight ({self.semantic_weight}) must sum to 1.0 (got {round(total_weight, 3)})")
        if self.challenge_threshold >= self.critical_alert_threshold:
            raise ValueError(f"challenge_threshold ({self.challenge_threshold}) must be strictly less than critical_alert_threshold ({self.critical_alert_threshold})")
        return self


class SentinelConfigManager:
    """Thread-safe singleton config manager."""

    def __init__(self, config: SentinelConfig | None = None):
        self._lock = threading.Lock()
        self._config = config or SentinelConfig()

    def get_config(self) -> SentinelConfig:
        with self._lock:
            return self._config.model_copy()

    def update_config(self, updates: Dict[str, Any]) -> SentinelConfig:
        with self._lock:
            current_dict = self._config.model_dump()
            current_dict.update(updates)
            new_config = SentinelConfig(**current_dict)
            self._config = new_config
            return self._config.model_copy()


sentinel_config_manager = SentinelConfigManager()
