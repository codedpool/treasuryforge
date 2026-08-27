import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
MCP_SERVER_DIR = APP_DIR.parent

PORT = int(os.environ.get("PORT", "4001"))

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() not in ("false", "0", "no")

DB_PATH = Path(os.environ.get("DB_PATH", str(MCP_SERVER_DIR / "data" / "wallet.db")))

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "").strip() or None

# Fixed display-only conversion rate. FX risk is explicitly out of scope --
# everything is tracked internally in USD; this constant only affects how
# INR equity prices are shown. Not a live rate.
FX_INR_PER_USD = float(os.environ.get("FX_INR_PER_USD", "83.0"))
