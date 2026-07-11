"""
Minimale client voor de GoCardless Bank Account Data API
(https://developer.gocardless.com/bank-account-data/overview).

Bevat alleen wat we nodig hebben: token ophalen, institutions zoeken,
agreement + requisition aanmaken, accounts en transacties ophalen.
"""
import time
import webbrowser

import requests

from config import GC_BASE_URL, GC_SECRET_ID, GC_SECRET_KEY, GC_REDIRECT_URI, INITIAL_HISTORY_DAYS
from i18n import t


class GoCardlessError(RuntimeError):
    pass


class GoCardlessClient:
    def __init__(self):
        if not GC_SECRET_ID or not GC_SECRET_KEY:
            raise GoCardlessError(t("secrets_missing"))
        self._access_token = None
        self._session = requests.Session()

    # ---------- Authenticatie ----------

    def _get_token(self) -> str:
        if self._access_token:
            return self._access_token
        resp = self._session.post(
            f"{GC_BASE_URL}/api/v2/token/new/",
            json={"secret_id": GC_SECRET_ID, "secret_key": GC_SECRET_KEY},
        )
        self._raise_for_status(resp)
        self._access_token = resp.json()["access"]
        return self._access_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
        }

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        if resp.status_code >= 400:
            raise GoCardlessError(f"GoCardless API-fout ({resp.status_code}): {resp.text}")

    # ---------- Institutions ----------

    def find_institution(self, country: str, name_contains: str) -> list:
        """Zoek instellingen in een land waarvan de naam de gegeven tekst bevat."""
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/institutions/",
            headers=self._headers(),
            params={"country": country},
        )
        self._raise_for_status(resp)
        institutions = resp.json()
        needle = name_contains.lower()
        return [i for i in institutions if needle in i["name"].lower()]

    def get_institution(self, institution_id: str) -> dict:
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/institutions/{institution_id}/",
            headers=self._headers(),
        )
        self._raise_for_status(resp)
        return resp.json()

    # ---------- Agreement + Requisition ----------

    def create_agreement(self, institution_id: str, max_historical_days: int) -> str:
        resp = self._session.post(
            f"{GC_BASE_URL}/api/v2/agreements/enduser/",
            headers=self._headers(),
            json={
                "institution_id": institution_id,
                "max_historical_days": str(max_historical_days),
                "access_valid_for_days": "90",
                "access_scope": ["balances", "details", "transactions"],
            },
        )
        self._raise_for_status(resp)
        return resp.json()["id"]

    def create_requisition(self, institution_id: str, agreement_id: str, reference: str) -> dict:
        resp = self._session.post(
            f"{GC_BASE_URL}/api/v2/requisitions/",
            headers=self._headers(),
            json={
                "redirect": GC_REDIRECT_URI,
                "institution_id": institution_id,
                "reference": reference,
                "agreement": agreement_id,
                "user_language": "NL",
            },
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_requisition(self, requisition_id: str) -> dict:
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/requisitions/{requisition_id}/",
            headers=self._headers(),
        )
        self._raise_for_status(resp)
        return resp.json()

    def delete_requisition(self, requisition_id: str) -> None:
        resp = self._session.delete(
            f"{GC_BASE_URL}/api/v2/requisitions/{requisition_id}/",
            headers=self._headers(),
        )
        # 404 betekent dat hij al weg is; dat is prima, geen probleem.
        if resp.status_code not in (200, 204, 404):
            self._raise_for_status(resp)

    def authorize_requisition_interactively(self, requisition: dict) -> dict:
        """
        Opent de autorisatielink in de browser en wacht tot de gebruiker
        klaar is bij de bank. Pollt daarna de requisition-status tot
        deze 'LN' (linked) is, of breekt af na een timeout.
        """
        link = requisition["link"]
        print(t("authorize_link", institution_id=requisition["institution_id"], link=link))
        try:
            webbrowser.open(link)
        except Exception:
            pass  # geen probleem als er geen browser beschikbaar is, de gebruiker kan de link zelf openen

        input(t("press_enter_when_done"))

        for _ in range(30):  # max ~2.5 minuut pollen
            req = self.get_requisition(requisition["id"])
            if req["status"] == "LN":
                return req
            time.sleep(5)
        raise GoCardlessError(t("requisition_timeout"))

    # ---------- Accounts + transacties ----------

    def get_account_details(self, account_id: str) -> dict:
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/accounts/{account_id}/details/",
            headers=self._headers(),
        )
        self._raise_for_status(resp)
        return resp.json().get("account", {})

    def get_account_metadata(self, account_id: str) -> dict:
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/accounts/{account_id}/",
            headers=self._headers(),
        )
        self._raise_for_status(resp)
        return resp.json()

    def get_transactions(self, account_id: str, date_from: str = None) -> dict:
        """
        Haalt transacties op. date_from is optioneel (YYYY-MM-DD); zonder
        opgave hanteert de bank zijn eigen standaardperiode (vaak 90 dagen).
        """
        params = {}
        if date_from:
            params["date_from"] = date_from
        resp = self._session.get(
            f"{GC_BASE_URL}/api/v2/accounts/{account_id}/transactions/",
            headers=self._headers(),
            params=params,
        )
        self._raise_for_status(resp)
        return resp.json().get("transactions", {})
