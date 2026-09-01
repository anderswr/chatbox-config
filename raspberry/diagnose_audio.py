#!/usr/bin/env python3
"""Non-interactive microphone and speaker diagnostics for the Liv box."""

from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv


def selector(value: str | None) -> int | str | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Test lydkort, høyttaler og mikrofon")
    parser.add_argument("--seconds", type=float, default=2.0)
    parser.add_argument("--no-tone", action="store_true", help="Ikke spill testtone")
    args = parser.parse_args()
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    input_device = selector(os.getenv("AUDIO_INPUT_DEVICE"))
    output_device = selector(os.getenv("AUDIO_OUTPUT_DEVICE"))
    print("Tilgjengelige PortAudio-enheter:\n")
    print(sd.query_devices())
    print(f"\nPortAudio-standard (input, output): {sd.default.device}")
    print(f"Liv override (input, output): {input_device!r}, {output_device!r}")

    try:
        input_info = sd.query_devices(input_device, "input")
        output_info = sd.query_devices(output_device, "output")
        input_rate = round(input_info["default_samplerate"])
        output_rate = round(output_info["default_samplerate"])
        print(f"Valgt mikrofon: {input_info['name']} @ {input_rate} Hz")
        print(f"Valgt høyttaler: {output_info['name']} @ {output_rate} Hz")

        if not args.no_tone:
            sample_count = int(output_rate * args.seconds)
            positions = np.arange(sample_count, dtype=np.float32)
            tone = (0.18 * np.sin(2 * math.pi * 440 * positions / output_rate)).astype(np.float32)
            print(f"Spiller en 440 Hz testtone i {args.seconds:.1f} sekunder …")
            sd.play(tone, output_rate, device=output_device, blocking=True)

        print(f"Måler mikrofonen i {args.seconds:.1f} sekunder – snakk nå …")
        recording = sd.rec(
            int(input_rate * args.seconds), samplerate=input_rate, channels=1,
            dtype="float32", device=input_device, blocking=True,
        )
        rms = float(np.sqrt(np.mean(np.square(recording))))
        peak = float(np.max(np.abs(recording)))
        print(f"Mikrofonnivå: RMS={rms:.5f}, peak={peak:.5f}")
        if peak < 0.001:
            print("FEIL: Mikrofonen er praktisk talt stille. Kontroller mute og AUDIO_INPUT_DEVICE.")
            return 2
        print("Lydtesten fullførte. Hvis tonen ikke var hørbar, sett AUDIO_OUTPUT_DEVICE i raspberry/.env.")
        return 0
    except Exception as error:
        print(f"FEIL: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

