"""
Whisper transcription adapter for VoiceShield ML service.
Provides low-latency speech-to-text inference with lazy-loading and thread safety.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional, Dict, Any
import numpy as np

try:
    import torch
    _has_torch = True
except ImportError:
    torch = None
    _has_torch = False

logger = logging.getLogger(__name__)


class WhisperTranscriberAdapter:
    """
    Singleton adapter for OpenAI Whisper ASR.
    Supports transcribing numpy float32 arrays (16 kHz mono) or file paths.
    """
    _instance: Optional[WhisperTranscriberAdapter] = None
    _lock = threading.Lock()

    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self._model = None
        self._load_lock = threading.Lock()
        self.device = "cuda" if (_has_torch and torch.cuda.is_available()) else "cpu"

    @classmethod
    def get_instance(cls, model_size: str = "tiny") -> WhisperTranscriberAdapter:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(model_size=model_size)
            return cls._instance

    def _ensure_model_loaded(self):
        if self._model is None:
            with self._load_lock:
                if self._model is None:
                    import whisper
                    logger.info(f"Loading Whisper model ({self.model_size}) on {self.device}...")
                    self._model = whisper.load_model(self.model_size, device=self.device)
                    logger.info("Whisper model loaded successfully.")

    def is_loaded(self) -> bool:
        return self._model is not None

    def transcribe(
        self,
        audio_16k: np.ndarray,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe 16kHz mono float32 numpy array.
        Returns:
            {
                "text": str,
                "detected_language": str,
                "duration_sec": float,
            }
        """
        if audio_16k is None or len(audio_16k) == 0:
            return {"text": "", "detected_language": "unknown", "duration_sec": 0.0}

        try:
            self._ensure_model_loaded()
            # Normalize float audio array to float32
            audio_data = audio_16k.astype(np.float32)
            duration_sec = float(len(audio_data) / 16000.0)

            options: Dict[str, Any] = {"fp16": False if self.device == "cpu" else True}
            if language:
                options["language"] = language

            result = self._model.transcribe(audio_data, **options)

            text = result.get("text", "").strip()
            detected_lang = result.get("language", "unknown")

            return {
                "text": text,
                "detected_language": detected_lang,
                "duration_sec": round(duration_sec, 2),
            }
        except Exception as exc:
            logger.error(f"Whisper transcription error: {exc}", exc_info=True)
            return {
                "text": "",
                "detected_language": "error",
                "duration_sec": 0.0,
                "error": str(exc),
            }


# Module singleton
transcription_adapter = WhisperTranscriberAdapter.get_instance()
