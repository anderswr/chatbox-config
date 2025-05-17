import os
import time
import speech_recognition as sr
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv


# Sett inn din OpenAI API-nøkkel
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")



recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Systeminstruksjon / rollebeskrivelse
SYSTEM_PROMPT = "Du er en ekspert på frisbeegolf og snakker gjerne om det. Utover det så svarer du høffelig på alle slags spørsmål, og stiller oppfølgingsspørsmål for å holde samtalen igang. Innimellom spør du spillet yatzy. Du heter Liv og er en pappeske med et rikt indre liv"

def speak(text):
    print("Svar:", text)
    tts = gTTS(text=text, lang="no")
    tts.save("response.mp3")
    os.system("mpg123 response.mp3")

def listen():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Snakk nå...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language="no-NO")
    except sr.UnknownValueError:
        return "Beklager, jeg hørte ikke det."
    except sr.RequestError as e:
        return f"Feil med talegjenkjenning: {e}"

def chat(prompt, system_prompt=SYSTEM_PROMPT):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    speak("Hei, hva skjer hos deg i dag ?")
    while True:
        user_input = listen()
        if user_input.lower() in ["død", "dødare"]:
            speak("å nei, du dødet meg. nå trenger jeg en omstart for å virke igjen. Ja, faktisk!")
            break
        response = chat(user_input)
        speak(response)
