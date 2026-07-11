"""
Eenvoudige, handmatig aanpasbare taalinstelling voor dit script.

De gekozen taal wordt opgeslagen in LANGUAGE_FILE (standaard: language.txt)
als platte tekst: 'nl' of 'en'. Bestaat dat bestand nog niet, dan wordt bij
het opstarten eenmalig gevraagd welke taal je wilt gebruiken.

Taal later wijzigen? Open language.txt in een teksteditor en verander de
inhoud naar 'nl' of 'en' (of verwijder het bestand om opnieuw gevraagd te
worden).
---
Simple, manually editable language setting for this script.

The chosen language is stored in LANGUAGE_FILE (default: language.txt) as
plain text: 'nl' or 'en'. If that file doesn't exist yet, you'll be asked
once, on startup, which language to use.

Want to change the language later? Open language.txt in a text editor and
change its contents to 'nl' or 'en' (or delete the file to be asked again).
"""
import os

LANGUAGE_FILE = "language.txt"

_current_language = "nl"  # fallback totdat ensure_language() is aangeroepen

STRINGS = {
    "nl": {
        "language_prompt_title": "Taal / Language",
        "language_prompt_option_nl": "  1. Nederlands",
        "language_prompt_option_en": "  2. English",
        "language_prompt_choice": "Keuze / Choice [1]: ",

        "secrets_missing": (
            "GC_SECRET_ID / GC_SECRET_KEY ontbreken. Zet ze in je .env-bestand "
            "(zie .env.example)."
        ),
        "authorize_link": "\nOpen deze link om {institution_id} te autoriseren:\n{link}\n",
        "press_enter_when_done": "Druk op Enter zodra je de autorisatie bij de bank hebt afgerond...",
        "requisition_timeout": (
            "De requisition is niet binnen de verwachte tijd gelinkt (status != 'LN'). "
            "Probeer het script opnieuw te draaien."
        ),

        "migration_start": "Bestaande koppelingen worden omgezet naar het nieuwe formaat...",
        "migration_done": "Omzetting klaar.\n",

        "search_country_prompt": "Landcode (bijv. NL, DE, BE) [{default}]: ",
        "search_term_prompt": "Zoekterm (bv. Rabobank, Bunq, Triodos) — laat leeg of vul * in voor alle banken: ",
        "no_banks_found": "Geen banken gevonden voor '{search}' in {country}.",
        "found_banks": "\nGevonden banken ({count}):",
        "select_number_prompt": "Welke wil je gebruiken? (nummer): ",
        "invalid_choice": "Ongeldige keuze.",

        "menu_title": "Welke bank wil je importeren?",
        "menu_search_option": "  {n}. Andere bank zoeken...",
        "menu_choice_prompt": "Keuze: ",
        "chosen_bank": "\nGekozen bank: {label}",

        "requisition_expired": "De eerdere koppeling met deze bank is verlopen of ongeldig; opnieuw inloggen...",
        "linking_error": "Fout bij koppelen van de bank: {error}",
        "no_accounts_found": "Geen rekeningen gevonden voor deze koppeling.",
        "accounts_found": "\n{count} rekening(en) gevonden. Transacties ophalen...",
        "account_error": "  Fout bij rekening {account_id}: {error}",

        "no_new_transactions": "  Geen nieuwe transacties voor rekening {iban}.",
        "written_file": "  {count} nieuwe transactie(s) weggeschreven naar {filename}",

        "done_with_files": "\nKlaar. Bestanden om in GnuCash te importeren:",
        "done_no_files": "\nKlaar. Geen nieuwe bestanden nodig (geen nieuwe transacties).",
    },
    "en": {
        "language_prompt_title": "Taal / Language",
        "language_prompt_option_nl": "  1. Nederlands",
        "language_prompt_option_en": "  2. English",
        "language_prompt_choice": "Keuze / Choice [1]: ",

        "secrets_missing": (
            "GC_SECRET_ID / GC_SECRET_KEY are missing. Set them in your .env file "
            "(see .env.example)."
        ),
        "authorize_link": "\nOpen this link to authorize {institution_id}:\n{link}\n",
        "press_enter_when_done": "Press Enter once you've finished authorizing with your bank...",
        "requisition_timeout": (
            "The requisition wasn't linked within the expected time (status != 'LN'). "
            "Please try running the script again."
        ),

        "migration_start": "Converting your existing bank links to the new format...",
        "migration_done": "Conversion done.\n",

        "search_country_prompt": "Country code (e.g. NL, DE, BE) [{default}]: ",
        "search_term_prompt": "Search term (e.g. Rabobank, Bunq, Triodos) — leave empty or enter * for all banks: ",
        "no_banks_found": "No banks found for '{search}' in {country}.",
        "found_banks": "\nBanks found ({count}):",
        "select_number_prompt": "Which one do you want to use? (number): ",
        "invalid_choice": "Invalid choice.",

        "menu_title": "Which bank do you want to import?",
        "menu_search_option": "  {n}. Search for another bank...",
        "menu_choice_prompt": "Choice: ",
        "chosen_bank": "\nSelected bank: {label}",

        "requisition_expired": "The previous link with this bank has expired or is no longer valid; logging in again...",
        "linking_error": "Error linking the bank: {error}",
        "no_accounts_found": "No accounts found for this link.",
        "accounts_found": "\n{count} account(s) found. Fetching transactions...",
        "account_error": "  Error for account {account_id}: {error}",

        "no_new_transactions": "  No new transactions for account {iban}.",
        "written_file": "  {count} new transaction(s) written to {filename}",

        "done_with_files": "\nDone. Files to import into GnuCash:",
        "done_no_files": "\nDone. No new files needed (no new transactions).",
    },
}


def _read_language_file():
    if os.path.exists(LANGUAGE_FILE):
        with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
            lang = f.read().strip().lower()
        if lang in STRINGS:
            return lang
    return None


def _write_language_file(lang: str) -> None:
    with open(LANGUAGE_FILE, "w", encoding="utf-8") as f:
        f.write(lang + "\n")


def _ask_language() -> str:
    s = STRINGS["nl"]
    print(s["language_prompt_title"])
    print(s["language_prompt_option_nl"])
    print(s["language_prompt_option_en"])
    choice = input(s["language_prompt_choice"]).strip()
    return "en" if choice == "2" else "nl"


def ensure_language() -> str:
    """Leest language.txt, of vraagt het eenmalig en slaat het antwoord op."""
    global _current_language
    lang = _read_language_file()
    if lang is None:
        lang = _ask_language()
        _write_language_file(lang)
    _current_language = lang
    return lang


def t(key: str, **kwargs) -> str:
    text = STRINGS.get(_current_language, STRINGS["nl"]).get(key, key)
    return text.format(**kwargs) if kwargs else text
