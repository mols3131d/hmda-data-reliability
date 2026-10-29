"""Current raw response and create-only JSON artifact storage tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from hmda_reliability.review_ai import store as store_module

pytestmark = pytest.mark.component


def test_current_json_artifact_has_exactly_one_concurrent_writer(
    tmp_path: Path,
) -> None:
    path = tmp_path / "workflow.json"
    payload: dict[str, object] = {"stage": "종합", "facts": {"delta": 0.2}}

    def write_once() -> str:
        try:
            store_module.write_review_json(path, payload, max_record_bytes=1024)
        except store_module.InvocationEvidenceExistsError:
            return "collision"
        return "created"

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: write_once(), range(2)))

    assert sorted(results) == ["collision", "created"]
    assert path.read_bytes() == '{"facts":{"delta":0.2},"stage":"종합"}\n'.encode()
    assert path.stat().st_mode & 0o077 == 0


def test_current_json_artifact_rejects_oversize_before_creating(tmp_path: Path) -> None:
    path = tmp_path / "output.json"
    with pytest.raises(store_module.InvocationEvidenceSizeError):
        store_module.write_review_json(path, {"text": "한😀"}, max_record_bytes=8)
    assert not path.exists()


def test_current_json_artifact_rolls_back_directory_fsync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "workflow.json"

    def fail(directory: Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(store_module, "_fsync_directory", fail)
    with pytest.raises(store_module.InvocationEvidenceWriteError):
        store_module.write_review_json(
            path, {"status": "completed"}, max_record_bytes=1024
        )
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("content", ["", " \n ", '{"응답":"잘린 JSON 😀"'])
def test_response_store_preserves_exact_utf8_body_separately(
    tmp_path: Path, content: str
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    path = store.write("inv-response", content, max_response_bytes=1024)

    assert path == tmp_path / "agentic-review" / "responses" / "inv-response.txt"
    assert path == store.path_for("inv-response")
    assert path.read_bytes() == content.encode("utf-8")
    assert path.stat().st_mode & 0o077 == 0
    assert not (tmp_path / "agentic-review" / "invocations").exists()


def test_response_store_rejects_duplicate_identity_without_replacing_body(
    tmp_path: Path,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)
    path = store.write("inv-response", "first response", max_response_bytes=1024)

    with pytest.raises(store_module.InvocationEvidenceExistsError):
        store.write("inv-response", "replacement response", max_response_bytes=1024)

    assert path.read_text(encoding="utf-8") == "first response"


def test_response_store_counts_utf8_bytes_and_accepts_exact_limit(
    tmp_path: Path,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)
    content = "한😀"

    path = store.write("inv-exact", content, max_response_bytes=7)
    with pytest.raises(store_module.InvocationEvidenceSizeError):
        store.write("inv-oversized", content, max_response_bytes=6)

    assert path.read_bytes() == b"\xed\x95\x9c\xf0\x9f\x98\x80"
    assert not store.path_for("inv-oversized").exists()


@pytest.mark.parametrize("invocation_id", ["../escape", "/absolute", "inv/response"])
def test_response_store_rejects_unsafe_identity(
    tmp_path: Path, invocation_id: str
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    with pytest.raises(ValueError, match="unsafe invocation identity"):
        store.write(invocation_id, "body", max_response_bytes=1024)

    assert not (tmp_path / "agentic-review").exists()


def test_response_store_rolls_back_body_when_directory_fsync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = store_module.InvocationResponseStore(tmp_path)

    def failing_fsync_directory(directory: Path) -> None:
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(store_module, "_fsync_directory", failing_fsync_directory)

    with pytest.raises(store_module.InvocationEvidenceWriteError):
        store.write("inv-response", "body", max_response_bytes=1024)

    assert not store.path_for("inv-response").exists()
    assert list(store.path_for("inv-response").parent.iterdir()) == []
