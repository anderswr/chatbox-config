mport speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import requests

# === Hent OpenAI API-nøkkel fra lokal variabel===

from dotenv import load_dotenv

# === Last inn miljøvariabler fra .env-filen ===
load_dotenv()

# === Hent API-nøkkel og evt. andre variabler ===
openainokkel = os.getenv("openainokkel")  # Hvis du har en ekstra variabel du vil bruke

# Henter konfig fra config.json
def hent_konfig():
    try:
        r = requests.get("https://chatbox-config-fruliv.vercel.app/config.json")  # ← Endre til din Vercel-URL om nødvendig
        if r.ok:
            data = r.json()
            return data.get("system_prompt"), data.get("speak_text")
    except Exception as e:
        print(f"Feil ved henting av konfig: {e}")
    return None, None

# === Tekst-til-tale med gTTS ===
def speak(text):
    print(f"Svar: {text}")
    tts = gTTS(text=text, lang='no')
    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as fp:
        tts.save(fp.name)
        os.system(f"mpg321 {fp.name} > /dev/null 2>&1")

# === Tale-til-tekst ===
def listen():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Lytter...")
        audio = recognizer.listen(source)

    try:
        return recognizer.recognize_google(audio, language="no-NO")
    except sr.UnknownValueError:
#        speak("Beklager, jeg forstod ikke det.")
        return ""
    except sr.RequestError:
        speak("Talegjenkjenning er utilgjengelig.")
        return ""


system_prompt, speak_text = hent_konfig()
if not system_prompt:
    system_prompt = "Du er en hjelpsom, norsk samtalepartner, som stiller oppfølgingsspørsmål"
if not speak_text:
    speak_text = "Hei, vil du snakke litt?"


# === Chat med OpenAI ===
def chat(prompt, system_prompt=system_prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(model="gpt-4",
    messages=messages)
    return response.choices[0].message.content

# === Start samtalen ===
speak(speak_text)

while True:
    user_input = listen()
    if user_input:
        response = chat(user_input)
        speak(response)
