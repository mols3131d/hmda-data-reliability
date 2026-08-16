# MVP Status

> **Snapshot:** 2026-08-16 / `main@f7bd019`
>
> **Overall:** 🟡 Partial — 최소 Data Lake와 deterministic Reliability 기반은 존재하지만
> MVP 완료에 필요한 bounded LLM reviewer가 아직 없다.

## Domain Status

| Domain | State | Current revision validation | Remaining gap |
| --- | :---: | :---: | --- |
| HMDA Data | 🟢 Done | ⚪ Not Verified | - |
| Data Platform | 🟢 Done | ⚪ Not Verified | - |
| Data Operations | 🟢 Done | ⚪ Not Verified | - |
| Reliability | 🟡 Partial | ⚪ Not Verified | 실제 LLM reviewer, structured Agentic output와 invocation trace |
| Orchestration | 🟢 Done | ⚪ Not Verified | - |

`Done`은 현재 repository에 해당 MVP capability의 구현 evidence가 존재한다는 뜻이다.
`Current revision validation`은 이 snapshot revision에서 acceptance를 다시 실행했는지
별도로 표시한다. 이번 문서 재구성에서는 runtime validation을 실행하지 않았으므로
모든 domain을 `Not Verified`로 기록한다.

## MVP Completion Gap

현재 가장 중요한 gap은 Reliability domain의 **Minimal Agentic Review**다.

현재 remediation workflow는 LangGraph를 사용하지만 triage, RCA와 plan node가
deterministic code로 동작한다. 이것은 좋은 safety baseline이지만 실제 LLM 판단을
포함하지 않는다.

MVP 완료를 위해서는 최소 한 개 synthetic incident에서 다음 acceptance가 필요하다.

```text
deterministic evidence + RemediationDraft
→ real LLM reviewer
→ structured review
→ deterministic safety check
→ external approval
→ recovery
→ re-validation
```

LLM reviewer는 recovery 권한을 갖지 않으며 기존 approval boundary를 그대로 유지한다.

## Evidence

| Domain | Primary evidence |
| --- | --- |
| HMDA Data | `src/project_pivot/hmda_data/`, `tests/hmda_data/` |
| Data Platform | `dbt/`, `src/project_pivot/data_platform/`, `tests/data_platform/`, `tests/dbt/` |
| Data Operations | `src/project_pivot/data_operations/`, `tests/data_operations/` |
| Reliability | `src/project_pivot/reliability/`, `tests/reliability/` |
| Orchestration | `src/project_pivot/orchestration/`, `tests/orchestration/` |

세부 완료 기준은 각 domain MVP 문서를 따른다.
