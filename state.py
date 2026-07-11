"""
Lokale state-opslag (JSON-bestand) zodat we:
- favoriete banken onthouden (zelf gekozen via het zoekmenu), zodat je
  ze niet steeds opnieuw hoeft op te zoeken
- eerder aangemaakte requisitions + rekeningen onthouden per bank
- per rekening weten wat de laatst geïmporteerde transactiedatum en
  transactie-ID's waren, om duplicaten te voorkomen bij een volgende run

Structuur:
{
  "favorites": [
    {"institution_id": "ING_INGBNL2A", "label": "ING", "country": "NL"},
    ...
  ],
  "requisitions": {
    "<institution_id>": {"id": "..."}
  },
  "accounts": {
    "<account_id>": {"last_booking_date": "...", "seen_transaction_ids": [...]}
  }
}
"""
import json
import os
from config import STATE_FILE

_DEFAULT_STATE = {
    "favorites": [],
    "requisitions": {},
    "accounts": {},
}


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return json.loads(json.dumps(_DEFAULT_STATE))  # deep copy
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # zorg dat alle top-level keys aanwezig zijn, ook na updates van dit script
    for key, value in _DEFAULT_STATE.items():
        data.setdefault(key, value)
    return data


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ---------- Favorieten ----------

def get_favorites(state: dict) -> list:
    return state["favorites"]


def find_favorite(state: dict, institution_id: str):
    for fav in state["favorites"]:
        if fav["institution_id"] == institution_id:
            return fav
    return None


def add_favorite(state: dict, institution_id: str, label: str, country: str) -> None:
    if find_favorite(state, institution_id):
        return
    state["favorites"].append({"institution_id": institution_id, "label": label, "country": country})
    save_state(state)


# ---------- Rekeningen ----------

def get_account_state(state: dict, account_id: str) -> dict:
    return state["accounts"].setdefault(
        account_id,
        {
            "last_booking_date": None,  # ISO datum (YYYY-MM-DD) van de laatst geïmporteerde transactie
            "seen_transaction_ids": [],  # lijst van reeds geëxporteerde transactie-ID's (voor dedup rond de randdatum)
        },
    )


def update_account_state(state: dict, account_id: str, last_booking_date: str, new_ids: list) -> None:
    acc_state = get_account_state(state, account_id)
    acc_state["last_booking_date"] = last_booking_date
    # Houd alleen de ID's van de laatste dag(en) bij om het bestand niet oneindig te laten groeien.
    combined = acc_state["seen_transaction_ids"] + new_ids
    acc_state["seen_transaction_ids"] = combined[-500:]
