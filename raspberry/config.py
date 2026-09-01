"""Environment based configuration for the Realtime voice assistant."""

from __future__ import annotations

import os
import logging
import time
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

DEFAULT_PROMPT = (
    "Du heter Liv og er en trygg, hyggelig og kortfattet norsk samtalepartner. "
    "Still gjerne relevante oppfølgingsspørsmål."
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
        token_url = os.getenv("REALTIME_TOKEN_URL", "").strip() or None
        device_token = os.getenv("RASPBERRY_DEVICE_TOKEN", "").strip() or None
        if not api_key and not (token_url and device_token):
            raise ValueError(
                f"Sett REALTIME_TOKEN_URL og RASPBERRY_DEVICE_TOKEN i {env_path}. "
                "OPENAI_API_KEY lokalt støttes bare som reserve."
            )

        config_url = os.getenv(
            "CHATBOX_CONFIG_URL",
            "https://chatbox-config-fruliv.vercel.app/config.json",
        )
        remote = cls._remote_settings(config_url)

        voice = str(remote.get("voice") or os.getenv("REALTIME_VOICE", "marin")).strip().lower()
        if voice not in SUPPORTED_VOICES:
            choices = ", ".join(SUPPORTED_VOICES)
            raise ValueError(f"Ugyldig REALTIME_VOICE={voice!r}. Gyldige stemmer: {choices}")

        eagerness = str(remote.get("vad_eagerness") or os.getenv("VAD_EAGERNESS", "auto")).strip().lower()
        if eagerness not in {"low", "medium", "high", "auto"}:
            raise ValueError("VAD_EAGERNESS må være low, medium, high eller auto")

        default_db = Path.home() / ".local" / "share" / "chatbox" / "memory.sqlite3"
        return cls(
            api_key=api_key,
            token_url=token_url,
            device_token=device_token,
            model=str(remote.get("model") or os.getenv("REALTIME_MODEL", "gpt-realtime")).strip(),
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
        )
