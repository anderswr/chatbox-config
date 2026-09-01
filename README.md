## Liv – samtaleboks

Liv er en modulær Raspberry Pi-basert samtalepartner som bruker GA-versjonen av
OpenAI Realtime API over WebSocket. Mikrofon og høyttaler strømmes samtidig,
`semantic_vad` oppdager turer, og brukeren kan avbryte Liv mens hun snakker.

Administrasjon: https://chatbox-config-fruliv.vercel.app

### Raspberry Pi

```bash
cd raspberry
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Legg RASPBERRY_DEVICE_TOKEN i raspberry/.env, og start fra repo-roten:
cd ..
raspberry/.venv/bin/python -m raspberry.main
```

PortAudio må være installert på operativsystemet (på Raspberry Pi OS:
`sudo apt install libportaudio2`). OpenAI-nøkkelen skal bare ligge som en
beskyttet miljøvariabel i Vercel og aldri i offentlig `config.json`.

Den langsiktige OpenAI-nøkkelen ligger bare som `OPENAI_API_KEY` i Vercel og
sendes aldri til Raspberry Pi-en, nettsiden eller `config.json`. Boksen har kun
en egen `RASPBERRY_DEVICE_TOKEN` i `raspberry/.env` og henter en kortlivet
Realtime client secret fra Vercel ved hver tilkobling. Samtaleinnstillingene hentes fra nettsidens
offentlige `config.json` hvert femte minutt; en faktisk endring oppretter en ny
Realtime-session, mens en uendret fil ikke avbryter samtalen.
`REALTIME_MODEL` i den lokale filen er reserve hvis nettet er nede. Stemmen kan
ikke byttes etter første lyd i en session, derfor brukes webendringen først i
den nye sessionen. Støttede stemmer er `marin`, `cedar`, `alloy`,
`ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer` og `verse`.

Minnet lagres lokalt i SQLite og injiseres i instructions ved neste tilkobling.
Det er uavhengig av Memory i ChatGPT-appen. Bare ytringer som ser ut som fakta
eller preferanser lagres. Sett `MEMORY_ENABLED=false` for å deaktivere dette.
Tokenbruk logges for siste svar, inneværende prosess og akkumulert total.

Admin-siden styrer hovedinstruks, oppstartssetning, modell og stemme. Under
avanserte taleinnstillinger kan man også styre talehastighet (0,25–1,5×),
støyreduksjon for nær- eller fjernmikrofon, transkripsjonsmodell, maksimal
svarlengde og reasoning effort for Realtime 2-modeller. `marin` og `cedar` er
anbefalte stemmer; `far_field` passer en Jabra konferansehøyttaler.

### Oppdater boksen med Git

Kjør dette fra repoet på Raspberry Pi-en:

```bash
cd /home/piadmin/chatbox
git pull
raspberry/.venv/bin/pip install -r raspberry/requirements.txt
sudo systemctl restart chatbox
sudo journalctl -u chatbox -n 100 --no-pager
```

`main.py` i rotmappen er et kompatibilitets-startpunkt for den eksisterende
servicen som bruker `WorkingDirectory=/home/piadmin/chatbox` og kjører
`python3 main.py`. Selve implementasjonen ligger fortsatt i
`raspberry/main.py`.

En oppdatert systemd-unit ligger i `raspberry/chatbox.service`. Den kan
installeres slik:

```bash
sudo cp raspberry/chatbox.service /etc/systemd/system/chatbox.service
sudo chown piadmin:piadmin /home/piadmin/chatbox/raspberry/.env
sudo chmod 0600 /home/piadmin/chatbox/raspberry/.env
sudo systemctl daemon-reload
sudo systemctl enable --now chatbox
```

Systemd-uniten leser `/home/piadmin/chatbox/raspberry/.env`. Minimum er:

```dotenv
RASPBERRY_DEVICE_TOKEN=lang-tilfeldig-hemmelig-verdi
REALTIME_TOKEN_URL=https://chatbox-config-fruliv.vercel.app/api/realtime-token
```

Direkte `OPENAI_API_KEY` på boksen støttes bare som reserve for lokal feilsøking.
I produksjon skal den fjernes fra boksen. Etter endring av unit eller `.env`, kjør
`sudo systemctl daemon-reload && sudo systemctl restart chatbox`.

Administratorpassordet ligger ikke i kildekoden. Sett eller reset
`PIADMIN_PASSWORD` og en tilfeldig `PIADMIN_SESSION_SECRET` under Vercel →
Project Settings → Environment Variables, og redeploy. Brukernavnet er `boks1`.
Legg også inn `OPENAI_API_KEY` og samme `RASPBERRY_DEVICE_TOKEN` i Vercel.

### Moduler

* `config.py` – validerte miljøinnstillinger.
* `audio.py` – full-dupleks capture/playback og umiddelbar lokal interrupt.
* `realtime_client.py` – GA WebSocket-events, semantic VAD, truncate og reconnect.
* `memory.py` – lokalt persistent brukerminne i SQLite.
* `usage.py` – tokenbruk per svar, sesjon og akkumulert.
* `main.py` – signaler, levetid og opprydding.
