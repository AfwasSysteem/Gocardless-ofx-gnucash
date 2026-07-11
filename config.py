"""
Configuratie voor het GoCardless -> OFX script.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GC_SECRET_ID = os.environ.get("GC_SECRET_ID")
GC_SECRET_KEY = os.environ.get("GC_SECRET_KEY")
GC_REDIRECT_URI = os.environ.get("GC_REDIRECT_URI", "https://localhost/gocardless/callback")

GC_BASE_URL = "https://bankaccountdata.gocardless.com"

# Standaard landcode die als suggestie getoond wordt bij het zoeken naar een bank
DEFAULT_COUNTRY = "NL"

# Mapmap voor lokale bestanden
STATE_FILE = "state.json"
OUTPUT_DIR = "output"

# Hoeveel dagen historie op te halen bij de allereerste import per rekening
INITIAL_HISTORY_DAYS = 90
