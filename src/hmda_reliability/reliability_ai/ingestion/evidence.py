"""고정된 시작 입력부터 종료 게시까지 순서와 digest를 검증하는 로컬 조사 기록."""

from __future__ import annotations

import json
import math
import re
import uuid
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from hmda_reliability.reliability_ai.prompt import canonical_json_bytes
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceDeadlineError,
    InvocationEvidenceExistsError,
    InvocationEvidenceStoreError,
    ReplayEvidenceError,
    evidence_digest,
    read_evidence_ref,
    write_evidence_ref,
    write_review_json,
)

VERSION = "ingestion-1"
MAX_BYTES = 4 * 1024 * 1024
_FAILURES = {"workflow_budget_exhausted", "evidence_write_failed"}


def directory(root: Path, investigation_id: str) -> Path:
    if not re.fullmatch(r"ing-[0-9a-f]{32}", investigation_id):
        raise ValueError("invalid ingestion investigation ID")
    return Path(root) / "ingestion" / investigation_id


def _seal(data: dict[str, Any]) -> dict[str, Any]:
    return {**data, "digest": evidence_digest(canonical_json_bytes(data))}


def _verify(raw: bytes, investigation_id: str) -> dict[str, Any]:
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("format"), str):
            raise ReplayEvidenceError("corrupt_evidence")
        if data["format"] != VERSION:
            raise ReplayEvidenceError("unsupported_version")
        digest = data.pop("digest")
        if (
            data["investigation_id"] != investigation_id
            or evidence_digest(canonical_json_bytes(data)) != digest
        ):
            raise ReplayEvidenceError("corrupt_evidence")
        return data
    except ReplayEvidenceError:
        raise
    except (TypeError, ValueError, KeyError, RecursionError):
        raise ReplayEvidenceError("corrupt_evidence") from None


class IngestionJournal:
    def __init__(self, root: Path) -> None:
        self.id = "ing-" + uuid.uuid4().hex
        self.path = directory(root, self.id)
        self.events: list[dict[str, str]] = []
        self.failed_event: dict[str, Any] | None = None

    def add(self, kind: str, payload: dict[str, Any]) -> None:
        index = len(self.events)
        event = {
            "format": VERSION,
            "investigation_id": self.id,
            "index": index,
            "kind": kind,
            "data": payload,
        }
        try:
            ref = write_evidence_ref(
                self.path,
                f"event-{index}.json",
                _seal(event),
                max_record_bytes=MAX_BYTES,
            )
        except InvocationEvidenceExistsError:
            raise
        except (InvocationEvidenceStoreError, OSError):
            self.failed_event = {"kind": kind, "index": index}
            raise
        self.events.append(ref)

    def _document(self, result: dict[str, Any]) -> dict[str, Any]:
        return {
            "format": VERSION,
            "investigation_id": self.id,
            "events": self.events,
            "result": result,
        }

    def retain_failure(self, result: dict[str, Any]) -> dict[str, Any]:
        if self.failed_event is not None:
            with suppress(InvocationEvidenceStoreError, OSError):
                write_review_json(
                    self.path / "failure.json",
                    _seal(
                        {**self._document(result), "failed_event": self.failed_event}
                    ),
                    max_record_bytes=MAX_BYTES,
                )
        return result

    def publish(
        self,
        result: dict[str, Any],
        clock: Callable[[], float],
        deadline: float,
        *,
        recorded_publication: str | None = None,
    ) -> dict[str, Any]:
        reason = recorded_publication
        if reason is None:
            try:
                write_review_json(
                    self.path / "result.json",
                    _seal(self._document(result)),
                    max_record_bytes=MAX_BYTES,
                    deadline=deadline if result["termination"] == "completed" else None,
                    clock=clock,
                )
                return result
            except InvocationEvidenceExistsError:
                raise
            except (InvocationEvidenceStoreError, OSError) as exc:
                reason = (
                    "workflow_budget_exhausted"
                    if isinstance(exc, InvocationEvidenceDeadlineError)
                    else "evidence_write_failed"
                )
        if reason not in _FAILURES:
            raise ReplayEvidenceError("corrupt_evidence")
        result = {
            **result,
            "termination": reason,
            "next_action": "request_confirmation",
            "advisory": None,
        }
        write_review_json(
            self.path / "failure.json",
            _seal({**self._document(result), "publication": reason}),
            max_record_bytes=MAX_BYTES,
        )
        return result


def _event(raw: bytes, investigation_id: str, i: int) -> dict[str, Any]:
    event = _verify(raw, investigation_id)
    if (
        event["index"] != i
        or not isinstance(event["kind"], str)
        or not isinstance(event["data"], dict)
    ):
        raise ReplayEvidenceError("corrupt_evidence")
    return {"kind": event["kind"], "data": event["data"]}


def validate_previous(
    root: Path, investigation_id: str
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """완료 조사 또는 실제 start를 게시한 중단 조사만 후속 요청에 연결한다."""
    path = directory(root, investigation_id)
    if (path / "result.json").exists() or (path / "failure.json").exists():
        return load_record(root, investigation_id)
    try:
        start = _event((path / "event-0.json").read_bytes(), investigation_id, 0)
        if start["kind"] != "start" or start["data"]["mode"] not in {
            "prepare",
            "review_run",
        }:
            raise ReplayEvidenceError("corrupt_evidence")
        return None, [start]
    except FileNotFoundError:
        raise ReplayEvidenceError("missing_evidence") from None
    except (KeyError, TypeError):
        raise ReplayEvidenceError("corrupt_evidence") from None


def load_record(
    root: Path, investigation_id: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = directory(root, investigation_id)
    try:
        final = path / "result.json"
        failure = path / "failure.json"
        if final.exists() and failure.exists():
            raise ReplayEvidenceError("corrupt_evidence")
        obj = _verify(
            (final if final.is_file() else failure).read_bytes(), investigation_id
        )
        if (
            not isinstance(obj["events"], list)
            or not isinstance(obj["result"], dict)
            or obj["result"]["investigation_id"] != investigation_id
        ):
            raise ReplayEvidenceError("corrupt_evidence")
        events = [
            _event(read_evidence_ref(path, ref, f"event-{i}.json"), investigation_id, i)
            for i, ref in enumerate(obj["events"])
        ]
        last_time = 0.0
        for event in events:
            if event["kind"].endswith("_time"):
                seconds = event["data"]["seconds"]
                if (
                    type(seconds) not in (int, float)
                    or not math.isfinite(seconds)
                    or seconds < last_time
                ):
                    raise ReplayEvidenceError("corrupt_evidence")
                last_time = seconds
        return obj, events
    except FileNotFoundError:
        raise ReplayEvidenceError("missing_evidence") from None
    except ReplayEvidenceError:
        raise
    except (KeyError, TypeError, ValueError, IndexError, OSError, RecursionError):
        raise ReplayEvidenceError("corrupt_evidence") from None
