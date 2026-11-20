"""Loopback-only fake OpenAI-compatible chat-completions server for tests."""

from __future__ import annotations

import json
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import cast


@dataclass(frozen=True)
class FakeRequest:
    """One captured chat-completions request."""

    path: str
    payload: dict[str, object]
    authorization: str


class FakeOpenAIServer:
    """Serves scripted responses over HTTP on 127.0.0.1 with an ephemeral port."""

    def __init__(self, responses: Sequence[dict[str, object]]) -> None:
        self.responses: list[dict[str, object]] = list(responses)
        self.requests: list[FakeRequest] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length).decode("utf-8")
                    payload = json.loads(raw)
                    if not isinstance(payload, dict):
                        raise ValueError("payload is not an object")
                except (ValueError, UnicodeDecodeError):
                    self.send_error(400, "invalid JSON")
                    return
                outer.requests.append(
                    FakeRequest(
                        path=self.path,
                        payload=cast(dict[str, object], payload),
                        authorization=self.headers.get("Authorization", ""),
                    )
                )
                index = len(outer.requests) - 1
                response = outer.responses[min(index, len(outer.responses) - 1)]
                status_raw: object = response.get("__status__", 200)
                status = (
                    status_raw
                    if isinstance(status_raw, int) and not isinstance(status_raw, bool)
                    else 200
                )
                raw_override: object = response.get("__raw__")
                body: bytes
                if isinstance(raw_override, str):
                    body = raw_override.encode("utf-8")
                else:
                    body = json.dumps(
                        {
                            key: value
                            for key, value in response.items()
                            if key not in {"__status__", "__raw__"}
                        }
                    ).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    @property
    def url(self) -> str:
        host_raw, port = self._httpd.server_address[:2]
        host = host_raw if isinstance(host_raw, str) else "127.0.0.1"
        return f"http://{host}:{port}/v1"

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)

    def __enter__(self) -> FakeOpenAIServer:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def tool_call(
    name: str, arguments: dict[str, object], call_id: str = "call-1"
) -> dict[str, object]:
    """Build one assistant tool-call entry."""
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments)},
    }


def assistant_turn(
    *,
    content: str = "",
    calls: Sequence[dict[str, object]] = (),
    tokens_in: int = 0,
    tokens_out: int = 0,
) -> dict[str, object]:
    """Build one chat-completions response with usage counters."""
    message: dict[str, object] = {"role": "assistant", "content": content}
    if calls:
        message["tool_calls"] = list(calls)
    return {
        "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
    }
