"""조사 결과의 불변 참조, 저장 경계와 오프라인 읽기."""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path
from typing import Any

from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.prompt import canonical_json_bytes
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceDeadlineError,
    InvocationEvidenceExistsError,
    InvocationEvidenceStoreError,
    InvocationResponseStore,
    ReplayEvidenceError,
    write_evidence_ref,
    write_review_json,
)
from hmda_reliability.reliability_ai.store import (
    evidence_digest as _digest,
)
from hmda_reliability.reliability_ai.store import (
    evidence_file_ref as _file_ref,
)
from hmda_reliability.reliability_ai.store import (
    read_evidence_ref as _read_ref,
)

_FORMAT = 2
_GRAPH = "incident-1"
_POLICY = "bounded-tools-1"


class InvestigationJournal:
    def __init__(self, artifact_root: Path, invocation_id: str) -> None:
        store = InvocationResponseStore(artifact_root)
        self.root = store.path_for(invocation_id).parent.parent
        self.invocation_id = invocation_id
        self._tool_refs: list[dict[str, str]] = []
        self._ticks: list[float] = []
        self._publication_expired = False
        self._publication_clock_reads = 0
        self._failed_write: dict[str, str | int | None] | None = None

    def clock(self, source: Callable[[], float]) -> Callable[[], float]:
        origin: float | None = None

        def sample() -> float:
            nonlocal origin
            now = source()
            if origin is None:
                origin = now
            self._ticks.append(now - origin)
            return now

        return sample

    def observe_tool(self, turn: int, record: ToolCallRecord, tool_output: str) -> None:
        path = (
            self.root
            / "observations"
            / f"{self.invocation_id}-{len(self._tool_refs)}.json"
        )
        serialization_failed = False
        try:
            data = record.model_dump(mode="json")
        except (ValueError, RecursionError):
            serialization_failed = True
            data = {
                "call_id": record.call_id,
                "tool_name": record.tool_name,
                "arguments": {},
                "result": {
                    "error": "unserializable_tool_record",
                    "raw_evidence": "investigation turns",
                },
                "latency_ms": record.latency_ms,
                "status": "error",
            }
        # The exact tool message contributes to the next input digest.
        if json.dumps(data["result"], ensure_ascii=False) == tool_output:
            del data["result"]
        observation = {"turn": turn, "record": data, "output": tool_output}
        ref = write_evidence_ref(
            path.parent, path.name, observation, max_record_bytes=4 * 1024 * 1024
        )
        if serialization_failed:
            ref["serialization"] = "failed"
        self._tool_refs.append(ref)

    def failed_write(self, kind: str, turn: int, tool_id: str | None = None) -> None:
        self._failed_write = {"kind": kind, "turn": turn, "tool_id": tool_id}

    def publish(
        self,
        manifest_path: Path,
        payload: dict[str, Any],
        *,
        max_record_bytes: int,
        deadline: float | None,
        clock: Callable[[], float],
        writer: Callable[..., Path] = write_review_json,
    ) -> InvestigationResult:
        result = payload["result"].copy()
        turns = [turn.copy() for turn in result["turns"]]
        instructions: list[dict[str, Any]] = []
        content_refs: dict[bytes, list[Any]] = {}
        observation_index = 0
        for index, turn in enumerate(turns):
            if turn["role"] == "assistant" and turn["turn"] < len(
                result["response_paths"]
            ):
                response = Path(result["response_paths"][turn["turn"]])
                turn["response"] = _file_ref(response)
                original = result["turns"][index]
                if original["tool_calls"]:
                    key = canonical_json_bytes(
                        {
                            "role": "assistant",
                            "content": original["content"],
                            "tool_calls": original["tool_calls"],
                        }
                    )
                    content_refs[key] = ["turn", index]
                turn.pop("content")
                if turn.pop("tool_calls_path", None):
                    turn["calls"] = _file_ref(Path(original["tool_calls_path"]))
                    turn.pop("raw_tool_calls")
                    turn.pop("tool_calls")
            elif turn["role"] == "tool":
                if observation_index < len(self._tool_refs):
                    key = canonical_json_bytes(
                        {
                            "role": "tool",
                            "tool_call_id": turn["tool_call_id"],
                            "content": turn.pop("content"),
                        }
                    )
                    content_refs[key] = ["turn", index]
                    turn["observation"] = observation_index
                    observation_index += 1
        canonical_message = canonical_json_bytes(payload["canonical_input"]).decode()
        message_dictionary: dict[bytes, list[Any]] = {}
        requests = []
        for messages in payload["compiled_messages"]:
            refs = []
            for message in messages:
                key = canonical_json_bytes(message)
                ref = content_refs.get(key) or message_dictionary.get(key)
                if ref is None:
                    entry = dict(message)
                    if entry.get("content") == canonical_message:
                        del entry["content"]
                        entry["canonical_content"] = True
                    ref = ["message", len(instructions)]
                    instructions.append(entry)
                    message_dictionary[key] = ref
                refs.append(ref)
            requests.append(refs)
        result["turns"] = turns
        result.pop("response_paths")
        result.pop("manifest_path")
        result["tool_calls"] = result["tool_calls"][len(self._tool_refs) :]
        document = {
            **{
                k: v
                for k, v in payload.items()
                if k not in {"result", "compiled_messages", "tool_definitions"}
            },
            # Codex embeds the schema as text. Preserve insertion order of nested
            # parameters even though the surrounding manifest uses sorted JSON.
            "tool_definitions_json": json.dumps(
                payload["tool_definitions"], ensure_ascii=False, separators=(",", ":")
            ),
            "record_version": _FORMAT,
            "graph_version": _GRAPH,
            "policy_version": _POLICY,
            "message_dictionary": instructions,
            "requests": requests,
            "observations": self._tool_refs,
            "relative_clock": list(self._ticks),
            "publication": "expired" if self._publication_expired else "written",
            "publication_clock_reads": self._publication_clock_reads,
            "failed_write": self._failed_write,
            "result": result,
        }

        def sealed() -> dict[str, Any]:
            return {
                **document,
                "record_digest": _digest(canonical_json_bytes(document)),
            }

        try:
            # Hydration and digest checks precede the budget-bound final publication.
            restored, _ = _hydrate(document, manifest_path)
            clock_count = len(self._ticks)
            writer(
                manifest_path,
                sealed(),
                max_record_bytes=max_record_bytes,
                deadline=deadline,
                clock=clock,
            )
        except InvocationEvidenceDeadlineError:
            self._publication_expired = True
            self._publication_clock_reads = len(self._ticks) - clock_count
            raise
        except InvocationEvidenceExistsError:
            raise
        except (OSError, InvocationEvidenceStoreError, ReplayEvidenceError):
            # Preserve the failed boundary in a separate create-only file.
            document["publication"] = "failed"
            failure = self.root / "failures" / manifest_path.name
            with suppress(InvocationEvidenceStoreError):
                write_review_json(failure, sealed(), max_record_bytes=max_record_bytes)
            raise
        return restored


