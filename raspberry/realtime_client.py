"""GA OpenAI Realtime WebSocket client."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import random
from typing import Any

import requests
from websockets.asyncio.client import connect

from raspberry.audio import API_SAMPLE_RATE, DuplexAudio
from raspberry.config import Config
from raspberry.memory import MemoryStore
from raspberry.usage import UsageTracker


class RealtimeClient:
    def __init__(self, config: Config, audio: DuplexAudio, memory: MemoryStore, usage: UsageTracker) -> None:
        self.config = config
        self.audio = audio
        self.memory = memory
        self.usage = usage
        self.last_user_text = ""
        self.greeted = False

    def instructions(self) -> str:
        memories = self.memory.relevant(self.last_user_text, self.config.memory_limit)
        if not memories:
            return self.config.instructions
        facts = "\n".join(f"- {fact}" for fact in memories)
        return f"{self.config.instructions}\n\nLokalt lagret brukerminne (bruk bare når relevant):\n{facts}"

    def session_event(self) -> dict[str, Any]:
        session = {
            "type": "realtime",
            "model": self.config.model,
            "instructions": self.instructions(),
            "output_modalities": ["audio"],
            "max_output_tokens": self.config.max_output_tokens,
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": API_SAMPLE_RATE},
                    "transcription": {"model": self.config.transcription_model, "language": "no"},
                    "noise_reduction": (
                        None
                        if self.config.noise_reduction == "off"
                        else {"type": self.config.noise_reduction}
                    ),
                    "turn_detection": {
                        "type": "semantic_vad",
                        "eagerness": self.config.vad_eagerness,
                        "create_response": True,
                        "interrupt_response": True,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcm", "rate": API_SAMPLE_RATE},
                    "voice": self.config.voice,
                    "speed": self.config.speed,
                },
            },
        }
        if self.config.model.startswith("gpt-realtime-2"):
            session["reasoning"] = {"effort": self.config.reasoning_effort}
        return {
            "type": "session.update",
            "session": session,
        }

    async def _send_audio(self, websocket: Any) -> None:
        while True:
            pcm = await self.audio.input_queue.get()
            await websocket.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(pcm).decode("ascii"),
            }))

    async def _truncate_playback(self, websocket: Any) -> None:
        item_id, content_index, audio_end_ms = self.audio.interrupt()
        if item_id is None:
            return
        await websocket.send(json.dumps({
            "type": "conversation.item.truncate",
            "item_id": item_id,
            "content_index": content_index,
            "audio_end_ms": audio_end_ms,
        }))
        logging.info("Avbrøt %s ved %d ms", item_id, audio_end_ms)

    async def _receive(self, websocket: Any) -> None:
        async for raw in websocket:
            event = json.loads(raw)
            event_type = event.get("type", "")
            if event_type in {"session.created", "session.updated", "response.created"}:
                logging.info("Realtime-event: %s", event_type)
            elif event_type == "response.output_audio.delta":
                self.audio.enqueue(
                    base64.b64decode(event["delta"]),
                    event["item_id"],
                    int(event.get("content_index", 0)),
                )
            elif event_type == "input_audio_buffer.speech_started":
                await self._truncate_playback(websocket)
            elif event_type == "conversation.item.input_audio_transcription.completed":
                self.last_user_text = event.get("transcript", "").strip()
                if self.last_user_text:
                    self.memory.remember_user_text(self.last_user_text)
                    logging.info("Bruker: %s", self.last_user_text)
            elif event_type == "response.output_audio_transcript.done":
                logging.info("Liv: %s", event.get("transcript", "").strip())
            elif event_type == "response.done":
                self.usage.add((event.get("response") or {}).get("usage"))
                status = (event.get("response") or {}).get("status", "ukjent")
                logging.info("Realtime-svar ferdig: status=%s", status)
            elif event_type == "error":
                raise RuntimeError(json.dumps(event.get("error", event), ensure_ascii=False))

    async def _watch_for_config_changes(self) -> None:
        """Poll web settings and end the socket only when they actually change."""
        import os

        seconds = max(60, int(os.getenv("CONFIG_REFRESH_SECONDS", "300")))
        while True:
            await asyncio.sleep(seconds)
            latest = await asyncio.to_thread(Config.load)
            if latest.remote_revision is None:
                logging.warning("Beholder aktiv konfigurasjon fordi webkonfigurasjonen ikke kunne hentes")
                continue
            if latest.remote_revision == self.config.remote_revision:
                logging.info("Webkonfigurasjonen er uendret")
                continue
            self.config = latest
            logging.info("Ny webkonfigurasjon funnet; starter en ny Realtime-session")
            return

    def _access_token(self) -> str:
        """Fetch a short-lived Realtime secret without exposing the OpenAI key."""
        if self.config.token_url and self.config.device_token:
            response = requests.post(
                self.config.token_url,
                json={"model": self.config.model, "voice": self.config.voice},
                headers={"Authorization": f"Bearer {self.config.device_token}"},
                timeout=10,
            )
            response.raise_for_status()
            value = response.json().get("value")
            if not value:
                raise RuntimeError("Token-endepunktet returnerte ikke en Realtime client secret")
            return value
        if self.config.api_key:
            logging.warning("Bruker langsiktig OPENAI_API_KEY direkte; bruk Vercel token-endepunkt i produksjon")
            return self.config.api_key
        raise RuntimeError("Mangler Realtime-legitimasjon")

    async def _connect_once(self) -> None:
        url = f"wss://api.openai.com/v1/realtime?model={self.config.model}"
        access_token = await asyncio.to_thread(self._access_token)
        async with connect(
            url,
            additional_headers={"Authorization": f"Bearer {access_token}"},
            ping_interval=20,
            ping_timeout=20,
            open_timeout=20,
            max_size=16 * 1024 * 1024,
        ) as websocket:
            logging.info("Tilkoblet GA Realtime: modell=%s stemme=%s", self.config.model, self.config.voice)
            while not self.audio.input_queue.empty():
                self.audio.input_queue.get_nowait()
            await websocket.send(json.dumps(self.session_event()))
            if not self.greeted and self.config.greeting:
                await websocket.send(json.dumps({
                    "type": "response.create",
                    "response": {
                        "output_modalities": ["audio"],
                        "instructions": f'Si naturlig på norsk: "{self.config.greeting}"',
                    },
                }))
                self.greeted = True
            tasks = {
                asyncio.create_task(self._send_audio(websocket)),
                asyncio.create_task(self._receive(websocket)),
                asyncio.create_task(self._watch_for_config_changes()),
            }
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()

    async def run_forever(self) -> None:
        attempt = 0
        while True:
            try:
                # Reloads raspberry/.env and the public web config. Voice changes
                # therefore take effect only in the new session, as required.
                self.config = Config.load()
                await self._connect_once()
                attempt = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                attempt += 1
                delay = min(30, 2 ** min(attempt, 5)) + random.random()
                logging.exception("Realtime-feil: %s; kobler til igjen om %.1f s", exc, delay)
                await asyncio.sleep(delay)
