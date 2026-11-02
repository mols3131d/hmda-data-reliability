"""최초 등록은 native 모듈 참조와 독립 oracle을 가진 합성 Dataset을 만든다."""

from types import SimpleNamespace

import pytest

from hmda_reliability.review_ai.evaluation import setup

pytestmark = pytest.mark.component


class SeedClient:
    def __init__(self):
        self.prompts = []
        self.datasets = []
        self.items = []

    def create_prompt(self, **kwargs):
        self.prompts.append(kwargs)
        return SimpleNamespace(name=kwargs["name"], version=11)

    def create_dataset(self, **kwargs):
        self.datasets.append(kwargs)

    def create_dataset_item(self, **kwargs):
        self.items.append(kwargs)


def test_setup_registers_korean_modules_native_composition_and_reviewer_oracles(
    monkeypatch,
):
    client = SeedClient()
    monkeypatch.setattr(setup, "get_client", lambda: client)

    assert (
        setup.main(argv=["--dataset", "first-setup", "--model", "model-under-test"])
        == 0
    )

    assert len(client.datasets) == 1 and client.datasets[0]["name"] == "first-setup"
    registered = {prompt["name"]: prompt for prompt in client.prompts}
    language = registered["hmda-review-ai/policies/language"]
    assert language["type"] == "text" and "한국어" in language["prompt"]
    for stage_id in ("evidence_review", "draft_critique", "synthesis"):
        prompt = registered[f"hmda-review-ai/{stage_id}"]
        assert prompt["type"] == "chat"
        assert prompt["labels"] == ["production"]
        assert prompt["prompt"][1] == {"type": "placeholder", "name": "history"}
        assert prompt["prompt"][0]["role"] == "system"
        assert (
            "@@@langfusePrompt:name=hmda-review-ai/policies/language|version=11@@@"
            in prompt["prompt"][0]["content"]
        )
        assert prompt["prompt"][-1] == {
            "role": "system",
            "content": (
                f"@@@langfusePrompt:name=hmda-review-ai/staged/{stage_id}|version=11@@@"
            ),
        }
    assert registered["hmda-review-ai/evidence_review"]["config"]["model"] == (
        "model-under-test"
    )
    assert len(client.items) == 3
    assert client.items[0]["expected_output"]["numeric"]["delta_percentage_points"] == (
        "20"
    )
    assert all("oracle" not in item["input"] for item in client.items)
    assert all(item["metadata"]["synthetic"] for item in client.items)


def test_setup_failure_reports_no_exception_body_or_credentials(monkeypatch, capsys):
    def unavailable():
        raise RuntimeError("PRIVATE_SECRET /home/private-user/project")

    monkeypatch.setattr(setup, "get_client", unavailable)
    assert setup.main(argv=[]) == 2
    captured = capsys.readouterr()
    assert "PRIVATE_SECRET" not in captured.out + captured.err
    assert "/home/private-user" not in captured.out + captured.err
