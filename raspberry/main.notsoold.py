#!/usr/bin/env python3
"""
main.py – Realtime stemmeassistent med gpt-realtime, auto-lytting

- Leser config fra Vercel (system_prompt, speak_text, voice, ev. api_key)
- Fallback hvis Vercel ikke svarer (forteller det høyt)
- Bruker gpt-realtime via WebSocket
- Leser opp oppstarts-setningen via Realtime-TTS
- Kjører kontinuerlig lytte-loop (ingen Enter for å snakke):
    - Auto-opptak med enkel VAD
    - Sender lyd til modellen når du har snakket og blitt stille
    - Spiller av svar
    - Logger alt (RMS, transkripsjoner, feilmeldinger) til terminal
"""

import os
import json
import base64
import asyncio
from typing import Optional, List, Tuple

import numpy as np
import sounddevice as sd
import requests
from dotenv import load_dotenv
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError


# ============================================================
#  KONFIG FRA Vercel + .env
# ============================================================

CONFIG_URL = "https://chatbox-config-fruliv.vercel.app/config.json"


def hent_konfig():
    try:
        print(f"[KONFIG] Henter config fra {CONFIG_URL} ...")
        r = requests.get(CONFIG_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        print("[KONFIG] Mottatt config:", data)
        system_instruction = data.get("system_instruction") or data.get("system_prompt")
        api_key = data.get("api_key")
        speak_text = data.get("speak_text")
        voice = data.get("voice")
        return system_instruction, api_key, speak_text, voice, True
    except Exception as e:
        print(f"[KONFIG] Feil ved henting av konfig: {e}")
        return None, None, None, None, False


load_dotenv()
system_instruction_cfg, api_key_cfg, speak_text_cfg, voice_cfg, config_ok = hent_konfig()

if not system_instruction_cfg:
    system_instruction_cfg = (
        "Du heter Liv, og er en hjelpsom og morsom norsk samtalepartner. "
        "Du kan stille hyggelige oppfølgingsspørsmål for å holde samtalen i gang. "
        "Innimellom tar du med noen relevante funfacts i samtalen."
    )

API_KEY = api_key_cfg or os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "Fant ingen API-nøkkel i Vercel-config eller miljøvariabelen OPENAI_API_KEY."
    )

VOICE = voice_cfg or "alloy"

if config_ok:
    SPEAK_TEXT = (
        speak_text_cfg
        or "Hei, vil du ha en god samtale. Du kan spørre meg om alt mulig rart."
    )
else:
    SPEAK_TEXT = (
        "Hei! Jeg fikk ikke kontakt med administrasjonssiden på nettet, "
        "så jeg bruker et lokalt standardoppsett akkurat nå. "
        "Det betyr at jeg kanskje ikke har helt oppdatert informasjon eller personlighet, "
        "men jeg skal gjøre så godt jeg kan. "
        "Du kan snakke til meg når som helst, så svarer jeg etter tur."
    )

print("[INIT] system_instruction:", system_instruction_cfg)
print("[INIT] voice:", VOICE)
print("[INIT] speak_text:", SPEAK_TEXT)
print("[INIT] config_ok:", config_ok)


# ============================================================
#  AUDIO-OPPSETT
# ============================================================

INPUT_DEVICE = "sysdefault"
OUTPUT_DEVICE = "sysdefault"

DEVICE_SAMPLE_RATE = 16000      # Jabra
API_SAMPLE_RATE = 24000         # gpt-realtime pcm16
DTYPE = "int16"
CHANNELS = 1

# Auto-lytting / VAD-parametre (tunet litt mer følsomt og raskt)
MAX_SECONDS = 15.0          # maks varighet per uttale
MIN_SECONDS = 0.4           # minst så lenge med lyd før stillhet kan avslutte
SILENCE_DURATION = 0.5      # hvor lenge stille før vi stopper
SILENCE_THRESHOLD = 100.0   # RMS under dette => "stille" i blokk
SPEECH_MIN_RMS = 150.0      # global RMS må over dette for at vi sender til modellen


def debug_list_devices():
    print("[AUDIO] Tilgjengelige enheter fra sounddevice:")
    try:
        print(sd.query_devices())
    except Exception as e:
        print("[AUDIO] Klarte ikke å liste enheter:", e)


debug_list_devices()
print(f"[AUDIO] INPUT_DEVICE={INPUT_DEVICE}, OUTPUT_DEVICE={OUTPUT_DEVICE}")
print(f"[AUDIO] DEVICE_SAMPLE_RATE={DEVICE_SAMPLE_RATE}, API_SAMPLE_RATE={API_SAMPLE_RATE}")
print(f"[AUDIO] VAD-parametre: MIN_SECONDS={MIN_SECONDS}, SILENCE_DURATION={SILENCE_DURATION}, "
      f"SILENCE_THRESHOLD={SILENCE_THRESHOLD}, SPEECH_MIN_RMS={SPEECH_MIN_RMS}")


