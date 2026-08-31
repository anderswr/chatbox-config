import sounddevice as sd

DEVICE = 'sysdefault'          # Jabra
SAMPLE_RATE = 16000
DTYPE = "int16"
CHANNELS = 1
DURATION = 3.0      # sekunder

print(sd.query_devices())

input(f"Trykk Enter, så tar vi opp {DURATION} sekunder fra Jabra ved {SAMPLE_RATE} Hz...")

frames = int(SAMPLE_RATE * DURATION)

recording = sd.rec(
    frames,
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype=DTYPE,
    device=DEVICE,
)
sd.wait()

print("Opptak ferdig. Spiller av det samme på Jabra...")

sd.play(recording, samplerate=SAMPLE_RATE, device=DEVICE)
sd.wait()

print("Ferdig.")
