import sqlite3
import threading

from . import config

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS holdings (
    asset TEXT PRIMARY KEY,
    quantity REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    asset TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price_usd REAL NOT NULL,
    usd_value REAL NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    dry_run INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS equity_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    total_usd REAL NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);
"""

# transactions.risk_snapshot: added after the original table existed in some
# already-seeded dev databases, so it can't just live in CREATE TABLE above --
# sqlite has no "ADD COLUMN IF NOT EXISTS". JSON-encoded check_risk_limits
# result computed server-side at trade time (see server.py's execute_trade
# wrapper); nullable because rows written before this migration (and the
# 'seed' rows, which never go through execute_trade) have none.
_MIGRATIONS = (
    ("transactions", "risk_snapshot", "ALTER TABLE transactions ADD COLUMN risk_snapshot TEXT"),
)

# Each thread opens its own connection on first use (see get_conn), and
# every one of those first-connections runs _run_migrations. Without a
# process-wide lock, two threads' first connections can both see a column
# missing (PRAGMA table_info) before either has run its ALTER TABLE, and
# the second ALTER then fails with "duplicate column name" -- a real Qodo
# finding, reproducible on a fresh process under concurrent early requests.
_migration_lock = threading.Lock()


def _run_migrations(conn: sqlite3.Connection) -> None:
    with _migration_lock:
        for table, column, ddl in _MIGRATIONS:
            existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                try:
                    conn.execute(ddl)
                except sqlite3.OperationalError as exc:
                    if "duplicate column name" not in str(exc):
                        raise
        conn.commit()


def get_conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is not None:
        return conn
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.commit()
    _run_migrations(conn)
    _local.conn = conn
    return conn


def get_meta(key: str) -> str | None:
    conn = get_conn()
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def reset_all() -> None:
    conn = get_conn()
    conn.executescript(
        "DELETE FROM holdings; DELETE FROM transactions; DELETE FROM meta; "
        "DELETE FROM equity_snapshots;"
    )
    conn.commit()
