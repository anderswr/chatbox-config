import json
import sys
import types
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

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
            speed=1.0,
            noise_reduction="far_field",
            transcription_model="gpt-realtime-whisper",
            max_output_tokens=512,
            reasoning_effort="low",
            remote_revision="revision-1",
        )
        self.client = RealtimeClient(config, FakeAudio(), FakeMemory(), FakeUsage())

    def test_ga_session_uses_semantic_vad_and_audio_voice(self):
        session = self.client.session_event()["session"]
        self.assertEqual(session["type"], "realtime")
        self.assertEqual(session["model"], "gpt-realtime")
        self.assertEqual(session["audio"]["output"]["voice"], "marin")
        self.assertEqual(session["audio"]["output"]["speed"], 1.0)
        self.assertEqual(session["audio"]["input"]["noise_reduction"], {"type": "far_field"})
        self.assertEqual(session["max_output_tokens"], 512)
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

    def test_token_error_explains_endpoint(self):
        self.client.config = replace(
            self.client.config,
            api_key=None,
            token_url="https://example.vercel.app/api/realtime-token",
            device_token="device-secret",
        )
        response = Mock(ok=False, status_code=404, text="Not Found")
        with patch("raspberry.realtime_client.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "HTTP 404.*Not Found"):
                self.client._access_token()

    def test_deployment_not_found_has_actionable_error(self):
        self.client.config = replace(
            self.client.config,
            api_key=None,
            token_url="https://stale.vercel.app/api/realtime-token",
            device_token="device-secret",
        )
        response = Mock(ok=False, status_code=404, text="DEPLOYMENT_NOT_FOUND")
        with patch("raspberry.realtime_client.requests.post", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "Settings → Domains"):
                self.client._access_token()

    def test_local_key_is_fallback_when_token_endpoint_is_down(self):
        self.client.config = replace(
            self.client.config,
            api_key="local-test-key",
            token_url="https://example.vercel.app/api/realtime-token",
            device_token="device-secret",
        )
        response = Mock(ok=False, status_code=404, text="Not Found")
        with patch("raspberry.realtime_client.requests.post", return_value=response):
            self.assertEqual(self.client._access_token(), "local-test-key")

    async def test_poll_applies_changed_web_config(self):
        updated = replace(self.client.config, voice="cedar", remote_revision="revision-2")
        with patch("raspberry.realtime_client.asyncio.sleep", new=AsyncMock()), patch.object(
            Config, "load", return_value=updated
        ):
            await self.client._watch_for_config_changes()
        self.assertEqual(self.client.config.voice, "cedar")


if __name__ == "__main__":
    unittest.main()
