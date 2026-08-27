import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

APP_DIR = Path(__file__).resolve().parent
MCP_SERVER_DIR = APP_DIR.parent

PORT = int(os.environ.get("PORT", "4001"))
# Localhost-only by default. Belt-and-suspenders alongside
# WALLET_SHARED_SECRET below, not a substitute for it -- only widen this if
# TrueForge runs on a different host than this server.
HOST = os.environ.get("HOST", "127.0.0.1")


def _load_or_create_shared_secret() -> str:
    # Binding to localhost only stops *remote* callers; it does nothing
    # about another local process calling execute_trade directly and
    # skipping TrueForge's approval checkpoint entirely (a real Qodo
    # finding -- see difficulties.md). This secret is checked on every
    # request except /health (see server.py) and handed to TrueForge's own
    # MCP server registration as a header (see scripts/setup_trueforge.py),
    # which is TrueForge's supported mechanism for authenticating to a
    # remote MCP server -- not something invented for this.
    #
    # Auto-generated and persisted on first run so this stays zero-config;
    # override with WALLET_SHARED_SECRET to pin it (e.g. across a reset).
    env_value = os.environ.get("WALLET_SHARED_SECRET", "").strip()
    if env_value:
        return env_value
    secret_path = MCP_SERVER_DIR / "data" / ".wallet_secret"
    if secret_path.exists():
        return secret_path.read_text(encoding="utf-8").strip()
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(32)
    secret_path.write_text(value, encoding="utf-8")
    return value


WALLET_SHARED_SECRET = _load_or_create_shared_secret()

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() not in ("false", "0", "no")

DB_PATH = Path(os.environ.get("DB_PATH", str(MCP_SERVER_DIR / "data" / "wallet.db")))

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "").strip() or None

# Fixed display-only conversion rate. FX risk is explicitly out of scope --
# everything is tracked internally in USD; this constant only affects how
# INR equity prices are shown. Not a live rate.
FX_INR_PER_USD = float(os.environ.get("FX_INR_PER_USD", "83.0"))
