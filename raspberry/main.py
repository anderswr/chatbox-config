#!/usr/bin/env python3
"""
main.py – Realtime stemmeassistent med gpt-realtime, auto-lytting

- Leser config fra Vercel (system_instruction/system_prompt, speak_text, voice, ev. api_key)
- Fallback hvis Vercel ikke svarer (forteller det høyt)
- Bruker gpt-realtime via WebSocket
- Leser opp oppstarts-setningen via Realtime
- Kjører kontinuerlig lytte-loop (ingen Enter for å snakke):
    - Auto-opptak med enkel VAD
    - Sender lyd til modellen når du har snakket og blitt stille
    - Spiller av svar
- Robusthet:
    - Reconnect-loop ved WS-fall (1011 keepalive ping timeout osv.)
    - Lokal historikk sendes inn igjen ved ny tilkobling (føles som "fortsetter samtalen")
- Logging:
    - Logger til fil med dato+klokkeslett i filnavn
    - Logger også til stdout (journalctl)
"""

import os
import json
import base64
import asyncio
import time
import random
from datetime import datetime
from typing import Optional, List, Tuple, Dict

import numpy as np
import sounddevice as sd
import requests
from dotenv import load_dotenv
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError


# ============================================================
#  LOGGING TIL FIL + STDOUT
# ============================================================

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, f"chatbox_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")


def log(*args):
    msg = " ".join(str(a) for a in args)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


log(f"[LOG] Logger til: {LOG_PATH}")


# ============================================================
#  KONFIG FRA Vercel + .env
# ============================================================

CONFIG_URL = "https://chatbox-config-fruliv.vercel.app/config.json"


def hent_konfig():
    try:
        log(f"[KONFIG] Henter config fra {CONFIG_URL} ...")
        r = requests.get(CONFIG_URL, timeout=5)
        r.raise_for_status()
        data = r.json()
        log("[KONFIG] Mottatt config:", data)
        system_instruction = data.get("system_instruction") or data.get("system_prompt")
        api_key = data.get("api_key")
        speak_text = data.get("speak_text")
        voice = data.get("voice")
        return system_instruction, api_key, speak_text, voice, True
    except Exception as e:
        log(f"[KONFIG] Feil ved henting av konfig: {e}")
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
    raise RuntimeError("Fant ingen API-nøkkel i Vercel-config eller miljøvariabelen OPENAI_API_KEY.")

VOICE = voice_cfg or "alloy"

if config_ok:
    SPEAK_TEXT = speak_text_cfg or "Hei, vil du ha en fantastisk samtale. Du kan spørre meg om alt mulig rart."
else:
    SPEAK_TEXT = (
        "Hei! Jeg fikk ikke kontakt med administrasjonssiden på nettet, "
        "så jeg bruker et lokalt standardoppsett akkurat nå. "
        "Det betyr at jeg kanskje ikke har helt oppdatert informasjon eller personlighet, "
        "men jeg skal gjøre så godt jeg kan."
    )

log("[INIT] system_instruction:", system_instruction_cfg)
log("[INIT] voice:", VOICE)
log("[INIT] speak_text:", SPEAK_TEXT)
log("[INIT] config_ok:", config_ok)


# ============================================================
#  LOKALT MINNE (for å "fortsette samtalen" etter reconnect)
# ============================================================

CONTEXT_MEMORY: List[Dict[str, str]] = []   # {"role": "user"/"assistant", "text": "..."}
MAX_CONTEXT_TURNS = 12


def remember(role: str, text: str):
    text = (text or "").strip()
    if not text:
        return
    CONTEXT_MEMORY.append({"role": role, "text": text})
    # hold buffer begrenset
    max_items = MAX_CONTEXT_TURNS * 2
    if len(CONTEXT_MEMORY) > max_items:
        del CONTEXT_MEMORY[: len(CONTEXT_MEMORY) - max_items]


