---
type: report
title: Detector Implementation And Validation
description: PR 252의 마지막 detector 수정에 대한 test-first 실패·성공, 영향 검증과 독립 리뷰 근거를 기록합니다.
tags:
  - reliability
  - testing
---

# Detector Implementation And Validation

## Active Scope

[규칙별 결정](17-report-detector-contract-cases.md)과 [Change](../../openspec/changes/reliability-detection-positive-degradation/)를 따른다. Source 시작점은 `61900aad`이며 기존 네 단위는 보존한다. 비결정적 품질 평가는 제외한다. 기존 5/30 loop 이후 여섯 번째 구현 loop를 완료했다.

## Test-First Evidence

Production 수정 전 새 test를 working tree에 추가하고 아래 명령을 실행했다.

```bash
.venv/bin/python -m pytest tests/reliability/test_basic_incident_detection.py -q --tb=short
```

결과는 **13 failed / 14 passed**, 0.37s다. 모든 실패는 실제 반환 incident 목록의 assertion에서 발생했다. 무변화의 volume/null 두 오경보, 한 규칙만 악화됐을 때 다른 경보 혼입, zero-row baseline의 null 오경보, schema/freshness 결과의 오경보 혼입 및 column별 독립성을 검출했다. Positive threshold equality와 실제 양의 악화는 이미 통과했다.

Tach plugin은 새 테스트가 impact selection에서 빠질 수 있다고 경고했으나 이 실행에는 `--tach`를 사용하지 않았고 27개를 모두 실행했다. 전체 검증도 이 필터에 의존하지 않는다.

## Current Checkpoint

Volume/null 두 분기에 `<= 0` 제외 조건을 추가했다. 양수 threshold 비교·schema·freshness의 실행 로직은 유지했고 설명과 canonical Spec을 일치시켰다. Threshold 설정 형태와 공개 API는 그대로다.

Focused GREEN 명령은 위 module에 `tests/reliability/test_quality_gate.py`를 함께 지정했으며 **39 passed**, 0.30s다. 새 회귀 18개와 기존 기본 탐지 9개, 기존 quality gate 12개를 포함한다.

## Broader Validation

| Check | Result |
| --- | --- |
| Full non-resource suite, separate DAGRun excluded | 944 passed / 2 skipped, 36.73s; `pytest --ignore=tests/orchestration/test_airflow_dagrun.py -q -ra -n 2` |
| Ruff | 변경한 Python 3개 lint 및 format 통과 |
| Types and module boundaries | repository-wide `ty check`, `tach check` 통과; AST/negative-path 회귀는 전체 suite에 포함 |
| Wheel | 기존 환경의 offline wheel build 성공 |
| OpenSpec | `validate --all --strict --no-interactive`: 21 passed / 0 failed; Apply 1/1, all_done |
| Editor diagnostics | 변경한 Python 3개 오류 없음 |
| Real Airflow DAGRun | 5 passed, 144.13s; 별도 serial 실행, production task/psutil monkeypatch 없음 |

Skip은 실제 zizmor audit cache prerequisite와 Windows npm/Node prerequisite 각 1건이다. 전체 suite에서 impact selection filter를 사용하지 않았다.

최종 구현 checkpoint는 `fe8c324ad22e65b37465bb6233210d1d4146498f`다. 전체 suite 944개와 별도 DAGRun 5개는 중복되지 않으므로 현재 로컬 근거는 **949 passed / 2 skipped**다. 앞선 focused 실행과 native hook 수치는 이 합계에 다시 더하지 않는다.

독립 review-lead가 두 specialist와 검토한 최종 구현은 [19](19-review-detector-completion.md)의 **clear**다. 기존 네 단위의 clear를 재사용할 수 있음을 직접 대조했으며 current_required는 없다. Reviewer가 caller의 runtime 실행을 직접 재실행한 것은 아니다.

Native pre-push도 OpenSpec 21개, affected tests **206 passed / 63 deselected**, Python lint/format을 통과했고 `fe8c324a`의 원격 전달을 확인했다. 이 테스트 수는 위 전체 suite와 중복되므로 합산하지 않는다.

여섯 번째 substantive implementation/review loop를 마쳐 기존 counter는 6/30이다. 다음은 최종 base/head CI와 완료 문서·PR 전달을 확인하는 것이다.

## Remote Checkpoint

현재 main은 `6ed9882ae8bed628c24931b960c18327ac60f9af`이며 `git ls-remote`로 확인했다. PR의 prospective merge `d23ad935772a77444738a7511e2348893565e2b6`의 commit message도 head `fe8c324a`를 이 main에 합쳤음을 식별한다. Connector의 base SHA 응답 `8bc62fa6`와 실제 통합 대상 main을 혼동하지 않는다.

[CI Lite 39028730573](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39028730573)은 completed / success다. Job `117384763487`의 prospective merge checkout·Markdown·OpenSpec·dependency boundary·wheel·Python·selected tests가 모두 실제 success였다. 경로가 없는 actionlint·JSON/TOML·zizmor·lock 등은 skip이며 실행됐다고 주장하지 않는다.

이 구현·main 조합의 required validation과 독립 implementation gate를 충족했으므로 이 범위의 Run은 COMPLETE, loop counter는 6/30이다. 후속 변경은 완료 artifact만 다루며 source/test/Spec 동일성을 확인한다. 최종 문서 head의 최신 CI는 별도로 확인해 PR 본문과 GitHub checks에 남긴다. Human Ready 전환·approval·merge와 실제 AI 리뷰 품질 평가는 수행하지 않는다.
