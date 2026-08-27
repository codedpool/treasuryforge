#!/usr/bin/env python3
"""One-shot TrueForge setup for TreasuryForge.

Registers (idempotently, safe to re-run) against a running local TrueForge
instance (default http://localhost:8790):
  1. Google Gemini as the primary model provider (well-known type
     "google-gemini"), registering both a flagship reasoning model and a
     faster one -- see GEMINI_MODELS below.
  2. Groq as a secondary/fallback catalog entry, registered as a "custom"
     OpenAI-compatible provider (Groq isn't one of TrueForge's well-known
     types) -- see GROQ_MODELS below. NOTE: TrueForge's agent manifest takes
     a single `model.name`; nothing in the verified API surface suggests
     automatic runtime fallback between providers. Registering Groq makes
     its models available/selectable in the catalog now; switching to one
     is a manual model-name change (in this script or the TrueForge UI)
     until/unless native fallback shows up in the docs.
  3. The wallet MCP server (this repo's mcp-server/, must already be running
     -- see mcp-server/README or the repo README) at MCP_SERVER_URL, with
     execute_trade gated behind TrueForge's native approval checkpoint.
  4. The Daytona sandbox provider, if DAYTONA_API_KEY is set (skipped
     otherwise -- Phase 2 concern, not required to clear the Phase 1 /
     Foundation Checkpoint proof of "one real MCP call in TrueForge's trace").
  5. The "treasury-agent" agent itself, referencing PRIMARY_MODEL_NAME.

Every endpoint/schema this script calls was verified against
https://trueforge.dev/api-reference before writing this -- see
difficulties.md for the one that turned out not to exist as guessed.

Usage (reads GEMINI_API_KEY / GROQ_API_KEY from the repo-root .env):
    python scripts/setup_trueforge.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

TRUEFORGE_URL = os.environ.get("TRUEFORGE_URL", "http://localhost:8790").rstrip("/")
API = f"{TRUEFORGE_URL}/api/v1"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

# name = alias used in agent manifests (agent.model.name), model_id = the
# upstream provider's own identifier. Verified 2026-08-27 by querying
# https://generativelanguage.googleapis.com/v1beta/models directly with the
# real key -- web search results for model IDs were wrong twice in a row
# while building this (see difficulties.md), so this list is the ground
# truth, not a guess. Re-verify there if these ever 404.
GEMINI_MODELS = [
    {"name": "gemini-pro", "model_id": "gemini-3.1-pro-preview", "properties": {}},  # flagship reasoning
    {"name": "gemini-flash", "model_id": "gemini-3.7-flash", "properties": {}},      # fast/agentic, cheaper
]
GROQ_MODELS = [
    {"name": "groq-gpt-oss-120b", "model_id": "openai/gpt-oss-120b", "properties": {}},
    {"name": "groq-qwen3.8-27b", "model_id": "qwen/qwen3.8-27b", "properties": {}},
    {"name": "groq-qwen3.6-27b", "model_id": "qwen/qwen3.6-27b", "properties": {}},
]
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# What the treasury-agent actually runs on. Agent manifests need the fully
# qualified "provider/model" form -- the bare alias from models[].name (as
# used above for GEMINI_MODELS/GROQ_MODELS) isn't enough on its own; the
# provider identifier is the well-known type ("google-gemini") or the
# custom provider's own name ("groq").
#
# If GEMINI_API_KEY is present, this is google-gemini/gemini-flash, not
# ...gemini-pro: this project's Gemini key is on the free tier, and Pro has
# a hard 0-request free-tier quota (confirmed via a live 429 -- "limit: 0,
# model: gemini-3.1-pro" -- not a guess). Switch to google-gemini/gemini-pro
# once billing is attached to the key.
#
# An explicit PRIMARY_MODEL_NAME env var always wins. Otherwise this is
# resolved after registration against whichever provider(s) actually
# succeeded (see resolve_primary_model_name) -- a Groq-only setup must not
# silently default to an unregistered Gemini model.
PRIMARY_MODEL_NAME_OVERRIDE = os.environ.get("PRIMARY_MODEL_NAME", "").strip() or None

MCP_SERVER_NAME = "treasuryforge-wallet"
# Trailing slash matters: POST /mcp 307-redirects to /mcp/ (Starlette mount
# behavior), and not every HTTP client follows a 307 redirect on POST.
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:4001/mcp/")


def _load_wallet_shared_secret() -> str | None:
    """Same value the wallet server checks on every request but /health (see
    mcp-server/app/config.py) -- passed to TrueForge as header auth so it's
    the only caller that can actually invoke execute_trade. Only reads the
    server's generated secret file; doesn't create one -- the server must
    already be running (this script's own precondition) so it's the source
    of truth for generating it."""
    env_value = os.environ.get("WALLET_SHARED_SECRET", "").strip()
    if env_value:
        return env_value
    secret_path = os.path.join(os.path.dirname(__file__), "..", "mcp-server", "data", ".wallet_secret")
    if os.path.exists(secret_path):
        with open(secret_path, encoding="utf-8") as f:
            return f.read().strip()
    return None


WALLET_SHARED_SECRET = _load_wallet_shared_secret()

DAYTONA_API_KEY = os.environ.get("DAYTONA_API_KEY", "").strip()
DAYTONA_EXEC_TIMEOUT_MS = int(os.environ.get("DAYTONA_EXEC_TIMEOUT_MS", "10000"))
# Despite the docs describing these as accepting "0 to disable", the API
# rejects a manifest that omits them -- all three are required. Values below
# match the docs' own example.
DAYTONA_AUTO_STOP_MIN = int(os.environ.get("DAYTONA_AUTO_STOP_MIN", "5"))
DAYTONA_AUTO_ARCHIVE_MIN = int(os.environ.get("DAYTONA_AUTO_ARCHIVE_MIN", "60"))
DAYTONA_AUTO_DELETE_MIN = int(os.environ.get("DAYTONA_AUTO_DELETE_MIN", "120"))

AGENT_NAME = "treasury-agent"

AGENT_INSTRUCTIONS = """\
You manage a simulated multi-asset treasury: cash, BTC, ETH, and a small \
basket of NSE equities (RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS). The \
point is not profitability -- it is demonstrating a safe, autonomous \
decision engine.

Default to holding. Only call execute_trade when you have a concrete, \
reasoned case for a rebalance, and always state your reasoning first: the \
triggering signal, current allocation, and why this trade is warranted.

Every execute_trade call pauses for human approval -- that is intentional \
and not something to work around. Before proposing any trade, explicitly \
check and state in your reasoning whether it would breach any of these:
  - Portfolio drawdown exceeding 5% in a day
  - More than 2 consecutive losing trades
  - Resulting single-asset allocation exceeding 50% of total portfolio value
  - A "sell all" of any position
  - An equity trade while market_open is false (NSE trades 09:15-15:30 IST, \
weekdays only) -- equity trades are hard-rejected by the wallet outside \
these hours, so check get_equity_price's market_open field first and hold \
instead of proposing one

Use get_portfolio and get_transaction_log to ground your reasoning in \
actual current state before deciding anything.
"""


def _safe_print(text: str) -> None:
    # Windows consoles are often cp1252/cp437, not UTF-8; TrueForge's error
    # messages can contain arrows/checkmarks that don't map cleanly. Never
    # let a diagnostics print crash the actual operation it's reporting on.
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "backslashreplace").decode("ascii"))


def _print_response(label: str, resp: httpx.Response) -> None:
    ok = "OK" if resp.status_code < 300 else "FAILED"
    _safe_print(f"[{ok}] {label}: {resp.status_code}")
    if resp.status_code >= 300:
        _safe_print(f"       {resp.text[:500]}")


def register_gemini_provider() -> bool:
    if not GEMINI_API_KEY:
        print("[SKIP] Gemini provider: GEMINI_API_KEY not set.")
        return False
    resp = httpx.put(
        f"{API}/settings/model-providers",
        json={
            "manifest": {
                "type": "google-gemini",
                "auth": {"api_key": GEMINI_API_KEY},
                "models": GEMINI_MODELS,
            }
        },
        timeout=20.0,
    )
    _print_response(f"model provider (google-gemini: {[m['name'] for m in GEMINI_MODELS]})", resp)
    return resp.status_code < 300


def register_groq_provider() -> bool:
    if not GROQ_API_KEY:
        print("[SKIP] Groq provider: GROQ_API_KEY not set.")
        return False
    resp = httpx.put(
        f"{API}/settings/model-providers",
        json={
            "manifest": {
                "type": "custom",
                "name": "groq",
                "base_url": GROQ_BASE_URL,
                "auth": {"api_key": GROQ_API_KEY},
                "models": GROQ_MODELS,
            }
        },
        timeout=20.0,
    )
    _print_response(f"model provider (groq: {[m['name'] for m in GROQ_MODELS]})", resp)
    return resp.status_code < 300


def resolve_primary_model_name(gemini_ready: bool, groq_ready: bool) -> str | None:
    """Which model.name the agent should reference, given what actually got
    registered. An explicit PRIMARY_MODEL_NAME env var always wins (the
    caller is responsible for making sure it matches a registered model);
    otherwise prefer Gemini, fall back to Groq's first model, or None if
    neither provider is available."""
    if PRIMARY_MODEL_NAME_OVERRIDE:
        return PRIMARY_MODEL_NAME_OVERRIDE
    if gemini_ready:
        return "google-gemini/gemini-flash"
    if groq_ready:
        return f"groq/{GROQ_MODELS[0]['name']}"
    return None


def register_mcp_server() -> bool:
    if not WALLET_SHARED_SECRET:
        print(
            "[FAIL] wallet MCP server: no shared secret found at "
            "mcp-server/data/.wallet_secret -- start the wallet server first "
            "(it generates this on first run), or set WALLET_SHARED_SECRET."
        )
        return False
    manifest = {
        "type": "remote",
        "name": MCP_SERVER_NAME,
        "url": MCP_SERVER_URL,
        "description": "Paper wallet + crypto/NSE equity market data for TreasuryForge.",
        "auth": {"type": "header", "headers": {"X-Wallet-Secret": WALLET_SHARED_SECRET}},
    }
    resp = httpx.put(f"{API}/settings/mcp-servers", json={"manifest": manifest}, timeout=20.0)
    _print_response(f"MCP server ({MCP_SERVER_URL})", resp)
    return resp.status_code < 300


def register_sandbox_provider() -> bool:
    if not DAYTONA_API_KEY:
        print("[SKIP] sandbox provider: DAYTONA_API_KEY not set (Phase 2 -- not required yet).")
        return False
    resp = httpx.put(
        f"{API}/settings/sandbox-providers",
        json={
            "manifest": {
                "type": "daytona",
                "auth": {"api_key": DAYTONA_API_KEY},
                "exec_timeout_ms": DAYTONA_EXEC_TIMEOUT_MS,
                "auto_stop_interval_in_minutes": DAYTONA_AUTO_STOP_MIN,
                "auto_archive_interval_in_minutes": DAYTONA_AUTO_ARCHIVE_MIN,
                "auto_delete_interval_in_minutes": DAYTONA_AUTO_DELETE_MIN,
            }
        },
        timeout=20.0,
    )
    _print_response("sandbox provider (daytona)", resp)
    return resp.status_code < 300


def create_agent(model_name: str, sandbox_ready: bool) -> bool:
    resp = httpx.post(
        f"{API}/agents",
        json={
            "name": AGENT_NAME,
            "manifest": {
                "model": {"name": model_name},
                "instructions": AGENT_INSTRUCTIONS,
                "config": {
                    "sandbox": {"enabled": sandbox_ready},
                    "dynamic_sub_agents": {"enabled": True},
                },
                "mcp_servers": [
                    {
                        "name": MCP_SERVER_NAME,
                        "require_approval_for_tools": ["execute_trade"],
                    }
                ],
            },
        },
        timeout=20.0,
    )
    if resp.status_code == 409:
        # POST /agents is create-only (no upsert, unlike the other settings
        # endpoints -- see difficulties.md), so re-running this script hits
        # this every time after the first. That's expected, not a failure --
        # this script promises to be safe to re-run, and re-registering the
        # providers/MCP server above already picks up any credential changes
        # even though the agent's own manifest (instructions, model) won't
        # be updated by a re-run. Delete the agent first if you need that.
        print(f"[OK] agent ({AGENT_NAME}): already exists, left as-is")
        return True
    _print_response(f"agent ({AGENT_NAME}, model={model_name})", resp)
    return resp.status_code < 300


def main() -> int:
    try:
        httpx.get(f"{API}/agents", timeout=5.0)
    except httpx.ConnectError:
        print(f"TrueForge not reachable at {TRUEFORGE_URL}. Start it first.")
        return 1

    gemini_ready = register_gemini_provider()
    groq_ready = register_groq_provider()
    mcp_ready = register_mcp_server()
    sandbox_ready = register_sandbox_provider()  # optional (Phase 2) -- not required for success

    if not mcp_ready:
        print("[FATAL] wallet MCP server registration failed -- see above.")
        return 1

    model_name = resolve_primary_model_name(gemini_ready, groq_ready)
    if model_name is None:
        print("[FATAL] no model provider registered -- set GEMINI_API_KEY or GROQ_API_KEY.")
        return 1

    if not create_agent(model_name, sandbox_ready):
        print("[FATAL] agent creation failed -- see above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