async def send_context(ws):
    """
    Sender lokal historikk inn som system-kontekst etter reconnect.
    Dette gjør at modellen fortsetter mer naturlig etter nett-drop.
    """
    if not CONTEXT_MEMORY:
        return

    lines = []
    for m in CONTEXT_MEMORY[-MAX_CONTEXT_TURNS * 2:]:
        who = "Bruker" if m["role"] == "user" else "Assistent"
        # hold det kompakt
        lines.append(f"{who}: {m['text']}")
    recap = (
        "Kontekst (samtalen fortsatte etter en kort nett-/tilkoblingsglipp). "
        "Her er siste dialog:\n" + "\n".join(lines)
    )

    evt = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "system",
            "content": [{"type": "input_text", "text": recap}],
        },
    }
    await ws.send(json.dumps(evt))
    log("[CTX] Sendte historikk til ny sesjon.")


# ============================================================
#  AUDIO-OPPSETT
# ============================================================

DEVICE_SAMPLE_RATE = 16000
INPUT_API_SAMPLE_RATE = 24000

# OBS: Realtime audio output har hos deg oppført seg som 8k PCM16.
# Hvis OpenAI endrer dette, kan vi justere senere, men dette matcher debug-linjene dine.
OUTPUT_API_SAMPLE_RATE = 8000

DTYPE = "int16"
CHANNELS = 1

# VAD – litt raskere respons enn før
MAX_SECONDS = 10.0
MIN_SECONDS = 1.2           # kortere "lock-in" før vi kan avslutte på stillhet
SILENCE_DURATION = 0.55     # kortere pause før vi svarer
SILENCE_THRESHOLD = 120.0
SPEECH_MIN_RMS = 150.0


def list_and_choose_devices() -> Tuple[Optional[int], Optional[int]]:
    """
    Lister opp lyd-enheter og velger Jabra for inn/ut hvis tilgjengelig.
    Hvis ikke: bruker system-default (None).
    """
    log("[AUDIO] Tilgjengelige enheter fra sounddevice:")
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            log(
                f"  {idx}: {dev['name']} "
                f"({dev['max_input_channels']} in, {dev['max_output_channels']} out, "
                f"default_sr={dev['default_samplerate']})"
            )
    except Exception as e:
        log("[AUDIO] Klarte ikke å liste enheter:", e)
        return None, None

    jabra_index = None
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            name = dev["name"]
            if ("Jabra" in name) or ("SPEAK 510" in name):
                # vi vil helst ha enhet med output-kanaler også
                if int(dev.get("max_output_channels", 0)) > 0:
                    jabra_index = idx
                    break
        if jabra_index is None:
            # fallback: ta Jabra selv om output ikke synes (men da blir det stille)
            for idx, dev in enumerate(devices):
                name = dev["name"]
                if ("Jabra" in name) or ("SPEAK 510" in name):
                    jabra_index = idx
                    break
    except Exception as e:
        log("[AUDIO] Klarte ikke å søke etter Jabra:", e)

    if jabra_index is not None:
        try:
            dev = sd.query_devices(jabra_index)
            log(
                f"[AUDIO] Fant Jabra-enhet på index {jabra_index}, "
                f"in={dev['max_input_channels']} out={dev['max_output_channels']} "
                f"default_sr={dev['default_samplerate']}"
            )
        except Exception:
            log(f"[AUDIO] Fant Jabra-enhet på index {jabra_index}.")
        return jabra_index, jabra_index

    log("[AUDIO] Fant ikke Jabra-enhet. Bruker system-default (None) for inn/ut.")
    return None, None


INPUT_DEVICE, OUTPUT_DEVICE = list_and_choose_devices()

