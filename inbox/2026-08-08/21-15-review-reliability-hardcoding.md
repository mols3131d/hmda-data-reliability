---
type: review
title: "Reliability Hardcoding Review"
description: "reliability domain의 threshold, table default, remediation/recovery policy literal을 검토한 결과 material hardcoding finding은 확인되지 않았다."
status: "completed"
tags:
  - "domain:reliability"
  - "concern:hardcoding"
  - "concern:configuration"
---

> [!NOTE]
> **Pass.** 현재 `reliability`의 주요 numeric threshold는 `DetectionThresholds`로 명시적으로 교체 가능하고, recovery의 기본 HMDA table은 `hmda_data`가 소유한 `HMDA_LOANS_TABLE`을 import해 재사용한다. incident kind, recovery action, remediation policy처럼 고정된 문자열은 현재 reliability contract의 domain semantics로 확인되어 material hardcoding defect로 판단하지 않았다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/reliability/**` | `main@8746db54c0e761f62e1fe4f248f9fdcce6266423` | detection thresholds, profiling/recovery defaults, remediation/evaluation policy와 관련 tests | Pass |

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| domain contract 확인 | `docs/domains/reliability.md`의 read-only lifecycle, recovery/evaluation boundary 확인 | Pass |
| detection threshold ownership | `DetectionThresholds`가 volume/null/freshness threshold를 typed override로 제공 | Pass |
| HMDA table default ownership | `ApprovedBackfillRequest.table_name`이 `HMDA_LOANS_TABLE`을 import해 사용 | Pass |
| policy literal candidate | incident kind, recovery action, remediation mapping은 현재 contract semantics로 분류 | Pass |
| duplicate operational path candidate | database/source 경로를 reliability 자체 default로 다시 정의하는 경로는 확인되지 않음 | Pass |
| runtime reproduction | 실행하지 않음 | Not Verified |
| pytest | 실행하지 않음 | Not Verified |

## Remaining Risks

- 이번 판정은 hardcoding/configuration ownership에 한정한다. reliability algorithm의 적절성이나 threshold 값 자체의 품질을 검증한 것은 아니다.
- 향후 threshold가 환경별 운영 설정으로 승격되면 application configuration과 연결 여부를 별도로 검토해야 한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Pass | 변경 가능 값은 typed configuration으로 노출되고 cross-domain table default도 공유 constant를 재사용해 현재 material hardcoding defect가 확인되지 않았다. | 별도 hardcoding fix 없음. configuration architecture 변경 시 regression review만 수행한다. |
