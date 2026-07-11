# GoCardless → OFX importscript / import script

*Nederlands hieronder*

---


## English

Fetches bank transactions via GoCardless Bank Account Data and writes them
per account as an `.ofx` file, ready to import into GnuCash.

### Installation

```bash
pip install -r requirements.txt
cp .env.example .env
```

Fill in your GoCardless `GC_SECRET_ID` and `GC_SECRET_KEY` in `.env`
(create these at https://bankaccountdata.gocardless.com/ → User secrets).

### Language

The very first time you run `python main.py`, it asks whether you want to
use Dutch or English. That choice is saved in **`language.txt`** (plain
text: `nl` or `en`) and won't be asked again after that.

Want to change the language later? Open `language.txt` in a text editor
and change its contents to `nl` or `en` — or delete the file to be asked
again on the next run.

### Usage

```bash
python main.py
```

- On startup you pick a bank from your **favorites** (banks you've used
  before), or choose "Search for another bank..." to look up any bank
  supported by GoCardless (e.g. Rabobank, Bunq, Triodos, or a foreign
  bank). Enter a country code (e.g. `NL`, `DE`, `BE`) and a search term —
  leave the search term empty or enter `*` to see all banks in that
  country. Once selected, the bank is automatically added to your
  favorites and will appear as a numbered quick option from then on.
- The first time you use a bank, you'll need to log in via a link in your
  browser to grant access (this is handled by GoCardless, not by this
  script). After that, the link is remembered locally in `state.json`, so
  you won't need to do this every run. If the link expires (after the
  allowed period, often ~90 days), the script detects this automatically
  and will show you the login link again.
- The first import for an account fetches 90 days of history by default
  (configurable via `INITIAL_HISTORY_DAYS` in `config.py`). Subsequent
  runs only fetch transactions since the last imported date, with
  deduplication by transaction ID so you never get duplicate transactions
  in GnuCash.
- For each account with new transactions, a file is written to `output/`,
  e.g. `NL00INGB0000000000_2026-07-11.ofx`.

#### If you have an older state.json

Used this script before (with a fixed bank list in `config.py`)? No
problem: on the first run, the script automatically converts your
existing links to the new favorites format. You won't need to log in to
your banks again.

### Files

- `main.py` — entry point, menu and orchestration
- `gocardless_client.py` — API communication with GoCardless
- `ofx_writer.py` — generates OFX 1.0.2 files directly (no external OFX library)
- `state.py` — local storage of links and import history (`state.json`)
- `i18n.py` — language strings (Dutch/English) and the language-selection logic
- `language.txt` — your chosen language (`nl` or `en`), safe to edit by hand
- `config.py` — settings (default country, history period, etc.)

### Note

- `state.json` and `.env` contain sensitive information (links/secrets) —
  don't share them or commit them to version control.
- GoCardless' free tier has a limit on API calls per link per day, so
  avoid running the script too often in a row.
- If an institution search returns multiple results (e.g. for Revolut,
  which has multiple entities), you pick the right one from the menu;
  that choice is then remembered.

  ## Nederlands

Haalt banktransacties op via GoCardless Bank Account Data en schrijft ze
per rekening weg als `.ofx`-bestand, klaar om in GnuCash te importeren.

### Installatie

```bash
pip install -r requirements.txt
cp .env.example .env
```

Vul in `.env` je GoCardless `GC_SECRET_ID` en `GC_SECRET_KEY` in
(aan te maken via https://bankaccountdata.gocardless.com/ → User secrets).

### Taal

Bij de allereerste keer dat je `python main.py` draait, vraagt het script
of je Nederlands of Engels wilt gebruiken. Dat antwoord wordt opgeslagen
in **`language.txt`** (gewoon platte tekst: `nl` of `en`) en daarna niet
meer gevraagd.

Wil je de taal later wijzigen? Open `language.txt` in een teksteditor en
verander de inhoud naar `nl` of `en` — of verwijder het bestand om
opnieuw gevraagd te worden bij de volgende run.

### Gebruik

```bash
python main.py
```

- Je kiest bij het opstarten een bank uit je **favorieten** (banken die je
  al eerder hebt gebruikt), of je kiest "Andere bank zoeken..." om een
  willekeurige bank te zoeken die GoCardless ondersteunt (bijv. Rabobank,
  Bunq, Triodos, of een buitenlandse bank). Vul dan een landcode (bijv.
  `NL`, `DE`, `BE`) en een zoekterm in — laat de zoekterm leeg of vul `*`
  in om alle banken in dat land te zien. De gevonden bank wordt na keuze
  automatisch aan je favorieten toegevoegd en verschijnt vanaf dan gewoon
  als genummerde snelkeuze.
- De eerste keer per bank moet je via een link in je browser inloggen bij
  de bank om toegang te geven (dit doet GoCardless, niet dit script).
  Daarna wordt de koppeling lokaal onthouden in `state.json` — je hoeft
  dit dus niet elke run opnieuw te doen. Verloopt de koppeling (na de
  toegestane periode, vaak ~90 dagen), dan herkent het script dat
  automatisch en krijg je vanzelf opnieuw de inlog-link te zien.
- Bij een eerste import per rekening wordt standaard 90 dagen historie
  opgehaald (in te stellen via `INITIAL_HISTORY_DAYS` in `config.py`).
  Bij volgende runs wordt alleen opgehaald sinds de laatst geïmporteerde
  transactiedatum, met een dedup-check op transactie-ID zodat je nooit
  dubbele transacties in GnuCash krijgt.
- Per rekening met nieuwe transacties komt er een bestand in `output/`,
  bijvoorbeeld `NL00INGB0000000000_2026-07-11.ofx`.

#### Als je een ouder state.json hebt

Had je dit script al eerder gebruikt (met een vaste bankenlijst in
`config.py`)? Geen probleem: bij de eerste run zet het script je bestaande
koppelingen automatisch om naar het nieuwe favorieten-formaat. Je hoeft
niet opnieuw in te loggen bij je banken.

### Bestanden

- `main.py` — startpunt, menu en orkestratie
- `gocardless_client.py` — API-communicatie met GoCardless
- `ofx_writer.py` — genereert de OFX 1.0.2-bestanden zelf (geen externe OFX-library)
- `state.py` — lokale opslag van koppelingen en importgeschiedenis (`state.json`)
- `i18n.py` — taalteksten (Nederlands/Engels) en de taalkeuzelogica
- `language.txt` — jouw gekozen taal (`nl` of `en`), handmatig aan te passen
- `config.py` — instellingen (standaardland, historieperiode, etc.)

### Let op

- `state.json` en `.env` bevatten gevoelige informatie (koppelingen/secrets)
  — niet delen of in versiebeheer zetten.
- GoCardless' gratis tier heeft een limiet op het aantal API-calls per
  koppeling per dag; draai het script dus niet te vaak achter elkaar.
- Mocht de institution-zoekopdracht meerdere resultaten geven (bijv. bij
  Revolut, dat meerdere entiteiten heeft), kies je zelf de juiste uit het
  menu; die keuze wordt daarna onthouden.

---