log(f"[AUDIO] INPUT_DEVICE={INPUT_DEVICE}, OUTPUT_DEVICE={OUTPUT_DEVICE}")
log(
    f"[AUDIO] DEVICE_SAMPLE_RATE={DEVICE_SAMPLE_RATE}, "
    f"INPUT_API_SAMPLE_RATE={INPUT_API_SAMPLE_RATE}, OUTPUT_API_SAMPLE_RATE={OUTPUT_API_SAMPLE_RATE}"
)
log(
    f"[AUDIO] VAD: MIN_SECONDS={MIN_SECONDS}, SILENCE_DURATION={SILENCE_DURATION}, "
    f"SILENCE_THRESHOLD={SILENCE_THRESHOLD}, SPEECH_MIN_RMS={SPEECH_MIN_RMS}"
)


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
    Returnerer (pcm_bytes @ INPUT_API_SAMPLE_RATE, global_rms).
    """

    log(
        f"[REC] Starter auto-opptak (max {MAX_SECONDS}s, stillhet={SILENCE_DURATION}s, "
        f"terskel={SILENCE_THRESHOLD:.1f}, device_sr={DEVICE_SAMPLE_RATE})"
    )

    # mindre blokker gir raskere "stopp på stillhet" og mer naturlig flyt
    block_duration = 0.15
    block_frames = int(DEVICE_SAMPLE_RATE * block_duration)

    all_samples: List[np.ndarray] = []
    total_frames = 0
    silence_frames = 0

    min_frames = int(MIN_SECONDS * DEVICE_SAMPLE_RATE)
    max_frames = int(MAX_SECONDS * DEVICE_SAMPLE_RATE)
    silence_frames_needed = int(SILENCE_DURATION * DEVICE_SAMPLE_RATE)

    input_kwargs = dict(
        samplerate=DEVICE_SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
    )
    if INPUT_DEVICE is not None:
        input_kwargs["device"] = INPUT_DEVICE

    with sd.InputStream(**input_kwargs) as stream:
        log("🎤 Lytter... snakk når du vil (Ctrl+C for å avslutte hele programmet).")
        last_log_sec = -1

        while True:
            data, overflowed = stream.read(block_frames)
            if overflowed:
                log("[REC] ADVARSEL: overflow i inputstream!")

            chunk = data[:, 0].astype(np.int16)
            all_samples.append(chunk)
            frames = len(chunk)
            total_frames += frames

            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2))) if frames > 0 else 0.0

            if rms < SILENCE_THRESHOLD:
                silence_frames += frames
            else:
                silence_frames = 0

            # log ca 1 gang/sek (ikke spam)
            total_sec = int(total_frames / DEVICE_SAMPLE_RATE)
            if total_sec != last_log_sec:
                last_log_sec = total_sec
                silence_sec = silence_frames / DEVICE_SAMPLE_RATE
                log(f"[REC] total={total_frames/DEVICE_SAMPLE_RATE:.1f}s, rms={rms:.1f}, stille_i={silence_sec:.1f}s")

            if total_frames >= max_frames:
                log("[REC] Stopp: nådd maks lengde.")
                break

            if total_frames >= min_frames and silence_frames >= silence_frames_needed:
                log("[REC] Stopp: stillhet registrert.")
                break

    if total_frames == 0:
        log("[REC] Ingen lyd fanget opp.")
        return b"", 0.0

    pcm_dev = np.concatenate(all_samples)
    log(f"[REC] Totale samples @{DEVICE_SAMPLE_RATE}: {len(pcm_dev)}")

    pcm_api = resample_int16(pcm_dev, DEVICE_SAMPLE_RATE, INPUT_API_SAMPLE_RATE)
    log(f"[REC] Totale samples resamplet til INPUT_API_SAMPLE_RATE={INPUT_API_SAMPLE_RATE}: {len(pcm_api)}")

    rms_all = float(np.sqrt(np.mean(pcm_api.astype(np.float32) ** 2))) if len(pcm_api) else 0.0
    log(f"[REC] RMS-level (hele opptaket @{INPUT_API_SAMPLE_RATE}): {rms_all:.1f}")

    return pcm_api.tobytes(), rms_all


def play_api_audio(audio_bytes_out: bytes):
    """
    Spiller av modellens lyd.

    Antar at audio_bytes_out er PCM16 @ OUTPUT_API_SAMPLE_RATE (8 kHz),
    resampler til DEVICE_SAMPLE_RATE (16 kHz).

    Håndterer 1-kanal og 2-kanals output.
    """
    if not audio_bytes_out:
        log("[PLAY] Ingen bytes å spille av.")
        return

    pcm_api = np.frombuffer(audio_bytes_out, dtype=np.int16)
    log(f"[PLAY] Mottatt {len(pcm_api)} samples @ {OUTPUT_API_SAMPLE_RATE}")

    pcm_dev = resample_int16(pcm_api, OUTPUT_API_SAMPLE_RATE, DEVICE_SAMPLE_RATE)
    log(f"[PLAY] Etter resampling: {len(pcm_dev)} samples @{DEVICE_SAMPLE_RATE}")

    if len(pcm_dev) == 0:
        log("[PLAY] ADVARSEL: 0 samples etter resampling, ingenting å spille.")
        return

    # Finn output-kanaler
    try:
        dev_info = sd.query_devices(OUTPUT_DEVICE if OUTPUT_DEVICE is not None else None, "output")
        max_out = int(dev_info["max_output_channels"])
        log(f"[PLAY] Output-enhet '{dev_info['name']}' max_output_channels={max_out}")
    except Exception as e:
        log(f"[PLAY] Klarte ikke å hente output-device info: {e}")
        return

    if max_out <= 0:
        log("[PLAY] Ingen output-kanaler tilgjengelig akkurat nå – sjekk USB/HDMI.")
        return

    if max_out == 1:
        data = pcm_dev
    else:
        data = np.column_stack([pcm_dev, pcm_dev])  # stereo-dupe

    play_kwargs = dict(samplerate=DEVICE_SAMPLE_RATE)
    if OUTPUT_DEVICE is not None:
        play_kwargs["device"] = OUTPUT_DEVICE

    log("[PLAY] Spiller av svar fra modellen...")
    sd.play(data, **play_kwargs)
    sd.wait()
    log("[PLAY] Avspilling ferdig.")


# ============================================================
#  HANDLE RESPONSE – ryddigere debug + returnerer tekst
# ============================================================

async def handle_response(ws) -> Tuple[str, str]:
    """
    Leser events for én respons fra Realtime-APIet.
    - Samler audio til ett svar (spilles i play_api_audio)
    - Samler assistent-transkript (ASSISTENT-SA-END)
    - Samler brukertranskript (BRUKER-SA-END)
    Returnerer (assistant_text, user_text)
    """
    audio_chunks: List[bytes] = []
    assistant_text = ""
    user_text = ""

    while True:
        try:
            raw = await ws.recv()
        except (ConnectionClosedOK, ConnectionClosedError) as e:
            log(f"[WS] Forbindelse lukket i handle_response: {e}")
            raise  # viktig: bubler opp, så reconnect-loop slår inn

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            log("[WS] Klarte ikke å parse melding som JSON.")
            continue

        etype: Optional[str] = event.get("type")
        if not etype:
            continue

        # --- Lyd fra modellen ---
        if etype in ("response.output_audio.delta", "response.audio.delta"):
            delta = event.get("delta") or event.get("audio")
            if isinstance(delta, dict):
                delta = delta.get("audio")
            if delta:
                audio_chunks.append(base64.b64decode(delta))
            continue

        if etype in ("response.output_audio.done", "response.audio.done"):
            if audio_chunks:
                all_audio = b"".join(audio_chunks)
                audio_chunks.clear()
                play_api_audio(all_audio)
            continue

        # --- Assistentens transkript ---
        if etype == "response.audio_transcript.delta":
            delta = event.get("delta") or event.get("text")
            if delta:
                assistant_text += delta
            continue

        if etype == "response.audio_transcript.done":
            if assistant_text.strip():
                log(f"[ASSISTENT-SA-END] {assistant_text.strip()}")
            else:
                log("[ASSISTENT-SA-END] (tomt transkript)")
            continue

        # --- Brukerens transkript ---
        if etype == "conversation.item.input_audio_transcription.delta":
            delta = event.get("delta") or event.get("text")
            if delta:
                user_text += delta
            continue

        if etype == "conversation.item.input_audio_transcription.completed":
            if user_text.strip():
                log(f"[BRUKER-SA-END] {user_text.strip()}")
            else:
                log("[BRUKER-SA-END] (ingen gjenkjent tale)")
            continue

        # --- Feil ---
        if etype in ("response.error", "error"):
            log("[WS-FEIL]", json.dumps(event, indent=2))
            continue

        # --- Slutt på respons ---
        if etype in ("response.completed", "response.done"):
            log("[WS] Response fullført.")
            break

    return assistant_text.strip(), user_text.strip()


# ============================================================
#  REALTIME – én connection-session
# ============================================================

async def run_realtime_once():
    model = "gpt-realtime"
    url = f"wss://api.openai.com/v1/realtime?model={model}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }

    log(f"[WS] Kobler til {url} ...")

    # ping_interval/ping_timeout: hjelper litt mot “stille” perioder og treghet
    async with connect(
        url,
        additional_headers=headers,
        ping_interval=20,
        ping_timeout=20,
        open_timeout=20,
        max_size=16 * 1024 * 1024,
    ) as ws:
        log("[WS] Tilkoblet OpenAI Realtime!")
        log(f"[SESSION] Modell: {model}, stemme: {VOICE}")
        log("[INFO] Ctrl+C i terminalen for å avslutte programmet.")

        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": system_instruction_cfg,
                "voice": VOICE,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1", "language": "no"},
            },
        }
        await ws.send(json.dumps(session_update))
        log("[WS→] session.update sendt")

        # Send historikk ved reconnect (før greeting)
        await send_context(ws)

        # Greeting
        greeting_evt = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": SPEAK_TEXT}],
            },
        }
        await ws.send(json.dumps(greeting_evt))
        log("[WS→] conversation.item.create (greeting)")

        await ws.send(json.dumps({"type": "response.create", "response": {"modalities": ["audio", "text"]}}))
        log("[WS→] response.create (greeting)")

        a_text, u_text = await handle_response(ws)
        # greeting er "system" så vi lagrer ikke u_text her; men vi kan lagre assistenten hvis ønskelig:
        if a_text:
            remember("assistant", a_text)

        turn_index = 1
        while True:
            log(f"\n======= NY TUR #{turn_index} – jeg lytter nå =======")
            pcm_api_bytes, rms_all = record_until_silence()

            if len(pcm_api_bytes) == 0:
                log("[MAIN] Ingen lyd fanget opp i denne turen. Prøver igjen.")
                continue

            if rms_all < SPEECH_MIN_RMS:
                log(f"[MAIN] RMS={rms_all:.1f} < SPEECH_MIN_RMS={SPEECH_MIN_RMS} – sender ikke til modellen.")
                turn_index += 1
                continue

            audio_b64 = base64.b64encode(pcm_api_bytes).decode("ascii")
            log(f"[MAIN] Tur #{turn_index}: Lyd encode b64-lengde: {len(audio_b64)} (INPUT_API_SAMPLE_RATE={INPUT_API_SAMPLE_RATE})")

            item_evt = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_audio", "audio": audio_b64}],
                },
            }
            await ws.send(json.dumps(item_evt))
            log("[WS→] conversation.item.create (audio)")

            await ws.send(json.dumps({"type": "response.create", "response": {"modalities": ["audio", "text"]}}))
            log("[WS→] response.create (audio+text)")

            assistant_text, user_text = await handle_response(ws)

            # lagre historikk for "resume"
            if user_text:
                remember("user", user_text)
            if assistant_text:
                remember("assistant", assistant_text)

            turn_index += 1


# ============================================================
#  RECONNECT-LOOP
# ============================================================

async def run_realtime_forever():
    attempt = 1
    while True:
        try:
            log(f"[MAIN] Starter Realtime (forsøk #{attempt}) ...")
            await run_realtime_once()
            log("[MAIN] run_realtime_once() avsluttet normalt. Starter på nytt om 2s.")
            time.sleep(2)
            attempt = 1
        except KeyboardInterrupt:
            raise
        except Exception as e:
            # Backoff + litt jitter
            wait = min(30, 2 + attempt) + random.random()
            log(f"[MAIN] Realtime falt ut: {e}")
            log(f"[MAIN] Reconnect om {wait:.1f}s ...")
            time.sleep(wait)
            attempt += 1


if __name__ == "__main__":
    try:
        asyncio.run(run_realtime_forever())
    except KeyboardInterrupt:
        log(
            "[MAIN] Avslutter manuelt. "
            "Hvis noe går galt neste gang, lover jeg at vi i hvert fall har nok debug til å klatre alle stiger og unngå slangene 😏"
        )