def _hydrate(
    document: dict[str, Any],
    path: Path,
) -> tuple[InvestigationResult, list[list[dict[str, Any]]]]:
    raw = dict(document["result"])
    invocation_id = raw["invocation_id"]
    if path.stem != invocation_id:
        raise ReplayEvidenceError("corrupt_evidence")
    root = path.parent.parent
    observation_data: list[tuple[dict[str, Any], str, int]] = []
    for i, ref in enumerate(document["observations"]):
        data = json.loads(
            _read_ref(root / "observations", ref, f"{invocation_id}-{i}.json")
        )
        record = data["record"]
        output = data["output"]
        if "result" not in record:
            record["result"] = json.loads(output)
        observation_data.append((record, output, data["turn"]))
    turns = []
    messages = {}
    response_paths = []
    for i, saved_turn in enumerate(raw["turns"]):
        turn = saved_turn.copy()
        n = turn["turn"]
        if "response" in turn:
            ref = turn.pop("response")
            turn["content"] = _read_ref(
                root / "responses", ref, f"{invocation_id}-{n}.txt"
            ).decode()
            response_paths.append(root / "responses" / ref["name"])
        if "calls" in turn:
            ref = turn.pop("calls")
            calls = json.loads(
                _read_ref(
                    root / "responses", ref, f"{invocation_id}-{n}-tool-calls.json"
                )
            )
            turn["tool_calls"] = calls["tool_calls"]
            turn["raw_tool_calls"] = calls["raw_tool_calls"]
            turn["tool_calls_path"] = root / "responses" / ref["name"]
        if turn.get("role") == "assistant" and turn.get("tool_calls"):
            messages[i] = {
                "role": "assistant",
                "content": turn["content"],
                "tool_calls": turn["tool_calls"],
            }
        if "observation" in turn:
            record, output, observed_turn = observation_data[turn.pop("observation")]
            if turn["tool_call_id"] != record["call_id"] or n != observed_turn:
                raise ReplayEvidenceError("corrupt_evidence")
            turn["content"] = output
            messages[i] = {
                "role": "tool",
                "tool_call_id": turn["tool_call_id"],
                "content": output,
            }
        turns.append(turn)
    raw.update(
        turns=turns,
        response_paths=response_paths,
        manifest_path=path,
        tool_calls=[row[0] for row in observation_data] + raw["tool_calls"],
    )
    result = InvestigationResult.model_validate(raw)
    dictionary = []
    for saved in document["message_dictionary"]:
        message = saved.copy()
        if message.pop("canonical_content", False):
            message["content"] = canonical_json_bytes(
                document["canonical_input"]
            ).decode()
        dictionary.append(message)
    requests = []
    for index, refs in enumerate(document["requests"]):
        batch = []
        for kind, n in refs:
            if kind not in {"turn", "message"} or not isinstance(n, int) or n < 0:
                raise ReplayEvidenceError("corrupt_evidence")
            batch.append(messages[n] if kind == "turn" else dictionary[n])
        if document["compiled_message_digests"][index] != _digest(
            canonical_json_bytes(batch)
        ):
            raise ReplayEvidenceError("corrupt_evidence")
        requests.append(batch)
    return result, requests


