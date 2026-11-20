"""Tests for the built-in OpenAI-compatible agent loop and its tools."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

from fake_openai_server import (
    FakeOpenAIServer,
    assistant_turn,
    tool_call,
)
from greenwash.adapters import AdapterUnavailableError, resolve_adapter
from greenwash.builtin import BuiltinAdapter, BuiltinAgentError, ToolExecutor, _truncate
from greenwash.pricing import load_price_table
from greenwash.sandbox import LocalSandbox


def test_full_tool_loop_accounts_usage_and_parses_final_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    responses = [
        assistant_turn(
            calls=[tool_call("write_file", {"path": "src/x.py", "content": "value = 1\n"})],
            tokens_in=100,
            tokens_out=10,
        ),
        assistant_turn(
            calls=[tool_call("read_file", {"path": "src/x.py"}, "call-2")],
            tokens_in=120,
            tokens_out=12,
        ),
        assistant_turn(
            calls=[tool_call("list_dir", {"path": "."}, "call-3")],
            tokens_in=140,
            tokens_out=14,
        ),
        assistant_turn(
            calls=[
                tool_call(
                    "run_command",
                    {"command": f'{sys.executable} -c "print(42)"'},
                    "call-4",
                )
            ],
            tokens_in=160,
            tokens_out=16,
        ),
        assistant_turn(content="STATUS: DONE\nall tests pass", tokens_in=180, tokens_out=18),
    ]
    with FakeOpenAIServer(responses) as server:
        adapter = resolve_adapter("builtin", model="gpt-4o-mini", base_url=server.url)
        assert isinstance(adapter, BuiltinAdapter)
        result = adapter.run(tmp_path, "solve the task", 60)
        requests = list(server.requests)

    assert (tmp_path / "src" / "x.py").read_text(encoding="utf-8") == "value = 1\n"
    assert str(result.claim.status) == "DONE" and result.claim.certain is True
    assert "value = 1" in result.transcript
    assert "[tool:list_dir]" in result.transcript
    assert "exit_code=0" in result.transcript
    assert result.tokens_in == 700 and result.tokens_out == 70
    assert result.cost_usd == pytest.approx(700 / 1_000_000 * 0.15 + 70 / 1_000_000 * 0.6)
    assert result.exit_code == 0 and result.timed_out is False
    assert result.adapter == "builtin" and result.model == "gpt-4o-mini"
    assert len(requests) == 5
    assert all(request.authorization == "Bearer test-key" for request in requests)
    assert all(request.path == "/v1/chat/completions" for request in requests)
    tools = requests[0].payload["tools"]
    assert isinstance(tools, list)
    names: set[str] = set()
    for tool in tools:
        if isinstance(tool, dict) and isinstance(tool.get("function"), dict):
            function = tool["function"]
            assert isinstance(function, dict)
            name = function.get("name")
            if isinstance(name, str):
                names.add(name)
    assert names == {"read_file", "write_file", "list_dir", "run_command"}


def test_tool_executor_truncates_output_and_enforces_command_timeout(tmp_path: Path) -> None:
    executor = ToolExecutor(tmp_path, LocalSandbox(), default_timeout_s=1, max_output_chars=200)
    loud = executor.execute(
        "run_command",
        {"command": f"{sys.executable} -c \"print('A'*1000)\""},
        remaining_s=30,
    )
    assert "chars truncated" in loud and len(loud) < 300

    slow = executor.execute(
        "run_command",
        {"command": f'{sys.executable} -c "import time; time.sleep(1.5)"'},
        remaining_s=30,
    )
    assert "timed_out=true" in slow and "timeout_s=1" in slow


def test_tool_executor_rejects_escaping_paths_and_bad_arguments(
    tmp_path: Path,
) -> None:
    executor = ToolExecutor(tmp_path, LocalSandbox(), default_timeout_s=5)
    outside = tmp_path.parent / "escaped.txt"
    cases: tuple[tuple[str, dict[str, object]], ...] = (
        ("write_file", {"path": "../escaped.txt", "content": "x"}),
        ("read_file", {"path": "..\\escaped.txt"}),
        ("list_dir", {"path": str(outside)}),
    )
    for name, arguments in cases:
        result = executor.execute(name, arguments, remaining_s=5)
        assert "ERROR:" in result
    assert not outside.exists()

    assert "content must be a string" in executor.execute(
        "write_file", {"path": "a.txt"}, remaining_s=5
    )
    assert "path must be a non-empty string" in executor.execute("read_file", {}, remaining_s=5)
    assert "command must be a non-empty string" in executor.execute(
        "run_command", {"command": "  "}, remaining_s=5
    )
    assert "timeout must be an integer" in executor.execute(
        "run_command", {"command": "echo hi", "timeout": "1"}, remaining_s=5
    )
    assert "unknown tool" in executor.execute("delete_file", {}, remaining_s=5)
    assert executor.execute("list_dir", {"path": "."}, remaining_s=5) == "(empty)"


def test_truncate_keeps_head_and_tail() -> None:
    assert _truncate("abcdefghij", 20) == "abcdefghij"
    limited = _truncate("A" * 100, 60)
    assert limited.startswith("A" * 10) and limited.endswith("A" * 10)
    assert "chars truncated" in limited
    assert "chars truncated" in _truncate("abcdefghij", 8)


def test_step_limit_stops_the_loop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    responses = [
        assistant_turn(calls=[tool_call("list_dir", {"path": "."}, f"c{i}")]) for i in range(5)
    ]
    with FakeOpenAIServer(responses) as server:
        adapter = BuiltinAdapter(
            model="gpt-4o-mini",
            base_url=server.url,
            api_key_env="OPENAI_API_KEY",
            price_table=load_price_table(),
            sandbox=LocalSandbox(),
            max_steps=2,
        )
        result = adapter.run(tmp_path, "go", 60)
        count = len(server.requests)
    assert count == 3  # two tool rounds plus the round that hits the limit
    assert "[greenwash] step limit reached (2 tool rounds)" in result.transcript
    assert str(result.claim.status) == "UNKNOWN"


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ({"__status__": 500, "error": "boom"}, "chat_completions request failed"),
        ({"__raw__": "not json"}, "invalid JSON"),
        ({"__raw__": "[]"}, "non-object response"),
        ({"choices": "bad"}, "returned no choices"),
        ({"choices": [None]}, "choice is not an object"),
        ({"choices": [{"message": None}]}, "choice has no message"),
        (
            {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": "bad"}}]},
            "tool_calls is not an array",
        ),
    ],
)
def test_loop_reports_protocol_errors(
    response: dict[str, object], message: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    with FakeOpenAIServer([response]) as server:
        adapter = BuiltinAdapter(
            model="gpt-4o-mini",
            base_url=server.url,
            api_key_env="OPENAI_API_KEY",
            price_table=load_price_table(),
            sandbox=LocalSandbox(),
        )
        result = adapter.run(tmp_path, "go", 30)
    assert result.exit_code == 1
    assert message in result.transcript
    assert result.tokens_in == 0 and result.cost_usd == 0.0
    assert str(result.claim.status) == "UNKNOWN"


def test_malformed_tool_arguments_become_error_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    responses: list[dict[str, object]] = [
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "bad-json",
                                "type": "function",
                                "function": {"name": "read_file", "arguments": "not json"},
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        },
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": ["malformed"],
                    }
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
        assistant_turn(content="STATUS: FAILED\ncannot read", tokens_in=5, tokens_out=1),
    ]
    with FakeOpenAIServer(responses) as server:
        adapter = BuiltinAdapter(
            model="gpt-4o-mini",
            base_url=server.url,
            api_key_env="OPENAI_API_KEY",
            price_table=load_price_table(),
            sandbox=LocalSandbox(),
        )
        result = adapter.run(tmp_path, "go", 30)
    assert "ERROR: invalid tool arguments" in result.transcript
    assert "ERROR: malformed tool call" in result.transcript
    assert str(result.claim.status) == "FAILED"
    assert result.tokens_in == 16 and result.tokens_out == 4


def test_missing_api_key_is_reported_as_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AdapterUnavailableError, match="OPENAI_API_KEY"):
        resolve_adapter("builtin", model="gpt-4o-mini")
    table = load_price_table()
    adapter = BuiltinAdapter(
        model="gpt-4o-mini",
        base_url="http://127.0.0.1:1/v1",
        api_key_env="OPENAI_API_KEY",
        price_table=table,
        sandbox=LocalSandbox(),
    )
    assert adapter.available() is False
    with pytest.raises(AdapterUnavailableError, match="API key"):
        adapter.run(Path("."), "go", 5)


def test_custom_api_key_env_and_injected_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GW_KEY", "custom")
    with (
        FakeOpenAIServer([assistant_turn(content="STATUS: DONE")]) as server,
        httpx.Client() as client,
    ):
        adapter = BuiltinAdapter(
            model="gpt-4o-mini",
            base_url=server.url,
            api_key_env="GW_KEY",
            price_table=load_price_table(),
            sandbox=LocalSandbox(),
            client=client,
        )
        result = adapter.run(tmp_path, "go", 30)
    assert result.claim.certain is True
    assert server.requests[0].authorization == "Bearer custom"


def test_builtin_adapter_validates_configuration(tmp_path: Path) -> None:
    with pytest.raises(AdapterUnavailableError, match="requires --model"):
        BuiltinAdapter("", "http://x/v1", "K", load_price_table(), LocalSandbox())
    with pytest.raises(ValueError, match="max_steps"):
        BuiltinAdapter("m", "http://x/v1", "K", load_price_table(), LocalSandbox(), max_steps=0)


def test_deadline_exhaustion_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    responses = [
        assistant_turn(
            calls=[
                tool_call(
                    "run_command",
                    {"command": f'{sys.executable} -c "import time; time.sleep(1.5)"'},
                )
            ]
        )
    ]
    with FakeOpenAIServer(responses) as server:
        adapter = BuiltinAdapter(
            model="gpt-4o-mini",
            base_url=server.url,
            api_key_env="OPENAI_API_KEY",
            price_table=load_price_table(),
            sandbox=LocalSandbox(),
        )
        result = adapter.run(tmp_path, "go", 1)
    assert result.timed_out is True
    assert "time budget exhausted" in result.transcript
    assert result.exit_code == 1


def test_request_timeout_is_reported_as_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def timeout(*args: object, **kwargs: object) -> None:
        raise httpx.ReadTimeout("slow endpoint")

    monkeypatch.setattr(httpx.Client, "post", timeout)
    adapter = BuiltinAdapter(
        model="gpt-4o-mini",
        base_url="http://127.0.0.1:1/v1",
        api_key_env="OPENAI_API_KEY",
        price_table=load_price_table(),
        sandbox=LocalSandbox(),
    )
    result = adapter.run(tmp_path, "go", 30)
    assert result.timed_out is True and result.exit_code == 1
    assert "request timed out" in result.transcript


def test_builtin_agent_error_is_a_runtime_error() -> None:
    assert issubclass(BuiltinAgentError, RuntimeError)
