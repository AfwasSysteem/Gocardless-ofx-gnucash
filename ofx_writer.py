"""
Genereert handmatig OFX 1.0.2 (SGML) bestanden, zonder externe OFX-library.
OFX 1.0.2 SGML wordt door GnuCash prima geïmporteerd.
"""
import hashlib
from datetime import datetime, timezone


def _ofx_date(date_str: str) -> str:
    """YYYY-MM-DD -> YYYYMMDD (OFX-datumformaat)."""
    return date_str.replace("-", "")


def _now_ofx() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _make_fitid(tx: dict) -> str:
    """
    Uniek transactie-ID voor OFX (FITID). GoCardless levert meestal
    transactionId of internalTransactionId; als die ontbreken, maken we
    een stabiele hash van de overige velden zodat dezelfde transactie
    bij een volgende run hetzelfde ID krijgt (nodig voor dedup in GnuCash).
    """
    for key in ("transactionId", "internalTransactionId"):
        if tx.get(key):
            return tx[key]
    basis = "|".join(
        [
            tx.get("bookingDate", ""),
            tx.get("transactionAmount", {}).get("amount", ""),
            tx.get("remittanceInformationUnstructured", ""),
            tx.get("creditorName", "") or tx.get("debtorName", ""),
        ]
    )
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:24]


def _tx_name(tx: dict) -> str:
    name = tx.get("creditorName") or tx.get("debtorName") or "Onbekend"
    return _escape(name)


def _tx_memo(tx: dict) -> str:
    memo = tx.get("remittanceInformationUnstructured")
    if not memo:
        lines = tx.get("remittanceInformationUnstructuredArray")
        memo = " ".join(lines) if lines else ""
    return _escape(memo)


def _escape(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .strip()
    )


def build_ofx(
    *,
    bank_id: str,
    account_id: str,
    currency: str,
    transactions: list,
    balance_amount: str = None,
    balance_date: str = None,
) -> str:
    """
    Bouwt een volledige OFX 1.0.2 SGML-string voor één rekening.

    transactions: lijst van GoCardless 'booked' transactie-dicts.
    """
    dtserver = _now_ofx()

    if transactions:
        dates = [t["bookingDate"] for t in transactions if t.get("bookingDate")]
        dtstart = _ofx_date(min(dates))
        dtend = _ofx_date(max(dates))
    else:
        dtstart = dtend = dtserver[:8]

    tx_blocks = []
    for tx in transactions:
        amount = tx.get("transactionAmount", {}).get("amount", "0")
        trntype = "CREDIT" if float(amount) >= 0 else "DEBIT"
        booking_date = _ofx_date(tx.get("bookingDate") or tx.get("valueDate"))
        fitid = _make_fitid(tx)

        tx_blocks.append(
            f"""        <STMTTRN>
          <TRNTYPE>{trntype}
          <DTPOSTED>{booking_date}
          <TRNAMT>{amount}
          <FITID>{fitid}
          <NAME>{_tx_name(tx)}
          <MEMO>{_tx_memo(tx)}
        </STMTTRN>"""
        )

    ledger_block = ""
    if balance_amount is not None:
        bal_date = _ofx_date(balance_date) if balance_date else dtend
        ledger_block = f"""      <LEDGERBAL>
        <BALAMT>{balance_amount}
        <DTASOF>{bal_date}
      </LEDGERBAL>
"""

    ofx = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS>
        <CODE>0
        <SEVERITY>INFO
      </STATUS>
      <DTSERVER>{dtserver}
      <LANGUAGE>NLD
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <TRNUID>{dtserver}
      <STATUS>
        <CODE>0
        <SEVERITY>INFO
      </STATUS>
      <STMTRS>
        <CURDEF>{currency}
        <BANKACCTFROM>
          <BANKID>{_escape(bank_id)}
          <ACCTID>{_escape(account_id)}
          <ACCTTYPE>CHECKING
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>{dtstart}
          <DTEND>{dtend}
{chr(10).join(tx_blocks)}
        </BANKTRANLIST>
{ledger_block}      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>
"""
    return ofx


def write_ofx_file(path: str, ofx_content: str) -> None:
    # OFX 1.0.2 SGML wordt standaard als platte tekst (CRLF is niet vereist) weggeschreven.
    with open(path, "w", encoding="cp1252", errors="replace") as f:
        f.write(ofx_content)
