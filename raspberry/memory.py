"""Small, local SQLite memory store. Realtime API sessions have no app memory."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


MEMORY_PATTERNS = re.compile(
    r"\b(jeg heter|kall meg|jeg liker|jeg elsker|jeg foretrekker|jeg bor|"
    r"jeg jobber|familien min|fødselsdagen min|husk at)\b",
    re.IGNORECASE,
)
WORDS = re.compile(r"[a-zæøå0-9]{3,}", re.IGNORECASE)


class MemoryStore:
    def __init__(self, path: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT
            )"""
        )
        self.connection.commit()

    def remember_user_text(self, text: str) -> bool:
        text = " ".join(text.strip().split())
        if not self.enabled or not text or not MEMORY_PATTERNS.search(text):
            return False
        self.connection.execute("INSERT OR IGNORE INTO memories(text) VALUES (?)", (text[:1000],))
        self.connection.commit()
        return True

    def relevant(self, query: str = "", limit: int = 8) -> list[str]:
        if not self.enabled or limit <= 0:
            return []
        rows = self.connection.execute(
            "SELECT id, text FROM memories ORDER BY COALESCE(last_used_at, created_at) DESC LIMIT 100"
        ).fetchall()
        query_words = set(WORDS.findall(query.lower()))
        ranked = sorted(
            rows,
            key=lambda row: len(query_words.intersection(WORDS.findall(row[1].lower()))),
            reverse=True,
        )[:limit]
        if ranked:
            self.connection.executemany(
                "UPDATE memories SET last_used_at=CURRENT_TIMESTAMP WHERE id=?",
                [(row[0],) for row in ranked],
            )
            self.connection.commit()
        return [row[1] for row in ranked]

    def close(self) -> None:
        self.connection.close()
