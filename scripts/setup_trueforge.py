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
     otherwise). Either way, the agent below is created with
     config.sandbox.enabled=true: TrueForge falls back to its own built-in
     local (bubblewrap) provider on its own when Daytona isn't ready, but
     only if the agent actually requests a sandbox at all -- see
     create_agent's comment for why this must not be tied to Daytona's own
     registration success.
  5. The "treasury-agent" agent itself, referencing PRIMARY_MODEL_NAME --
     created if it doesn't exist, or its manifest (instructions/model/
     config) updated in place if it does, so re-running this after an
     instructions change (like Phase 3's self-audit section) actually
     reaches an already-existing agent instead of leaving it stale.

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

DEFAULT_TRUEFORGE_URL = "http://localhost:8790"
# .strip() or default, not .get(key, default): python-dotenv sets the env
# var to "" for a blank `KEY=` line in .env, which isn't the same as the
# key being absent -- .env.example documents "leave blank for the
# default", so a literal copy-and-fill-only-the-keys workflow has to
# actually produce that default, not an empty API base URL (a real Qodo
# finding).
TRUEFORGE_URL = (os.environ.get("TRUEFORGE_URL", "").strip() or DEFAULT_TRUEFORGE_URL).rstrip("/")
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
    {"name": "gemini-flash-lite", "model_id": "gemini-3.5-flash-lite", "properties": {}},  # cheapest/fastest -- default, see below
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
# If GEMINI_API_KEY is present, this is google-gemini/gemini-flash-lite, not
# ...gemini-pro or ...gemini-flash: this project's Gemini key is on the free
# tier. Pro has a hard 0-request free-tier quota (confirmed via a live 429 --
# "limit: 0, model: gemini-3.1-pro" -- not a guess). Flash has a real but low
# free-tier RPD cap that heavy same-day testing exhausts fast (confirmed via
# a live 429 -- "limit: 20, model: gemini-3.7-flash"). Flash-lite is a
# separate quota bucket entirely and stayed available through all of that --
# it's also the model a friend's parallel TrueForge project
# (github.com/Anamiiikka/Mayday) settled on for the same reason. Switch to
# google-gemini/gemini-flash or ...gemini-pro once billing is attached to
# the key and free-tier ceilings stop mattering.
#
# An explicit PRIMARY_MODEL_NAME env var always wins. Otherwise this is
# resolved after registration against whichever provider(s) actually
# succeeded (see resolve_primary_model_name) -- a Groq-only setup must not
# silently default to an unregistered Gemini model.
PRIMARY_MODEL_NAME_OVERRIDE = os.environ.get("PRIMARY_MODEL_NAME", "").strip() or None

MCP_SERVER_NAME = "treasuryforge-wallet"
# Trailing slash matters: POST /mcp 307-redirects to /mcp/ (Starlette mount
# behavior), and not every HTTP client follows a 307 redirect on POST.
# Same blank-vs-absent fix as TRUEFORGE_URL above.
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "").strip() or "http://localhost:4001/mcp/"


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
decision engine. Every tool call costs real time and quota, so be \
economical: call each tool once with complete arguments, never re-fetch \
data you already have in this turn, and keep your response to as few tool \
calls as the decision actually requires.

Standard procedure:
1. EVIDENCE (read-only, one call each): get_portfolio for current holdings, \
get_transaction_log for recent history. Default to holding unless this \
evidence gives you a concrete, reasoned case for a rebalance.
2. If you have a case, decide the exact trade (asset, side, quantity or \
usd_amount), then call check_risk_limits ONCE with those exact arguments. \
Its answer is computed, not your own estimate -- always cite its actual \
numbers in execute_trade's `reason`, never a guess. It checks:
   - Portfolio drawdown exceeding 5% in a day
   - More than 2 consecutive losing trades
   - Resulting single-asset allocation exceeding 50% of total portfolio value
   - A "sell all" of any position
3. If check_risk_limits reports any_breach=true, run exactly ONE sandbox \
Python script before deciding whether to proceed: paste the position \
values you already fetched into it as literals (no network calls -- the \
sandbox has none), apply a correlated shock (BTC/ETH down 20%, equities \
down 10%), and compute the resulting portfolio drawdown against the same \
5% limit. Cite that number in execute_trade's `reason` alongside \
check_risk_limits' numbers. Never use the sandbox to place trades or call \
any wallet tool from within it -- it is read-only analysis feeding your \
reasoning, nothing else.
4. Propose the trade: call execute_trade with your full reasoning in \
`reason`. It always pauses for human approval regardless of what \
check_risk_limits said -- that is intentional and not something to work \
around.

An equity trade while market_open is false (NSE trades 09:15-15:30 IST, \
weekdays only) is hard-rejected by the wallet outright, not gated by \
check_risk_limits -- check get_equity_price's market_open field first and \
hold instead of proposing one.

