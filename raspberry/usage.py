"""Token accounting for Realtime response.done usage payloads."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_text_tokens: int = 0
    input_audio_tokens: int = 0
    cached_tokens: int = 0
    output_text_tokens: int = 0
    output_audio_tokens: int = 0

    @classmethod
    def from_api(cls, usage: dict[str, Any] | None) -> "TokenUsage":
        usage = usage or {}
        input_details = usage.get("input_token_details") or {}
        output_details = usage.get("output_token_details") or {}
        cached_details = input_details.get("cached_tokens_details") or {}
        return cls(
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
            input_text_tokens=int(input_details.get("text_tokens") or 0),
            input_audio_tokens=int(input_details.get("audio_tokens") or 0),
            cached_tokens=int(input_details.get("cached_tokens") or cached_details.get("text_tokens") or 0),
            output_text_tokens=int(output_details.get("text_tokens") or 0),
            output_audio_tokens=int(output_details.get("audio_tokens") or 0),
        )

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(**{
            field: getattr(self, field) + getattr(other, field)
            for field in self.__dataclass_fields__
        })

    def short(self) -> str:
        return (
            f"input={self.input_tokens} output={self.output_tokens} total={self.total_tokens} "
            f"(text inn/ut={self.input_text_tokens}/{self.output_text_tokens}, "
            f"audio inn/ut={self.input_audio_tokens}/{self.output_audio_tokens}, "
            f"cached={self.cached_tokens})"
        )


class UsageTracker:
    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database_path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS usage_totals (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)"
        )
        self.connection.commit()
        self.session = TokenUsage()

    def add(self, usage_payload: dict[str, Any] | None) -> TokenUsage:
        current = TokenUsage.from_api(usage_payload)
        self.session = self.session + current
        accumulated = self.accumulated + current
        import json

        self.connection.execute(
            "INSERT OR REPLACE INTO usage_totals(id, payload) VALUES (1, ?)",
            (json.dumps(accumulated.__dict__),),
        )
        self.connection.commit()
        logging.info("Tokens siste svar: %s", current.short())
        logging.info("Tokens denne sesjonen: %s", self.session.short())
        logging.info("Tokens akkumulert: %s", accumulated.short())
        return current

    @property
    def accumulated(self) -> TokenUsage:
        import json

        row = self.connection.execute("SELECT payload FROM usage_totals WHERE id=1").fetchone()
        return TokenUsage(**json.loads(row[0])) if row else TokenUsage()

    def close(self) -> None:
        self.connection.close()
