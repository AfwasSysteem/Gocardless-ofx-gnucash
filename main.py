"""
GoCardless -> OFX importscript.

Gebruik:
    python main.py

Kiest bij het opstarten een bank uit je favorieten, of zoekt een nieuwe
bank op (elke bank die GoCardless ondersteunt). Haalt via de GoCardless
Bank Account Data API de transacties op sinds de vorige run, en schrijft
per rekening een .ofx-bestand weg in de map 'output/'.
"""
import os
import sys
import time
from datetime import date, timedelta

from config import DEFAULT_COUNTRY, INITIAL_HISTORY_DAYS, OUTPUT_DIR
from gocardless_client import GoCardlessClient, GoCardlessError
from i18n import ensure_language, t
from ofx_writer import build_ofx, write_ofx_file
from state import (
    load_state,
    save_state,
    get_account_state,
    update_account_state,
    get_favorites,
    add_favorite,
)


def migrate_legacy_state(state: dict, client: GoCardlessClient) -> None:
    """
    Zet een state.json van vóór de favorieten-functionaliteit om naar het
    nieuwe formaat, zodat bestaande koppelingen (ING/N26/Revolut) niet
    opnieuw geautoriseerd hoeven te worden.
    """
    legacy_institutions = state.pop("institutions", None)
    if not legacy_institutions:
        return

    print(t("migration_start"))
    old_requisitions = state.get("requisitions", {})
    new_requisitions = {}

    for bank_key, institution_id in legacy_institutions.items():
        try:
            institution = client.get_institution(institution_id)
            label = institution.get("name", institution_id)
        except GoCardlessError:
            label = institution_id  # als opzoeken mislukt, gebruik de ID als label

        add_favorite(state, institution_id, label, DEFAULT_COUNTRY)

        if bank_key in old_requisitions:
            new_requisitions[institution_id] = old_requisitions[bank_key]

    state["requisitions"] = new_requisitions
    save_state(state)
    print(t("migration_done"))


def search_bank(client: GoCardlessClient) -> dict:
    country = input(t("search_country_prompt", default=DEFAULT_COUNTRY)).strip().upper() or DEFAULT_COUNTRY
    search = input(t("search_term_prompt")).strip()
    if search == "*":
        search = ""

    matches = client.find_institution(country, search)
    if not matches:
        print(t("no_banks_found", search=search, country=country))
        sys.exit(1)

    print(t("found_banks", count=len(matches)))
    for i, inst in enumerate(matches, start=1):
        print(f"  {i}. {inst['name']}  ({inst['id']})")
    idx = input(t("select_number_prompt")).strip()
    try:
        institution = matches[int(idx) - 1]
    except (ValueError, IndexError):
        print(t("invalid_choice"))
        sys.exit(1)

    return {"institution_id": institution["id"], "label": institution["name"], "country": country}


def choose_bank(state: dict, client: GoCardlessClient) -> dict:
    favorites = get_favorites(state)

    print(t("menu_title"))
    for i, fav in enumerate(favorites, start=1):
        print(f"  {i}. {fav['label']}")
    search_option = len(favorites) + 1
    print(t("menu_search_option", n=search_option))

    choice = input(t("menu_choice_prompt")).strip()
    try:
        choice_num = int(choice)
    except ValueError:
        print(t("invalid_choice"))
        sys.exit(1)

    if 1 <= choice_num <= len(favorites):
        return favorites[choice_num - 1]

    if choice_num == search_option:
        bank = search_bank(client)
        add_favorite(state, bank["institution_id"], bank["label"], bank["country"])
        return bank

    print(t("invalid_choice"))
    sys.exit(1)


def ensure_requisition(client: GoCardlessClient, state: dict, institution_id: str) -> dict:
    cached = state["requisitions"].get(institution_id)
    if cached:
        req = client.get_requisition(cached["id"])
        if req["status"] == "LN" and req.get("accounts"):
            return req
        # Bestaande requisition is niet (meer) bruikbaar (bv. verlopen autorisatie).
        # Opruimen zodat de reference vrijkomt, en opnieuw laten inloggen.
        print(t("requisition_expired"))
        client.delete_requisition(cached["id"])

    institution = client.get_institution(institution_id)
    max_days = min(730, int(institution.get("transaction_total_days", 90)))
    agreement_id = client.create_agreement(institution_id, max_historical_days=max_days)
    reference = f"{institution_id}-{int(time.time())}"
    requisition = client.create_requisition(institution_id, agreement_id, reference)
    requisition = client.authorize_requisition_interactively(requisition)

    state["requisitions"][institution_id] = {"id": requisition["id"]}
    save_state(state)
    return requisition


def export_account(client: GoCardlessClient, state: dict, account_id: str) -> str | None:
    details = client.get_account_details(account_id)
    currency = details.get("currency", "EUR")
    iban = details.get("iban", account_id)
    bic = details.get("bic") or details.get("resourceId", "UNKNOWN")

    acc_state = get_account_state(state, account_id)
    if acc_state["last_booking_date"]:
        # één dag terug beginnen we opnieuw op te halen, als marge voor laat-geboekte transacties
        date_from = (
            date.fromisoformat(acc_state["last_booking_date"]) - timedelta(days=1)
        ).isoformat()
    else:
        date_from = (date.today() - timedelta(days=INITIAL_HISTORY_DAYS)).isoformat()

    tx_data = client.get_transactions(account_id, date_from=date_from)
    booked = tx_data.get("booked", [])

    already_seen = set(acc_state["seen_transaction_ids"])
    new_transactions = []
    for tx in booked:
        tx_id = tx.get("transactionId") or tx.get("internalTransactionId")
        if tx_id and tx_id in already_seen:
            continue
        new_transactions.append(tx)

    if not new_transactions:
        print(t("no_new_transactions", iban=iban))
        return None

    ofx_content = build_ofx(
        bank_id=bic,
        account_id=iban,
        currency=currency,
        transactions=new_transactions,
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_iban = iban.replace(" ", "")
    filename = os.path.join(OUTPUT_DIR, f"{safe_iban}_{date.today().isoformat()}.ofx")
    write_ofx_file(filename, ofx_content)

    new_ids = [tx.get("transactionId") or tx.get("internalTransactionId") for tx in new_transactions]
    new_ids = [i for i in new_ids if i]
    latest_date = max(t["bookingDate"] for t in new_transactions if t.get("bookingDate"))
    update_account_state(state, account_id, latest_date, new_ids)
    save_state(state)

    print(t("written_file", count=len(new_transactions), filename=filename))
    return filename


def main():
    ensure_language()

    state = load_state()
    client = GoCardlessClient()

    migrate_legacy_state(state, client)

    bank = choose_bank(state, client)
    print(t("chosen_bank", label=bank["label"]))

    try:
        requisition = ensure_requisition(client, state, bank["institution_id"])
    except GoCardlessError as e:
        print(t("linking_error", error=e))
        sys.exit(1)

    account_ids = requisition.get("accounts", [])
    if not account_ids:
        print(t("no_accounts_found"))
        sys.exit(1)

    print(t("accounts_found", count=len(account_ids)))
    written_files = []
    for account_id in account_ids:
        try:
            path = export_account(client, state, account_id)
            if path:
                written_files.append(path)
        except GoCardlessError as e:
            print(t("account_error", account_id=account_id, error=e))

    if written_files:
        print(t("done_with_files"))
        for f in written_files:
            print(f"  - {f}")
    else:
        print(t("done_no_files"))


if __name__ == "__main__":
    main()
