## Liv – samtaleboks

Liv er en modulær Raspberry Pi-basert samtalepartner som bruker GA-versjonen av
OpenAI Realtime API over WebSocket. Mikrofon og høyttaler strømmes samtidig,
`semantic_vad` oppdager turer, og brukeren kan avbryte Liv mens hun snakker.

Administrasjon: https://chatbox-config.vercel.app

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
Realtime client secret fra Vercel ved hver tilkobling. Samtaleinnstillingene hentes fra
`/api/config` hvert femte minutt; endepunktet leser siste GitHub-versjon uten cache. En faktisk endring oppretter en ny
Realtime-session, mens en uendret fil ikke avbryter samtalen.
`REALTIME_MODEL` i den lokale filen er reserve hvis nettet er nede. Stemmen kan
ikke byttes etter første lyd i en session, derfor brukes webendringen først i
den nye sessionen. Støttede stemmer er `marin`, `cedar`, `alloy`,
`ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer` og `verse`.

Minnet lagres lokalt i SQLite og injiseres i instructions ved neste tilkobling.
Det er uavhengig av Memory i ChatGPT-appen. Bare ytringer som ser ut som fakta
eller preferanser lagres. Sett `MEMORY_ENABLED=false` for å deaktivere dette.
Tokenbruk logges for siste svar, inneværende prosess og akkumulert total.

`max_output_tokens` teller både tekst- og lydtokens. En grense på `512` gir i
praksis ofte bare rundt 20 sekunder tale og kan avslutte midt i et ord. Standard
er derfor `2048`. Journalen logger en tydelig advarsel med årsak hvis OpenAI
likevel returnerer et svar med status `incomplete`.

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

En oppdatert systemd-unit ligger i `raspberry/chatbox.service`. Installer den
med skriptet som også bygger et manglende eller flyttet virtualenv på nytt:

```bash
cd /home/piadmin/chatbox
chmod +x raspberry/install-service.sh
./raspberry/install-service.sh
```

Skriptet validerer bare de aktive Liv-modulene. Gamle filer som
`main.old.py` og det historiske `raspberry/venv` ignoreres og kan derfor ikke
stoppe installasjonen med irrelevante kompileringsfeil.

Systemd-uniten leser `/home/piadmin/chatbox/raspberry/.env`. Minimum er:

```dotenv
RASPBERRY_DEVICE_TOKEN=lang-tilfeldig-hemmelig-verdi
REALTIME_TOKEN_URL=https://chatbox-config.vercel.app/api/realtime-token
```

Direkte `OPENAI_API_KEY` på boksen støttes bare som reserve for lokal feilsøking.
I produksjon skal den fjernes fra boksen. Etter endring av unit eller `.env`, kjør
`sudo systemctl daemon-reload && sudo systemctl restart chatbox`.

Hvis Liv ikke starter, kjør:

```bash
sudo systemctl is-enabled chatbox
sudo systemctl status chatbox --no-pager --full
sudo journalctl -u chatbox -b -n 150 --no-pager
/home/piadmin/chatbox/raspberry/.venv/bin/python --version
cd /home/piadmin/chatbox && ./raspberry/install-service.sh
```

`is-enabled` skal svare `enabled`. Feil om `.venv/bin/python` betyr normalt at
miljøet mangler eller ble flyttet; skriptet bygger det på nytt. Kontroller også
nettinnstillingene med
`curl -fsS https://chatbox-config.vercel.app/api/config`.

Vercel-domenet skal aldri gjettes eller endres i klientkoden. Bruk domenet som
står under **Vercel → Project → Domains** i `REALTIME_TOKEN_URL`. En HTTP 404 på
`/api/realtime-token` betyr vanligvis at GitHub-versjonen med API-ruten ikke er
deployet til det eksisterende Vercel-prosjektet; det oppretter ikke et nytt
domene å endre URL-en i klienten til.

At `pages/api/realtime-token.js` vises på GitHub betyr bare at kildekoden er
merget. Det betyr ikke at Vercel har bygget den eller at et tidligere domene
fortsatt peker på prosjektet. Etter deploy kan riktig domene kontrolleres uten
hemmeligheter med:

```bash
curl -fsS https://chatbox-config.vercel.app/api/health
```

Svaret skal inneholde `"ok":true` og commit-ID-en Vercel faktisk kjører.

Før tjenesten restartes kan hele kjeden testes uten å åpne lydkortet:

```bash
cd /home/piadmin/chatbox
raspberry/.venv/bin/python -m raspberry.preflight
```

`OK: Realtime client secret mottatt` betyr at Vercel og OpenAI-nøkkelen er
klare. En forklarende 404 betyr at `pages/api/realtime-token.js` finnes i
GitHub, men ikke i Vercel-deploymenten som domenet peker på. Da må `main`
redeployes i det samme Vercel-prosjektet. Installasjonsskriptet flytter også en
gammel `CHATBOX_CONFIG_URL=.../config.json` til raw GitHub automatisk.

Hvis tjenesten kjører, men du ikke hører lyd, stopp den midlertidig slik at den
ikke låser lydkortet og kjør den innebygde lydtesten som samme bruker:

```bash
sudo systemctl stop chatbox
cd /home/piadmin/chatbox
raspberry/.venv/bin/python -m raspberry.diagnose_audio
sudo systemctl start chatbox
sudo journalctl -u chatbox -f
```

Testen skriver ut alle lydkort, valgt mikrofon/høyttaler, spiller en testtone
og måler mikrofonnivået. Hvis feil enhet velges, legg indeks eller en del av
enhetsnavnet i `raspberry/.env`, for eksempel:

```dotenv
AUDIO_INPUT_DEVICE=Jabra
AUDIO_OUTPUT_DEVICE=Jabra
```

Ved normal drift skal journalen vise `Mikrofonstrøm mottatt`,
`Realtime-event: session.updated` og `Første lydpakke fra OpenAI mottatt`.
Hvis de to første finnes, men den siste mangler, ligger feilen mellom
Realtime-konfigurasjonen og OpenAI – ikke i høyttaleren.

### Lagring fra administrasjonssiden

Lagreknappen oppdaterer `public/config.json` gjennom GitHub Contents API.
`/api/config` leser alltid `public/config.json` direkte fra GitHub med cache avslått.
Dermed krever senere innstillingsendringer ingen ny Vercel-build. Denne
versjonen må likevel deployes én gang for å installere endepunktet.

Disse miljøvariablene må settes i Vercel:

```dotenv
GH_TOKEN=github-fine-grained-token-med-contents-write
GH_REPO=anderswr/chatbox-config
GH_BRANCH=main
PIADMIN_PASSWORD=...
PIADMIN_SESSION_SECRET=lang-tilfeldig-verdi
```

GitHub-tokenet må ha tilgang til repoet og **Contents: Read and write**.
`GITHUB_TOKEN` kan brukes som alternativt navn. Etter første oppsett av
variablene må Vercel redeployes én gang. Adminsiden viser den konkrete
serverfeilen dersom GitHub avviser lagringen.

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
