import importlib

import setup_trueforge as st


# --- _merge_agent_manifest -------------------------------------------------
# The exact scenarios Qodo caught during Phase 3's review: a naive PUT of a
# freshly generated manifest silently erases anything the script doesn't
# itself own -- skills, model params, other MCP servers, other nested
# config keys.

def test_merge_preserves_unrelated_top_level_fields():
    existing = {
        "model": {"name": "old-model", "params": {"temperature": 0.9}},
        "instructions": "old instructions",
        "config": {"iteration_limit": 50},
        "mcp_servers": [{"name": "some-other-server", "require_approval_for_tools": []}],
        "skills": [{"name": "custom-skill"}],
    }
    merged = st._merge_agent_manifest(existing, "google-gemini/gemini-flash-lite")

    assert merged["model"] == {"name": "google-gemini/gemini-flash-lite", "params": {"temperature": 0.9}}
    assert merged["instructions"] == st.AGENT_INSTRUCTIONS
    assert merged["config"]["iteration_limit"] == 50
    assert merged["skills"] == [{"name": "custom-skill"}]


def test_merge_preserves_other_mcp_servers_and_updates_own_entry():
    existing = {
        "model": {},
        "config": {},
        "mcp_servers": [
            {"name": "some-other-server", "require_approval_for_tools": []},
            {"name": st.MCP_SERVER_NAME, "require_approval_for_tools": []},
        ],
    }
    merged = st._merge_agent_manifest(existing, "x")

    names = [s["name"] for s in merged["mcp_servers"]]
    assert names.count(st.MCP_SERVER_NAME) == 1  # updated in place, not duplicated
    assert "some-other-server" in names
    own_entry = next(s for s in merged["mcp_servers"] if s["name"] == st.MCP_SERVER_NAME)
    assert own_entry["require_approval_for_tools"] == ["execute_trade"]


def test_merge_preserves_nested_config_sibling_keys():
    existing = {
        "model": {},
        "config": {
            "sandbox": {"enabled": False, "file_downloads": True},
            "dynamic_sub_agents": {"enabled": False, "foo": "bar"},
        },
        "mcp_servers": [],
    }
    merged = st._merge_agent_manifest(existing, "x")

    assert merged["config"]["sandbox"] == {"enabled": True, "file_downloads": True}
    assert merged["config"]["dynamic_sub_agents"] == {"enabled": True, "foo": "bar"}


def test_merge_handles_a_bare_minimal_existing_manifest():
    # No model/config/mcp_servers keys at all -- must not KeyError.
    merged = st._merge_agent_manifest({}, "x")
    assert merged["model"] == {"name": "x"}
    assert merged["config"]["sandbox"] == {"enabled": True}
    assert merged["mcp_servers"] == [{"name": st.MCP_SERVER_NAME, "require_approval_for_tools": ["execute_trade"]}]


# --- resolve_primary_model_name --------------------------------------------

def test_explicit_override_always_wins(monkeypatch):
    monkeypatch.setattr(st, "PRIMARY_MODEL_NAME_OVERRIDE", "custom/model")
    assert st.resolve_primary_model_name(gemini_ready=False, groq_ready=False, openrouter_ready=False) == "custom/model"


def test_prefers_openrouter_when_no_override(monkeypatch):
    monkeypatch.setattr(st, "PRIMARY_MODEL_NAME_OVERRIDE", None)
    assert st.resolve_primary_model_name(gemini_ready=True, groq_ready=True, openrouter_ready=True) == "openrouter/openrouter-minimax-m3"


def test_falls_back_to_gemini_when_openrouter_not_ready(monkeypatch):
    monkeypatch.setattr(st, "PRIMARY_MODEL_NAME_OVERRIDE", None)
    assert st.resolve_primary_model_name(gemini_ready=True, groq_ready=True, openrouter_ready=False) == "google-gemini/gemini-flash-lite"


def test_falls_back_to_groq_when_gemini_not_ready(monkeypatch):
    monkeypatch.setattr(st, "PRIMARY_MODEL_NAME_OVERRIDE", None)
    # The only Groq model without the reasoning_content bug -- see the
    # module's own comment on this constant.
    assert st.resolve_primary_model_name(gemini_ready=False, groq_ready=True, openrouter_ready=False) == "groq/groq-qwen3.8-27b"


def test_returns_none_when_no_provider_ready(monkeypatch):
    monkeypatch.setattr(st, "PRIMARY_MODEL_NAME_OVERRIDE", None)
    assert st.resolve_primary_model_name(gemini_ready=False, groq_ready=False, openrouter_ready=False) is None


# --- Blank env values fall back to defaults, not literal empty ------------
# A blank `KEY=` line in a copied .env.example sets the var to "", not
# absent -- os.environ.get(key, default) only falls back when the key is
# missing entirely. Reloads the module under controlled env to exercise the
# actual module-level resolution, not a reimplementation of it.

def test_blank_trueforge_url_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("TRUEFORGE_URL", "")
    monkeypatch.setenv("MCP_SERVER_URL", "")
    reloaded = importlib.reload(st)
    try:
        assert reloaded.TRUEFORGE_URL == reloaded.DEFAULT_TRUEFORGE_URL
        assert reloaded.MCP_SERVER_URL == "http://localhost:4001/mcp/"
    finally:
        monkeypatch.delenv("TRUEFORGE_URL", raising=False)
        monkeypatch.delenv("MCP_SERVER_URL", raising=False)
        importlib.reload(st)  # restore normal module state for later tests


def test_explicit_trueforge_url_is_respected(monkeypatch):
    monkeypatch.setenv("TRUEFORGE_URL", "http://localhost:9999/")
    reloaded = importlib.reload(st)
    try:
        assert reloaded.TRUEFORGE_URL == "http://localhost:9999"  # trailing slash stripped
    finally:
        monkeypatch.delenv("TRUEFORGE_URL", raising=False)
        importlib.reload(st)
