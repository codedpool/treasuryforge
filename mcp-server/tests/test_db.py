import sqlite3

import pytest

from app import db


def test_schema_creates_all_tables(isolated_db):
    tables = {
        r["name"]
        for r in isolated_db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"meta", "holdings", "transactions", "equity_snapshots"} <= tables


def test_migration_adds_risk_snapshot_column(isolated_db):
    cols = {r["name"] for r in isolated_db.execute("PRAGMA table_info(transactions)")}
    assert "risk_snapshot" in cols


def test_migration_is_idempotent(isolated_db):
    # Running it again on a connection that already has the column must not
    # raise "duplicate column name" -- this is exactly the race Qodo caught
    # between two threads' first connections (see difficulties.md, not part
    # of this repo); simulating the non-concurrent case here at minimum.
    db._run_migrations(isolated_db)
    db._run_migrations(isolated_db)
    cols = [r["name"] for r in isolated_db.execute("PRAGMA table_info(transactions)")]
    assert cols.count("risk_snapshot") == 1


def test_migration_tolerates_duplicate_column_race():
    # A prior test using isolated_db (already migrated by that fixture)
    # can't actually exercise this: _run_migrations' own PRAGMA check would
    # correctly see the column present and skip the ALTER entirely, never
    # reaching the except branch this test claims to cover (a real Qodo
    # finding). Build a raw connection instead: the column is genuinely
    # already there (as if another thread's connection just added it), but
    # PRAGMA table_info is made to report it missing -- the same stale read
    # two racing first-connections would each see -- so _run_migrations
    # actually attempts its own ALTER TABLE and has to survive the real
    # "duplicate column name" OperationalError that produces.
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA)
    conn.execute("ALTER TABLE transactions ADD COLUMN risk_snapshot TEXT")
    conn.commit()

    class StaleReadConnection:
        """sqlite3.Connection.execute is read-only (a C extension type) --
        can't monkeypatch it directly, so wrap it instead. _run_migrations
        only ever calls .execute() and .commit(), so that's all this needs
        to forward."""

        def execute(self, sql, *args, **kwargs):
            cursor = conn.execute(sql, *args, **kwargs)
            if sql.strip().upper().startswith("PRAGMA TABLE_INFO"):
                return [r for r in cursor.fetchall() if r["name"] != "risk_snapshot"]
            return cursor

        def commit(self):
            conn.commit()

    db._run_migrations(StaleReadConnection())  # must not raise despite the ALTER TABLE it attempts failing
    conn.close()


def test_meta_roundtrip(isolated_db):
    assert db.get_meta("missing_key") is None
    db.set_meta("k", "v1")
    assert db.get_meta("k") == "v1"
    db.set_meta("k", "v2")  # upsert, not insert-fails-on-conflict
    assert db.get_meta("k") == "v2"


def test_reset_all_clears_every_table(isolated_db):
    isolated_db.execute("INSERT INTO holdings (asset, quantity) VALUES ('CASH', 100)")
    isolated_db.execute(
        "INSERT INTO transactions (timestamp, asset, side, quantity, price_usd, usd_value) "
        "VALUES ('t', 'BTC', 'buy', 1, 1, 1)"
    )
    db.set_meta("k", "v")
    isolated_db.execute("INSERT INTO equity_snapshots (timestamp, total_usd) VALUES ('t', 100)")
    isolated_db.commit()

    db.reset_all()

    assert isolated_db.execute("SELECT COUNT(*) FROM holdings").fetchone()[0] == 0
    assert isolated_db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 0
    assert isolated_db.execute("SELECT COUNT(*) FROM meta").fetchone()[0] == 0
    assert isolated_db.execute("SELECT COUNT(*) FROM equity_snapshots").fetchone()[0] == 0
