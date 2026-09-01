import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from raspberry.config import Config
from raspberry.memory import MemoryStore
from raspberry.usage import TokenUsage, UsageTracker


class ConfigTests(unittest.TestCase):
    def test_loads_realtime_settings(self):
        values = {
            "OPENAI_API_KEY": "test-key",
            "REALTIME_MODEL": "future-realtime-model",
            "REALTIME_VOICE": "cedar",
            "VAD_EAGERNESS": "high",
            "MEMORY_ENABLED": "false",
        }
        with patch.dict(os.environ, values, clear=True), patch("raspberry.config.load_dotenv"), patch.object(Config, "_remote_settings", return_value={}):
            config = Config.load()
        self.assertEqual(config.model, "future-realtime-model")
        self.assertEqual(config.voice, "cedar")
        self.assertEqual(config.vad_eagerness, "high")
        self.assertFalse(config.memory_enabled)

    def test_rejects_unknown_voice(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "REALTIME_VOICE": "unknown"}, clear=True), patch("raspberry.config.load_dotenv"), patch.object(Config, "_remote_settings", return_value={}):
            with self.assertRaises(ValueError):
                Config.load()

    def test_accepts_vercel_token_configuration_without_openai_key(self):
        values = {
            "REALTIME_TOKEN_URL": "https://example.test/api/realtime-token",
            "RASPBERRY_DEVICE_TOKEN": "device-secret",
        }
        with patch.dict(os.environ, values, clear=True), patch("raspberry.config.load_dotenv"), patch.object(Config, "_remote_settings", return_value={}):
            config = Config.load()
        self.assertIsNone(config.api_key)
        self.assertEqual(config.device_token, "device-secret")

    def test_remote_settings_override_local_fallbacks(self):
        remote = {
            "system_prompt": "Prompt fra nettet",
            "speak_text": "Hei fra nettet",
            "voice": "verse",
            "model": "remote-model",
            "vad_eagerness": "low",
            "memory_enabled": False,
            "memory_limit": 3,
        }
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "REALTIME_VOICE": "alloy"}, clear=True), patch("raspberry.config.load_dotenv"), patch.object(Config, "_remote_settings", return_value=remote):
            config = Config.load()
        self.assertEqual(config.instructions, "Prompt fra nettet")
        self.assertEqual(config.voice, "verse")
        self.assertEqual(config.model, "remote-model")
        self.assertFalse(config.memory_enabled)
        self.assertEqual(config.memory_limit, 3)


class MemoryTests(unittest.TestCase):
    def test_only_persists_memory_like_user_facts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryStore(Path(directory) / "memory.sqlite3")
            self.assertFalse(store.remember_user_text("Hvordan er været?"))
            self.assertTrue(store.remember_user_text("Jeg liker kaffe uten melk."))
            self.assertEqual(store.relevant("kaffe", 2), ["Jeg liker kaffe uten melk."])
            store.close()


class UsageTests(unittest.TestCase):
    PAYLOAD = {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "input_token_details": {"text_tokens": 3, "audio_tokens": 7, "cached_tokens": 2},
        "output_token_details": {"text_tokens": 1, "audio_tokens": 4},
    }

    def test_usage_is_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "usage.sqlite3"
            tracker = UsageTracker(path)
            current = tracker.add(self.PAYLOAD)
            self.assertEqual(current, TokenUsage(10, 5, 15, 3, 7, 2, 1, 4))
            tracker.close()
            reopened = UsageTracker(path)
            self.assertEqual(reopened.accumulated.total_tokens, 15)
            reopened.close()


if __name__ == "__main__":
    unittest.main()