def read_record(
    path: Path,
) -> tuple[dict[str, Any], InvestigationResult, list[list[dict[str, Any]]]]:
    try:
        document = json.loads(path.read_bytes())
        if "record_version" not in document:
            return document, InvestigationResult.model_validate(document["result"]), []
        if (
            document["record_version"],
            document["graph_version"],
            document["policy_version"],
        ) != (_FORMAT, _GRAPH, _POLICY):
            raise ReplayEvidenceError("incompatible_version")
        digest = document.pop("record_digest")
        if digest != _digest(canonical_json_bytes(document)):
            raise ReplayEvidenceError("corrupt_evidence")
        result, requests = _hydrate(document, path)
    except FileNotFoundError:
        raise ReplayEvidenceError("missing_evidence") from None
    except ReplayEvidenceError:
        raise
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        UnicodeError,
        RecursionError,
        OSError,
    ) as exc:
        raise ReplayEvidenceError("corrupt_evidence") from exc
    return document, result, requests


def load_investigation(path: Path) -> InvestigationResult:
    """구형 인라인 기록 또는 검증한 참조에서 조사 결과를 복원한다."""
    document, result, _ = read_record(path)
    if document.get("publication") == "failed":
        return result.model_copy(
            update={
                "status": "error",
                "failure_code": "manifest_persistence_failed",
                "facts": {},
                "findings": (),
                "hypotheses": (),
                "uncertainties": (),
                "manifest_path": None,
            }
        )
    return result