Self-audit: when asked to "run a self-audit" or "review performance," or on \
your own initiative if it has been a while since the last one and several \
new trades have happened, delegate it to a sub-agent via create_sub_agent \
-- do not do this analysis yourself inline. It has no access to this \
conversation, so give it a fully self-contained task: review the last 20 \
decisions via get_transaction_log. Not every entry has a risk_snapshot -- \
seed rows and any trade made before this field existed carry \
risk_snapshot=null -- so it must skip those, backtest only the entries that \
do have one, and state how many of the 20 it actually had usable risk data \
for rather than assuming all 20. For the ones with a snapshot (the actual \
computed daily_drawdown/consecutive_losses/concentration numbers from that \
moment, not a guess), pull get_wallet_metrics for realized/unrealized P&L, \
win rate, max drawdown, and Sharpe, then run exactly ONE sandbox script \
that backtests an alternative daily-drawdown threshold (e.g. 7% instead of \
the current 5%) against the risk_snapshot data already fetched -- no \
network calls needed, it's all in that data -- and reports how many \
decisions would have been flagged differently. Ask it to return a concise \
summary: current performance, the usable sample size, how many decisions \
breached the current threshold vs. the alternative, and one or two \
concrete rule-adjustment suggestions with that backtest evidence attached. \
Present its \
returned summary to the user as-is.
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
        return "google-gemini/gemini-flash-lite"
    if groq_ready:
        return "groq/groq-qwen3.8-27b"  # the only Groq model without the reasoning_content bug -- see difficulties.md
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


def _agent_manifest(model_name: str) -> dict:
    return {
        "model": {"name": model_name},
        "instructions": AGENT_INSTRUCTIONS,
        "config": {
            # Always requested, independent of whether Daytona registration
            # succeeded above. TrueForge's own gate is spec.config.sandbox.enabled
            # (verified in the vendored dist): if false, it never even attempts a
            # sandbox, Daytona or otherwise. When Daytona isn't ready, TrueForge
            # falls back to its built-in local (bubblewrap) provider on its own --
            # tying this flag to Daytona's success would silently disable that
            # fallback on exactly the host (WSL2) where it's the *only* sandbox
            # path that works -- see difficulties.md.
            "sandbox": {"enabled": True},
            "dynamic_sub_agents": {"enabled": True},
        },
        "mcp_servers": [
            {
                "name": MCP_SERVER_NAME,
                "require_approval_for_tools": ["execute_trade"],
            }
        ],
    }


def _merge_agent_manifest(existing_manifest: dict, model_name: str) -> dict:
    """PUT /agents/{id} replaces the *whole* manifest, not just the fields
    given -- so naively PUTting _agent_manifest()'s minimal manifest over an
    existing agent would silently erase anything not generated by this
    script: skills, model params, other MCP servers, other config TrueForge
    or a human added directly (a real Qodo finding). Only touch the fields
    this script actually owns; leave everything else in the fetched
    manifest exactly as found."""
    manifest = dict(existing_manifest)

    model = dict(manifest.get("model") or {})
    model["name"] = model_name
    manifest["model"] = model

    manifest["instructions"] = AGENT_INSTRUCTIONS

    config = dict(manifest.get("config") or {})
    # Same shallow-merge-not-replace rule one level deeper: an existing
    # agent's config.sandbox can carry other keys (file_downloads, seen on
    # a real registered agent) that a flat {"enabled": True} would discard.
    # Only set the one field this script actually owns.
    config["sandbox"] = {**(config.get("sandbox") or {}), "enabled": True}
    config["dynamic_sub_agents"] = {**(config.get("dynamic_sub_agents") or {}), "enabled": True}
    manifest["config"] = config

    mcp_servers = [
        s for s in (manifest.get("mcp_servers") or []) if s.get("name") != MCP_SERVER_NAME
    ]
    mcp_servers.append({"name": MCP_SERVER_NAME, "require_approval_for_tools": ["execute_trade"]})
    manifest["mcp_servers"] = mcp_servers

    return manifest


def create_agent(model_name: str) -> bool:
    manifest = _agent_manifest(model_name)
    resp = httpx.post(
        f"{API}/agents",
        json={"name": AGENT_NAME, "manifest": manifest},
        timeout=20.0,
    )
    if resp.status_code == 409:
        # POST /agents is create-only (no upsert, unlike the other settings
        # endpoints), but PUT /agents/{id} does update an existing agent's
        # manifest -- so re-running this script now genuinely re-applies
        # instructions/model/config changes to an already-existing agent
        # instead of silently leaving it on whatever it had at creation
        # time. That used to require deleting the agent by hand first (a
        # real Qodo finding: an existing Phase 1/2 installation would never
        # pick up Phase 3's self-audit instructions otherwise). Look the
        # agent up by name to get its current manifest and server-generated
        # id -- PUT is keyed on id, not name, and merges onto what's there
        # (see _merge_agent_manifest) rather than replacing it wholesale.
        list_resp = httpx.get(f"{API}/agents", timeout=10.0)
        if list_resp.status_code >= 300:
            _print_response(f"agent ({AGENT_NAME}): lookup for update", list_resp)
            return False
        agent = next(
            (a for a in list_resp.json().get("data", []) if a["name"] == AGENT_NAME),
            None,
        )
        if agent is None:
            print(f"[FAIL] agent ({AGENT_NAME}): got 409 on create but couldn't find it to update")
            return False
        merged = _merge_agent_manifest(agent["manifest"], model_name)
        put_resp = httpx.put(f"{API}/agents/{agent['id']}", json={"manifest": merged}, timeout=20.0)
        _print_response(f"agent ({AGENT_NAME}, model={model_name}): updated existing", put_resp)
        return put_resp.status_code < 300
    _print_response(f"agent ({AGENT_NAME}, model={model_name}): created", resp)
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
    register_sandbox_provider()  # optional (Daytona) -- agent still requests sandbox if this fails; see create_agent

    if not mcp_ready:
        print("[FATAL] wallet MCP server registration failed -- see above.")
        return 1

    model_name = resolve_primary_model_name(gemini_ready, groq_ready)
    if model_name is None:
        print("[FATAL] no model provider registered -- set GEMINI_API_KEY or GROQ_API_KEY.")
        return 1

    if not create_agent(model_name):
        print("[FATAL] agent creation failed -- see above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
