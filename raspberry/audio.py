"""Low-latency, full-duplex PCM capture and playback."""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from typing import Any

import numpy as np
import sounddevice as sd


API_SAMPLE_RATE = 24_000
BLOCK_MS = 20


def resample_pcm16(data: bytes, source_rate: int, target_rate: int) -> bytes:
    if not data or source_rate == target_rate:
        return data
    samples = np.frombuffer(data, dtype=np.int16)
    length = max(1, round(len(samples) * target_rate / source_rate))
    source = np.arange(len(samples), dtype=np.float32)
    target = np.linspace(0, len(samples), length, endpoint=False, dtype=np.float32)
    return np.interp(target, source, samples).astype(np.int16).tobytes()


def _device(selector: str | None, direction: str) -> tuple[int | str | None, dict[str, Any]]:
    if selector:
        try:
            selected: int | str = int(selector)
        except ValueError:
            selected = selector
        return selected, sd.query_devices(selected, direction)
    devices = sd.query_devices()
    channel_key = "max_input_channels" if direction == "input" else "max_output_channels"
    for index, candidate in enumerate(devices):
        if "jabra" in str(candidate["name"]).lower() and candidate[channel_key] > 0:
            return index, sd.query_devices(index, direction)
    return None, sd.query_devices(None, direction)


class DuplexAudio:
    def __init__(self, loop: asyncio.AbstractEventLoop, input_selector: str | None, output_selector: str | None) -> None:
        self.loop = loop
        self.input_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=100)
        self.chunks: deque[bytes] = deque()
        self.buffer = bytearray()
        self.lock = threading.Lock()
        self.current_item_id: str | None = None
        self.current_content_index = 0
        self.played_api_bytes = 0
        self.input_device, input_info = _device(input_selector, "input")
        self.output_device, output_info = _device(output_selector, "output")
        self.input_rate = round(input_info["default_samplerate"])
        self.output_rate = round(output_info["default_samplerate"])
        logging.info("Mikrofon: %s @ %d Hz", input_info["name"], self.input_rate)
        logging.info("Høyttaler: %s @ %d Hz", output_info["name"], self.output_rate)
        self.input_stream = sd.RawInputStream(
            device=self.input_device, samplerate=self.input_rate, channels=1, dtype="int16",
            blocksize=round(self.input_rate * BLOCK_MS / 1000), callback=self._capture,
        )
        self.output_stream = sd.RawOutputStream(
            device=self.output_device, samplerate=self.output_rate, channels=1, dtype="int16",
            blocksize=round(self.output_rate * BLOCK_MS / 1000), callback=self._play,
        )

    def _put_input(self, pcm: bytes) -> None:
        if self.input_queue.full():
            self.input_queue.get_nowait()
        self.input_queue.put_nowait(pcm)

    def _capture(self, data: memoryview, frames: int, time: Any, status: Any) -> None:
        if status:
            logging.warning("Mikrofonstatus: %s", status)
        pcm = resample_pcm16(bytes(data), self.input_rate, API_SAMPLE_RATE)
        self.loop.call_soon_threadsafe(self._put_input, pcm)

    def _play(self, output: memoryview, frames: int, time: Any, status: Any) -> None:
        if status:
            logging.warning("Høyttalerstatus: %s", status)
        with self.lock:
            while len(self.buffer) < len(output) and self.chunks:
                self.buffer.extend(self.chunks.popleft())
            chunk = self.buffer[: len(output)]
            del self.buffer[: len(output)]
            self.played_api_bytes += round(len(chunk) * API_SAMPLE_RATE / self.output_rate)
        output[: len(chunk)] = chunk
        output[len(chunk):] = b"\0" * (len(output) - len(chunk))

    def enqueue(self, pcm: bytes, item_id: str, content_index: int) -> None:
        converted = resample_pcm16(pcm, API_SAMPLE_RATE, self.output_rate)
        with self.lock:
            if item_id != self.current_item_id:
                self.current_item_id = item_id
                self.current_content_index = content_index
                self.played_api_bytes = 0
            self.chunks.append(converted)

    def interrupt(self) -> tuple[str | None, int, int]:
        with self.lock:
            item_id = self.current_item_id
            content_index = self.current_content_index
            # PCM16 mono: two bytes per sample.
            audio_end_ms = self.played_api_bytes * 1000 // (API_SAMPLE_RATE * 2)
            self.chunks.clear()
            self.buffer.clear()
            self.current_item_id = None
            self.played_api_bytes = 0
        return item_id, content_index, audio_end_ms

    def start(self) -> None:
        self.input_stream.start()
        self.output_stream.start()

    def close(self) -> None:
        for stream in (self.input_stream, self.output_stream):
            stream.stop()
            stream.close()
