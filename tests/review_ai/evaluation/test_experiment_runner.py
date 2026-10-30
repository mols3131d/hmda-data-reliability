import sys
import time

import pytest

from hmda_reliability.review_ai.evaluation.experiment import main, run_isolated

pytestmark = pytest.mark.component


def test_disabled_experiment_never_requires_sdk_or_credentials(capsys):
    assert main(env={}, argv=[]) == 0
    assert "disabled" in capsys.readouterr().out


def test_missing_credentials_are_rejected_without_printing_values(capsys):
    assert (
        main(
            env={
                "HMDA_LANGFUSE_ENABLED": "true",
                "LANGFUSE_PUBLIC_KEY": "PRIVATE_SECRET",
            },
            argv=[],
        )
        == 2
    )
    assert "PRIVATE_SECRET" not in capsys.readouterr().err


def test_hanging_external_sdk_is_killed_within_io_budget():
    started = time.monotonic()
    result = run_isolated(
        {"langfuse": {"io_timeout_seconds": 0.2}},
        {},
        command=[sys.executable, "-c", "import time; time.sleep(30)"],
    )
    assert result["failure_code"] == "external_io_timeout"
    assert time.monotonic() - started < 3


def test_core_time_is_not_charged_to_the_external_io_budget():
    script = """import json,time
print(json.dumps({'kind':'phase','phase':'core'}),flush=True)
time.sleep(.4)
print(json.dumps({'kind':'core_result','result':{'status':'completed','workflow_id':'retained'}}),flush=True)
print(json.dumps({'kind':'phase','phase':'remote'}),flush=True)
print(json.dumps({'kind':'receipt','receipt':{'status':'submitted_unverified'}}),flush=True)
"""
    result = run_isolated(
        {"langfuse": {"io_timeout_seconds": 0.2}},
        {},
        command=[sys.executable, "-c", script],
    )
    assert result["status"] == "submitted_unverified"
    assert result["core_results"] == [
        {"status": "completed", "workflow_id": "retained"}
    ]


def test_external_timeout_keeps_already_reported_core_result():
    script = """import json,time
print(json.dumps({'kind':'core_result','result':{'status':'completed','workflow_id':'kept'}}),flush=True)
time.sleep(30)
"""
    result = run_isolated(
        {"langfuse": {"io_timeout_seconds": 0.2}},
        {},
        command=[sys.executable, "-c", script],
    )
    assert result["failure_code"] == "external_io_timeout"
    assert result["core_results"][0]["workflow_id"] == "kept"


def test_stalled_worker_stdin_is_also_bounded_by_io_budget():
    started = time.monotonic()
    result = run_isolated(
        {"langfuse": {"io_timeout_seconds": 0.1}, "padding": "x" * 500_000},
        {},
        command=[sys.executable, "-c", "import time; time.sleep(2)"],
    )
    assert result["failure_code"] == "external_io_timeout"
    assert time.monotonic() - started < 1


def test_real_worker_runs_all_three_cases_without_provider_network(tmp_path):
    import json
    from pathlib import Path

    from hmda_reliability.review_ai.evaluation import experiment
    from tests.review_ai.test_live_harness import _live_environment

    script = """import os
from tests.review_ai.evaluation.test_native_sdk import FakeClient
from tests.review_ai.test_live_harness import StagedTextProvider
from hmda_reliability.review_ai.staged import service
from hmda_reliability.review_ai.evaluation import native_sdk
from hmda_reliability.review_ai.evaluation.experiment_worker import worker
provider=StagedTextProvider()
service.OpenAICompatibleAdapter=lambda *a,**k: provider
native_sdk.make_client=lambda settings: FakeClient()
os._exit(worker())
"""
    environment = _live_environment(tmp_path)
    cases = json.loads(Path(experiment.__file__).with_name("cases.json").read_text())
    request = dict(
        action="run",
        cases=cases,
        run_name="test-native-three",
        langfuse=dict(
            base_url="http://unused.invalid",
            public_key="pk",
            secret_key="PRIVATE_SECRET",
            io_timeout_seconds=5,
            dataset_name="test",
        ),
    )
    result = run_isolated(request, environment, command=[sys.executable, "-c", script])
    assert result["status"] == "submitted_unverified"
    assert len(result["bindings"]) == len(result["core_results"]) == 3
    assert all(case["status"] == "completed" for case in result["core_results"])
    assert "PRIVATE_SECRET" not in json.dumps(result)
    workflows = list(
        (tmp_path / "artifacts" / "agentic-review" / "staged").glob("*/workflow.json")
    )
    assert len(workflows) == 3


def test_worker_exception_body_cannot_escape_to_receipt():
    import json

    script = """import os
from hmda_reliability.review_ai.evaluation import native_sdk
from hmda_reliability.review_ai.evaluation.experiment_worker import worker
def fail(_settings):
    raise RuntimeError('PRIVATE_SECRET /home/private-user/work/private-project')
native_sdk.make_client=fail
os._exit(worker())
"""
    result = run_isolated(
        dict(action="check", langfuse=dict(io_timeout_seconds=5)),
        {},
        command=[sys.executable, "-c", script],
    )
    assert result["failure_code"] == "native_experiment_failed"
    assert "PRIVATE_SECRET" not in json.dumps(result)
    assert "/home/private-user" not in json.dumps(result)


def test_check_needs_no_ai_provider_configuration(tmp_path, monkeypatch, capsys):
    import json

    from hmda_reliability.review_ai.evaluation import experiment

    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(dict(bindings=[{}])))
    monkeypatch.setattr(
        experiment,
        "run_isolated",
        lambda *a: dict(status="checked", annotations=[dict(status="complete")]),
    )
    assert (
        main(
            env=dict(
                HMDA_LANGFUSE_ENABLED="true",
                LANGFUSE_BASE_URL="http://unused.invalid",
                LANGFUSE_PUBLIC_KEY="pk",
                LANGFUSE_SECRET_KEY="sk",
            ),
            argv=["--check", str(receipt), "--reviewer-id", "human"],
        )
        == 0
    )
    assert "checked" in capsys.readouterr().out
