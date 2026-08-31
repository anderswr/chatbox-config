import sounddevice as sd
import numpy as np

DEVICE = 0          # Jabra
SAMPLE_RATE = 16000 # fra python -m sounddevice
DURATION = 2.0      # sekunder
FREQ = 440.0        # Hz (A-tone)

print("[INFO] Tilgjengelige enheter:")
print(sd.query_devices())

print(f"\n[INFO] Bruker device {DEVICE} ved {SAMPLE_RATE} Hz")

# Lag en ren sinus-tone
t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
data = 0.2 * np.sin(2 * np.pi * FREQ * t)  # 0.2 for å ikke være altfor høyt
data = data.astype("float32")

input("Trykk Enter for å spille en test-tone på Jabra...")

sd.play(data, samplerate=SAMPLE_RATE, device=DEVICE)
sd.wait()

print("Ferdig. Hørte du tonen?")
