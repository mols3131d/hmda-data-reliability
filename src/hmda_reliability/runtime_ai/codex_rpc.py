"""로컬 Codex App Server의 기한 있는 stdio JSON-RPC 전송."""

from __future__ import annotations

import json
import os
import select
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

Json = dict[str, Any]
_MAX_FRAME_BYTES = 2 * 1024 * 1024


class ProtocolError(ValueError):
    """서버가 허용되지 않은 JSON-RPC 프레임을 보냈다."""


def _check_structure(container: dict[str, Any] | list[Any], depth: int = 0) -> None:
    # The interpreter's JSON nesting limit varies by build and thread stack.
    if depth >= 128:
        raise ProtocolError("Codex RPC message nesting exceeds limit")
    for value in container.values() if isinstance(container, dict) else container:
        if isinstance(value, (dict, list)):
            _check_structure(value, depth + 1)


class RpcRejected(Exception):
    def __init__(self, code: int):
        super().__init__("Codex RPC rejected")
        self.code = code


class AppServer:
    """직렬 요청 하나와 관련된 이벤트를 한 파이프에서 읽는다."""

    def __init__(
        self, command: list[str], cwd: Path, clock: Callable[[], float] = time.monotonic
    ):
        self.clock = clock
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            env={
                k: os.environ[k]
                for k in ("HOME", "CODEX_HOME", "LANG", "PATH")
                if k in os.environ
            },
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        assert self.process.stdin is not None and self.process.stdout is not None
        self.input = self.process.stdin
        self.output = self.process.stdout
        os.set_blocking(self.input.fileno(), False)
        self.buffer = bytearray()
        self.next_id = 1

    def _wait(self, deadline: float, *, writing: bool = False) -> None:
        remaining = deadline - self.clock()
        if remaining <= 0:
            raise TimeoutError
        readers, writers, _ = select.select(
            [] if writing else [self.output],
            [self.input] if writing else [],
            [],
            remaining,
        )
        if not readers and not writers:
            raise TimeoutError

    def send(self, message: Json, deadline: float) -> None:
        data = memoryview(
            json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode()
            + b"\n"
        )
        while data:
            self._wait(deadline, writing=True)
            data = data[os.write(self.input.fileno(), data) :]

    def read(self, deadline: float) -> Json:
        while True:
            if self.clock() >= deadline:
                raise TimeoutError
            boundary = self.buffer.find(b"\n")
            frame_size = len(self.buffer) if boundary < 0 else boundary
            if frame_size > _MAX_FRAME_BYTES:
                raise ProtocolError("Codex RPC frame exceeds limit")
            if boundary >= 0:
                line = bytes(self.buffer[:boundary])
                del self.buffer[: boundary + 1]
                try:
                    message = json.loads(line)
                except (ValueError, RecursionError) as error:
                    raise ProtocolError("invalid Codex JSON") from error
                if not isinstance(message, dict):
                    raise ProtocolError("invalid Codex RPC message")
                _check_structure(message)
                return message
            self._wait(deadline)
            chunk = os.read(self.output.fileno(), 16_384)
            if not chunk:
                raise EOFError
            self.buffer.extend(chunk)

    def rpc(
        self,
        method: str,
        params: Json,
        deadline: float,
        *,
        event: Callable[[Json], None] | None = None,
    ) -> Json:
        request_id = self.next_id
        self.next_id += 1
        self.send({"method": method, "id": request_id, "params": params}, deadline)
        while True:
            message = self.read(deadline)
            if "method" in message:
                if "id" in message:
                    raise ValueError("unexpected Codex server request")
                if event:
                    event(message)
            elif message.get("id") == request_id:
                if "error" in message:
                    raise RpcRejected(message["error"]["code"])
                result = message.get("result")
                if not isinstance(result, dict):
                    raise ProtocolError("invalid Codex RPC result")
                return result

    def close(self) -> None:
        self.input.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.output.close()
