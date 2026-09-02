# Liv — designforslag 1a «Stue»

Designunderlag for nettsiden der familien setter opp Liv-boksen (Raspberry Pi + Jabra Speak, OpenAI Realtime API).

## Filer

| Fil | Bruk |
| --- | --- |
| `liv-stue.html` | Selvstendig HTML-fil. Åpne i nettleser for å se designet. Dette er referansen. |
| `Liv Stue.dc.html` + `support.js` | Kildefilen designet ble laget i. Trenger ikke brukes ved implementasjon. |
| `README.md` | Denne spesifikasjonen. |

Designet viser tre skjermer stablet under hverandre: **forside**, **innlogging**, **instruksjonsside etter innlogging**. Illustrasjonen på forsiden er en enkel SVG-skisse og bør erstattes av ordentlig illustrasjon senere.

## Retning

Varm og hjemlig, ikke teknisk. Målgruppen er pårørende til eldre og demente — ofte selv 50–75 år. Store tekststørrelser, rolige jordfarger, tydelige skillelinjer, ingen tettpakkede dashboards. Tekniske realtime-parametre ligger sammenslått bak «Tekniske innstillinger» nederst i høyre kolonne, slik at vanlige brukere ikke møter dem.

## Farger

| Rolle | Verdi |
| --- | --- |
| Sidebakgrunn | `#eceae5` |
| Kortflate / panel | `#faf6ef` |
| Sekundær flate (illustrasjon, seksjonsbakgrunn) | `#f2e9da` |
| Inputflate / innhold | `#ffffff` / `#fdfbf7` |
| Ramme | `#ded5c6`, lys variant `#ebe2d3` |
| Tekst primær | `#22201c` |
| Tekst sekundær | `#5f594f` |
| Tekst dempet | `#8a8378` |
| Aksent (terrakotta) | `#c8613f`, lys `#e07a52`, ekstra lys `#f2a184` |
| Status positiv | flate `#eef3ea`, ramme `#cdd9c6`, tekst `#2f4429`, punkt `#4f7a43` |
| Grønt i illustrasjon | `#8fa384` |
| Sand i illustrasjon | `#e9d3b8`, `#c2ac8d`, `#a8927a` |

Maks to bakgrunnsfarger per skjerm. Ingen gradienter.

## Typografi

- **Overskrifter:** Instrument Serif, regular. 60px hero, 34px sidetittel, 27px korttittel, 24px undertittel.
- **Brødtekst og UI:** Source Sans 3. 21px hero-ingress, 17–18px brødtekst, 16px labels (600), 15px hjelpetekst.
- **Tall/kode-preg:** JetBrains Mono, kun til småetiketter.
- Ingen tekst under 15px. Linjehøyde 1.5–1.6 på brødtekst. `text-wrap: pretty` på lange overskrifter.

## Form og layout

- Kortradius 20px (ytre paneler), 16–18px (indre kort), 12px (rader), 10px (input).
- Knapper: pill (`border-radius: 999px`). Primær = terrakotta med hvit tekst. Sekundær = 1px ramme `#cdc2ad`.
- Toggle: 52×30px pill, terrakotta når på.
- Rutenett: forside 1.05fr / 1fr hero, tre kolonner features. Instruksjonsside 1.35fr / 1fr, statusstrip fire like kolonner.
- Alt av grupper er flex/grid med `gap`, ikke marginer.
- Designbredde 1120px. Mobil: alle rutenett kollapser til én kolonne, statusstrip til 2×2.

## Skjerm 1 — Forside

Topplinje (logo, tre lenker, «Logg inn»-pill) → hero med illustrasjon → tre punkter med ikon: «Står bare der», «Minner på til rett tid», «Familien fyller på».

## Skjerm 2 — Innlogging

Ett kort, 440px, sentrert på `#f2e9da`. E-post, passord, primærknapp, «Glemt passord» / «Ny bruker». Ingenting mer.

## Skjerm 3 — Instruksjonsside

**Statusstrip (4 kort):** Boksen (på nett / punkt), Sist tilkoblet (`I dag 14:12`), Snakket i dag (`47 min`), Denne måneden (`18 t 40 min`).

**Venstre kolonne:**
- *Hvem er Astrid?* — stort tekstfelt for hovedinstruksen, tegnteller, «Lagre og send til boksen».
- *Dagen hennes* — påminnelsesrader `09:00` frokost, `10:00` medisiner, `22:00` kveldsmedisin, med «Endre» og «+ Legg til påminnelse».

**Høyre kolonne:**
- *Stemmen* — stemmevalg (Marin / Cedar), talehastighet-slider, oppstartssetning, minne-toggle.
- *Bruk denne måneden* — tokentall, søylediagram siste 7 dager, anslått kostnad.
- *Tekniske innstillinger* — sammenslått panel.

## Anbefalte standardverdier (bak «Tekniske innstillinger»)

| Felt | Standard | Alternativer |
| --- | --- | --- |
| Modell | `gpt-realtime` | `gpt-realtime-2.1`, `gpt-realtime-2.1-mini`, `gpt-realtime-mini` |
| Stemme | `marin` | `cedar` |
| Semantic VAD | `auto` | `low`, `medium`, `high` |
| Støyreduksjon | `far_field` | `near_field`, av |
| Transkripsjon | `gpt-realtime-whisper` | `gpt-4o-mini-transcribe`, `gpt-4o-transcribe` |
| Talehastighet | `0.90` | 0.25–1.5 |
| Maks output-tokens | `512` | 1–4096 |
| Reasoning effort | `low` | `medium` (kun 2.x-modeller) |
| Minne | 30 dager | av / alt |

Stemme kan ikke endres etter at en sesjon har produsert lyd — ny sesjon opprettes når konfigurasjonen lastes på nytt.

## Tekst og tone

Norsk bokmål. Korte setninger, konkret, ingen markedsføringsspråk. Snakk om «Astrid» og «boksen», ikke «brukeren» og «enheten». Sitater fra Liv settes i «anførselstegn».
