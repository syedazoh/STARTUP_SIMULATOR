"""Guard the operator CLI against the installed SDK's actual client signature."""

import inspect
import runpy
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
import httpx
import pytest
from mcp.client.streamable_http import streamable_http_client


@pytest.mark.asyncio
async def test_operator_script_uses_current_sdk_contract_and_hides_capability(
    monkeypatch, capsys
):
    script = runpy.run_path(str(Path(__file__).parents[1] / "scripts/check_mcp.py"))
    main = script["main"]
    scope = main.__globals__
    seen = []
    monkeypatch.setattr(
        scope["getpass"], "getpass", lambda prompt: "test-private-capability"
    )
    original = httpx.AsyncClient
    monkeypatch.setitem(
        scope,
        "httpx",
        SimpleNamespace(
            AsyncClient=lambda **kwargs: original(trust_env=False, **kwargs)
        ),
    )

    @asynccontextmanager
    async def transport(*args, **kwargs):
        # Bind against the real installed SDK, not a permissive fake signature.
        bound = inspect.signature(streamable_http_client).bind(*args, **kwargs)
        assert (
            bound.arguments["http_client"].headers["Authorization"]
            == "Bearer test-private-capability"
        )
        seen.append(bound.arguments["url"])
        yield None, None, None

    class Session:
        def __init__(self, *args):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def initialize(self):
            pass

        async def list_tools(self):
            return SimpleNamespace(tools=[SimpleNamespace(name="get_budget")])

    monkeypatch.setitem(scope, "streamable_http_client", transport)
    monkeypatch.setitem(scope, "ClientSession", Session)
    await main()
    assert len(seen) == 1
    output = capsys.readouterr().out
    assert "get_budget" in output and "test-private-capability" not in output
