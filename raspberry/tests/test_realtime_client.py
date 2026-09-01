import json
import sys
import types
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

# PortAudio is hardware-only in CI; the client schema does not need a device.
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))

from raspberry.config import Config
from raspberry.realtime_client import RealtimeClient


class FakeMemory:
    def relevant(self, query, limit):
        return ["Jeg liker kaffe."]

    def remember_user_text(self, text):
        return True


class FakeUsage:
    def add(self, payload):
        return None


class FakeAudio:
    input_queue = None

    def interrupt(self):
        return "item-1", 0, 725


class FakeWebSocket:
    def __init__(self):
        self.sent = []

    async def send(self, payload):
        self.sent.append(json.loads(payload))


class RealtimeClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        config = Config(
            api_key="test",
            token_url=None,
            device_token=None,
            model="gpt-realtime",
            voice="marin",
            instructions="Vær hjelpsom.",
            greeting="Hei!",
            vad_eagerness="auto",
            memory_enabled=True,
            memory_limit=8,
            input_device=None,
            output_device=None,
            database_path=Path("unused.sqlite3"),
        )
        self.client = RealtimeClient(config, FakeAudio(), FakeMemory(), FakeUsage())

    def test_ga_session_uses_semantic_vad_and_audio_voice(self):
        session = self.client.session_event()["session"]
        self.assertEqual(session["type"], "realtime")
        self.assertEqual(session["model"], "gpt-realtime")
        self.assertEqual(session["audio"]["output"]["voice"], "marin")
        vad = session["audio"]["input"]["turn_detection"]
        self.assertEqual(vad["type"], "semantic_vad")
        self.assertTrue(vad["create_response"])
        self.assertTrue(vad["interrupt_response"])
        self.assertIn("Jeg liker kaffe", session["instructions"])

    async def test_interrupt_sends_conversation_item_truncate(self):
        websocket = FakeWebSocket()
        await self.client._truncate_playback(websocket)
        self.assertEqual(websocket.sent, [{
            "type": "conversation.item.truncate",
            "item_id": "item-1",
            "content_index": 0,
            "audio_end_ms": 725,
        }])

    def test_fetches_short_lived_token_from_vercel(self):
        self.client.config = replace(
            self.client.config,
            api_key=None,
            token_url="https://example.test/api/realtime-token",
            device_token="device-secret",
        )
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"value": "ek_short_lived"}
        with patch("raspberry.realtime_client.requests.post", return_value=response) as post:
            self.assertEqual(self.client._access_token(), "ek_short_lived")
        post.assert_called_once_with(
            "https://example.test/api/realtime-token",
            json={"model": "gpt-realtime", "voice": "marin"},
            headers={"Authorization": "Bearer device-secret"},
            timeout=10,
        )


if __name__ == "__main__":
    unittest.main()
