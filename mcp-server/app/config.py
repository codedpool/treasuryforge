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


def _write_secret(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    try:
        os.chmod(path, 0o600)  # owner read/write only -- no-op-ish on Windows, real on Linux/Mac
    except OSError:
        pass


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
    # Always kept in sync with data/.wallet_secret regardless of source
    # (env var or generated), since scripts/setup_trueforge.py only reads
    # that file -- an env-only value it can't see would make registration
    # fail with "no shared secret found" (another real Qodo finding).
    secret_path = MCP_SERVER_DIR / "data" / ".wallet_secret"

    env_value = os.environ.get("WALLET_SHARED_SECRET", "").strip()
    if env_value:
        _write_secret(secret_path, env_value)
        return env_value

    if secret_path.exists():
        existing = secret_path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
        # Empty/whitespace-only file (e.g. an interrupted write): the auth
        # middleware compares a missing header's "" default against this
        # value, so an empty secret would silently disable authentication
        # entirely. Treat it as absent and regenerate below.

    value = secrets.token_urlsafe(32)
    _write_secret(secret_path, value)
    return value


WALLET_SHARED_SECRET = _load_or_create_shared_secret()

DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() not in ("false", "0", "no")

DB_PATH = Path(os.environ.get("DB_PATH", str(MCP_SERVER_DIR / "data" / "wallet.db")))

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "").strip() or None

# Fixed display-only conversion rate. FX risk is explicitly out of scope --
# everything is tracked internally in USD; this constant only affects how
# INR equity prices are shown. Not a live rate.
FX_INR_PER_USD = float(os.environ.get("FX_INR_PER_USD", "83.0"))