def resample_int16(data: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out or len(data) == 0:
        return data

    x_old = np.linspace(0, 1, num=len(data), endpoint=False, dtype=np.float32)
    new_len = int(round(len(data) * sr_out / sr_in))
    if new_len <= 0:
        return np.zeros(0, dtype=np.int16)

    x_new = np.linspace(0, 1, num=new_len, endpoint=False, dtype=np.float32)
    data_f = data.astype(np.float32)
    resampled = np.interp(x_new, x_old, data_f).astype(np.int16)
    return resampled


def record_until_silence() -> Tuple[bytes, float]:
    """
    Auto-opptak med enkel VAD.
    Returnerer (pcm24k_bytes, global_rms).
    """
    print(
        f"[REC] Starter auto-opptak (max {MAX_SECONDS}s, stillhet={SILENCE_DURATION}s, "
        f"terskel={SILENCE_THRESHOLD:.1f})"
    )

    block_duration = 0.2
    block_frames = int(DEVICE_SAMPLE_RATE * block_duration)

    all_samples: List[np.ndarray] = []
    total_frames = 0
    silence_frames = 0

    min_frames = int(MIN_SECONDS * DEVICE_SAMPLE_RATE)
    max_frames = int(MAX_SECONDS * DEVICE_SAMPLE_RATE)
    silence_frames_needed = int(SILENCE_DURATION * DEVICE_SAMPLE_RATE)

    with sd.InputStream(
        samplerate=DEVICE_SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        device=INPUT_DEVICE,
    ) as stream:
        print("🎤 Lytter... snakk når du vil (Ctrl+C for å avslutte hele programmet).")
        while True:
            data, overflowed = stream.read(block_frames)
            if overflowed:
                print("[REC] ADVARSEL: overflow i inputstream!")

            chunk = data[:, 0].astype(np.int16)
            all_samples.append(chunk)
            frames = len(chunk)
            total_frames += frames

            if frames > 0:
                rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            else:
                rms = 0.0

            if rms < SILENCE_THRESHOLD:
                silence_frames += frames
            else:
                silence_frames = 0

            # Debug ca. hvert sekund
            if total_frames % (DEVICE_SAMPLE_RATE * 1) < block_frames:
                total_sec = total_frames / DEVICE_SAMPLE_RATE
                silence_sec = silence_frames / DEVICE_SAMPLE_RATE
                print(
                    f"[REC] total={total_sec:.1f}s, rms={rms:.1f}, stille_i={silence_sec:.1f}s"
                )

            if total_frames >= max_frames:
                print("[REC] Stopp: nådd maks lengde.")
                break

            if total_frames >= min_frames and silence_frames >= silence_frames_needed:
                print("[REC] Stopp: stillhet registrert.")
                break

    if total_frames == 0:
        print("[REC] Ingen lyd fanget opp.")
        return b"", 0.0

    pcm_dev = np.concatenate(all_samples)
    print(f"[REC] Totale samples @16k: {len(pcm_dev)}")

    pcm_api = resample_int16(pcm_dev, DEVICE_SAMPLE_RATE, API_SAMPLE_RATE)
    print(f"[REC] Totale samples resamplet til 24k: {len(pcm_api)}")

    if len(pcm_api) > 0:
        rms_all = float(np.sqrt(np.mean(pcm_api.astype(np.float32) ** 2)))
        print(f"[REC] RMS-level (hele opptaket): {rms_all:.1f}")
    else:
        rms_all = 0.0
        print("[REC] ADVARSEL: 0 samples etter resampling!")

    return pcm_api.tobytes(), rms_all


def play_api_audio(audio_bytes_24k: bytes):
    if not audio_bytes_24k:
        print("[PLAY] Ingen bytes å spille av.")
        return

    pcm_api = np.frombuffer(audio_bytes_24k, dtype=np.int16)
    print(f"[PLAY] Mottatt {len(pcm_api)} samples @ 24k")

    pcm_dev = resample_int16(pcm_api, API_SAMPLE_RATE, DEVICE_SAMPLE_RATE)
    print(f"[PLAY] Etter resampling: {len(pcm_dev)} samples @ 16k")

    if len(pcm_dev) == 0:
        print("[PLAY] ADVARSEL: 0 samples etter resampling, ingenting å spille.")
        return

    print("[PLAY] Spiller av svar fra modellen...")
    sd.play(pcm_dev, samplerate=DEVICE_SAMPLE_RATE, device=OUTPUT_DEVICE)
    sd.wait()
    print("[PLAY] Avspilling ferdig.")


# ============================================================
#  HANDLE RESPONSE
# ============================================================

async def handle_response(ws):
    audio_chunks: List[bytes] = []

    while True:
        try:
            raw = await ws.recv()
        except (ConnectionClosedOK, ConnectionClosedError) as e:
            print(f"[WS] Forbindelse lukket i handle_response: {e}")
            return

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            print("[WS] Klarte ikke å parse melding som JSON:", raw)
            continue

        etype: Optional[str] = event.get("type")
        if not etype:
            print("[WS] Event uten type:", event)
            continue

        print(f"[WS←] type={etype}")

        if etype in ("response.output_audio.delta", "response.audio.delta"):
            delta = event.get("delta") or event.get("audio")
            if isinstance(delta, dict):
                delta = delta.get("audio")
            if delta:
                chunk = base64.b64decode(delta)
                audio_chunks.append(chunk)
                print(f"[WS←] audio.delta mottatt, chunk-len={len(chunk)}")
            continue

        if etype in ("response.output_audio.done", "response.audio.done"):
            print("[WS←] audio.done – samler og spiller av")
            if audio_chunks:
                all_audio = b"".join(audio_chunks)
                play_api_audio(all_audio)
                audio_chunks.clear()
            else:
                print("[PLAY] Ingen audio-chunks samlet opp før done.")
            continue

        if etype == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                print(f"[ASSISTENT-TEXT-DELTA] {delta}", end="", flush=True)
            elif isinstance(delta, dict):
                content = delta.get("content")
                if content:
                    print(f"[ASSISTENT-TEXT-DELTA] {content}", end="", flush=True)
            continue

        if etype == "response.output_text.done":
            print()
            continue

        if etype == "response.audio_transcript.delta":
            delta = event.get("delta") or event.get("text")
            if delta:
                print(f"[ASSISTENT-SA] {delta}", end="", flush=True)
            continue

        if etype == "response.audio_transcript.done":
            transcript = (
                event.get("transcript")
                or event.get("text")
                or event.get("input_text")
            )
            if transcript:
                print(f"\n[ASSISTENT-SA-END] {transcript}")
            else:
                print()
            continue

        if etype == "conversation.item.input_audio_transcription.delta":
            delta = event.get("delta") or event.get("text")
            if delta:
                print(f"[BRUKER-SA] {delta}", end="", flush=True)
            continue

        if etype == "conversation.item.input_audio_transcription.completed":
            transcript = (
                event.get("transcript")
                or event.get("text")
                or event.get("input_text")
            )
            if transcript:
                print(f"\n[BRUKER-SA-END] {transcript}")
            else:
                print()
            continue

        if etype == "response.error":
            print("[RESPONS-FEIL]", json.dumps(event, indent=2))
            continue

        if etype == "error":
            print("[SERVER-FEIL]", json.dumps(event, indent=2))
            continue

        if etype in ("response.completed", "response.done"):
            print("[WS] Response fullført.")
            break


# ============================================================
#  REALTIME HOVEDLØKKE
# ============================================================

async def run_realtime():
    model = "gpt-realtime"
    url = f"wss://api.openai.com/v1/realtime?model={model}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    print(f"[WS] Kobler til {url} ...")
    try:
        async with connect(url, additional_headers=headers) as ws:
            print("[WS] Tilkoblet OpenAI Realtime!")
            print(f"[SESSION] Modell: {model}, stemme: {VOICE}")
            print("[INFO] Ctrl+C i terminalen for å avslutte programmet.")

            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": system_instruction_cfg,
                    "voice": VOICE,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1",
                        "language": "no",
                    },
                },
            }
            print("[WS→] session.update:", json.dumps(session_update))
            await ws.send(json.dumps(session_update))

            greeting_evt = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": SPEAK_TEXT,
                        }
                    ],
                },
            }
            print("[WS→] conversation.item.create (greeting)")
            await ws.send(json.dumps(greeting_evt))

            resp_create_greet = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"],
                },
            }
            print("[WS→] response.create (greeting)")
            await ws.send(json.dumps(resp_create_greet))

            await handle_response(ws)

            turn_index = 1
            while True:
                print(f"\n======= NY TUR #{turn_index} – jeg lytter nå =======")
                pcm_api_bytes, rms_all = record_until_silence()

                if len(pcm_api_bytes) == 0:
                    print("[MAIN] Ingen lyd fanget opp i denne turen. Prøver igjen.")
                    continue

                if rms_all < SPEECH_MIN_RMS:
                    print(
                        f"[MAIN] RMS={rms_all:.1f} < SPEECH_MIN_RMS={SPEECH_MIN_RMS}, "
                        "tolker dette som ingen tydelig tale – sender ikke til modellen."
                    )
                    turn_index += 1
                    continue

                audio_b64 = base64.b64encode(pcm_api_bytes).decode("ascii")
                print(f"[MAIN] Tur #{turn_index}: Lyd encode b64-lengde: {len(audio_b64)}")

                item_evt = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "audio": audio_b64,
                            }
                        ],
                    },
                }
                print("[WS→] conversation.item.create (audio)")
                await ws.send(json.dumps(item_evt))

                resp_create = {
                    "type": "response.create",
                    "response": {
                        "modalities": ["audio", "text"],
                    },
                }
                print("[WS→] response.create (audio+text)")
                await ws.send(json.dumps(resp_create))

                await handle_response(ws)
                turn_index += 1

    except Exception as e:
        print(f"[WS] Klarte ikke å koble til eller kjøre Realtime: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_realtime())
    except KeyboardInterrupt:
        print(
            "\n[MAIN] Avslutter. "
            "Hvis noe går galt neste gang, lover jeg at vi i hvert fall har nok debug til å klatre alle stiger og unngå slangene 😏"
        )
