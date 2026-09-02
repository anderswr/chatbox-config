"""Environment based configuration for the Realtime voice assistant."""

from __future__ import annotations

import os
import logging
import time
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


SUPPORTED_VOICES = (
    "marin",
    "cedar",
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "sage",
    "shimmer",
    "verse",
)
SUPPORTED_MODELS = (
    "gpt-realtime-2.1",
    "gpt-realtime-2.1-mini",
    "gpt-realtime-2",
    "gpt-realtime-1.5",
    "gpt-realtime",
    "gpt-realtime-mini",
)
SUPPORTED_TRANSCRIPTION_MODELS = (
    "gpt-realtime-whisper",
    "gpt-4o-mini-transcribe",
    "gpt-4o-transcribe",
    "whisper-1",
)

DEFAULT_PROMPT = (
    "Du heter Liv og er en trygg, hyggelig og kortfattet norsk samtalepartner. "
    "Still gjerne relevante oppfølgingsspørsmål."
)

DEFAULT_CONFIG_URL = (
    "https://chatbox-config.vercel.app/api/config"
)


def _boolean(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


def _integer(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ValueError(f"{name} må være et heltall") from exc


@dataclass(frozen=True)
class Config:
    api_key: str | None
    token_url: str | None
    device_token: str | None
    model: str
    voice: str
    instructions: str
    greeting: str
    vad_eagerness: str
    memory_enabled: bool
    memory_limit: int
    input_device: str | None
    output_device: str | None
    database_path: Path
    speed: float
    noise_reduction: str
    transcription_model: str
    max_output_tokens: int
    reasoning_effort: str
    remote_revision: str | None

    @staticmethod
    def _remote_settings(url: str) -> dict[str, Any]:
        try:
            separator = "&" if "?" in url else "?"
            response = requests.get(
                f"{url}{separator}t={int(time.time())}",
                timeout=5,
                headers={"Cache-Control": "no-cache"},
            )
            response.raise_for_status()
            settings = response.json()
            if not isinstance(settings, dict):
                raise ValueError("config.json må inneholde et JSON-objekt")
            logging.info("Hentet offentlig konfigurasjon fra %s", url)
            return settings
        except (requests.RequestException, ValueError) as exc:
            logging.warning("Kunne ikke hente offentlig konfigurasjon: %s", exc)
            return {}

    @classmethod
    def load(cls) -> "Config":
        # API key stays only on the Pi. This file is ignored by Git.
        env_path = Path(__file__).with_name(".env")
        load_dotenv(env_path)

        api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("openainokkel") or "").strip() or None
        token_url = os.getenv("REALTIME_TOKEN_URL", "").strip().rstrip("/") or None
        device_token = os.getenv("RASPBERRY_DEVICE_TOKEN", "").strip() or None
        if not api_key and not (token_url and device_token):
            raise ValueError(
                f"Sett REALTIME_TOKEN_URL og RASPBERRY_DEVICE_TOKEN i {env_path}. "
                "OPENAI_API_KEY lokalt støttes bare som reserve."
            )

        config_url = os.getenv("CHATBOX_CONFIG_URL", DEFAULT_CONFIG_URL).strip()
        remote = cls._remote_settings(config_url)
        remote_revision = (
            hashlib.sha256(json.dumps(remote, sort_keys=True).encode("utf-8")).hexdigest()
            if remote
            else None
        )

        voice = str(remote.get("voice") or os.getenv("REALTIME_VOICE", "marin")).strip().lower()
        if voice not in SUPPORTED_VOICES:
            choices = ", ".join(SUPPORTED_VOICES)
            raise ValueError(f"Ugyldig REALTIME_VOICE={voice!r}. Gyldige stemmer: {choices}")

        model = str(remote.get("model") or os.getenv("REALTIME_MODEL", "gpt-realtime")).strip()
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Ugyldig Realtime-modell: {model}")

        eagerness = str(remote.get("vad_eagerness") or os.getenv("VAD_EAGERNESS", "auto")).strip().lower()
        if eagerness not in {"low", "medium", "high", "auto"}:
            raise ValueError("VAD_EAGERNESS må være low, medium, high eller auto")

        default_db = Path.home() / ".local" / "share" / "chatbox" / "memory.sqlite3"
        speed = float(remote.get("speed", os.getenv("REALTIME_SPEED", "1")))
        if not 0.25 <= speed <= 1.5:
            raise ValueError("REALTIME_SPEED må være mellom 0.25 og 1.5")
        noise_reduction = str(remote.get("noise_reduction") or os.getenv("NOISE_REDUCTION", "far_field"))
        if noise_reduction not in {"off", "near_field", "far_field"}:
            raise ValueError("NOISE_REDUCTION må være off, near_field eller far_field")
        transcription_model = str(
            remote.get("transcription_model")
            or os.getenv("TRANSCRIPTION_MODEL", "gpt-realtime-whisper")
        )
        if transcription_model not in SUPPORTED_TRANSCRIPTION_MODELS:
            raise ValueError(f"Ugyldig transkripsjonsmodell: {transcription_model}")
        max_output_tokens = int(remote.get("max_output_tokens", os.getenv("MAX_OUTPUT_TOKENS", "2048")))
        if not 1 <= max_output_tokens <= 4096:
            raise ValueError("MAX_OUTPUT_TOKENS må være mellom 1 og 4096")
        reasoning_effort = str(remote.get("reasoning_effort") or os.getenv("REASONING_EFFORT", "low"))
        if reasoning_effort not in {"minimal", "low", "medium", "high", "xhigh"}:
            raise ValueError("Ugyldig REASONING_EFFORT")
        return cls(
            api_key=api_key,
            token_url=token_url,
            device_token=device_token,
            model=model,
            voice=voice,
            instructions=str(
                remote.get("system_prompt")
                or remote.get("system_instruction")
                or os.getenv("SYSTEM_PROMPT", DEFAULT_PROMPT)
            ).strip(),
            greeting=str(
                remote.get("speak_text")
                or os.getenv("GREETING", "Hei! Hva har du lyst til å snakke om?")
            ).strip(),
            vad_eagerness=eagerness,
            memory_enabled=(
                bool(remote["memory_enabled"])
                if isinstance(remote.get("memory_enabled"), bool)
                else _boolean(os.getenv("MEMORY_ENABLED"), True)
            ),
            memory_limit=max(
                0,
                int(remote["memory_limit"])
                if isinstance(remote.get("memory_limit"), int) and not isinstance(remote.get("memory_limit"), bool)
                else _integer("MEMORY_LIMIT", 8),
            ),
            input_device=os.getenv("AUDIO_INPUT_DEVICE") or None,
            output_device=os.getenv("AUDIO_OUTPUT_DEVICE") or None,
            database_path=Path(os.getenv("MEMORY_DB", str(default_db))).expanduser(),
            speed=speed,
            noise_reduction=noise_reduction,
            transcription_model=transcription_model,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
            remote_revision=remote_revision,
        )
