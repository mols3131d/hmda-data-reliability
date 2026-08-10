# Directive

이 문서는 `pivot-clarify-code`의 인간 주도 규범적 기준선이다. 실행 절차보다 목적, 요구사항과 설계 결정을 소유한다.

## Purpose

기존 동작을 보존하면서 코드 이해 부채를 줄인다.

잘못 이해했을 때 비용이 큰 읽기 병목을 가장 작은 안전한 변경으로 해소해, 호출자는 구현을 깊게 읽지 않고 필요한 사용 의미를 알 수 있고 유지보수자는 코드에서 의도와 제약을 복원할 수 있게 한다.

코드 품질 전반을 개선하거나 기능, 정확성, 성능, 아키텍처 문제를 대신 해결하는 것은 목적이 아니다.

## Requirements

| ID | Requirement |
| --- | --- |
| R-01 | 기존 observable behavior와 public contract를 보존해야 한다. |
| R-02 | 오해 비용이 가장 큰 이해 병목 하나를 우선해야 한다. |
| R-03 | 병목을 해소할 가장 작은 안전한 변경을 선택해야 한다. |
| R-04 | 이름과 구조로 충분하면 prose를 늘리지 않고, prose로 충분하면 abstraction을 늘리지 않아야 한다. |
| R-05 | caller가 알아야 할 의미는 API 가까이, maintainer가 알아야 할 code-local 이유는 코드 가까이, 넓은 정책은 canonical owner에 두어야 한다. |
| R-06 | caller, 관련 test와 현재 behavior를 이해 근거로 사용하되 test를 requirement나 canonical contract의 대체 근거로 취급하지 않아야 한다. |
| R-07 | correctness review, architecture redesign, repository navigation, 포괄적 documentation처럼 주된 문제가 다른 책임에 속하면 별도 작업으로 분리해야 한다. |
| R-08 | 선택한 병목이 해소되면 추가 정리를 위해 scope를 확대하지 않고 중단해야 한다. |
| R-09 | 새 규칙이나 기능은 이 기준선의 목적과 요구를 강화할 때만 추가해야 한다. |

## Decisions

| Decision | Rationale |
| --- | --- |
| clarification을 behavior-preserving change로 제한한다. | 이해 개선과 behavior 변경을 분리해야 변경 이유와 검증 범위가 명확하게 유지된다. |
| 하나의 가장 중요한 병목을 우선한다. | 전면 정리는 검토 범위와 변경 위험을 키우며 이해 부채보다 일반 refactoring으로 흐르기 쉽다. |
| 최소 개입을 기본 전략으로 사용한다. | 설명, helper와 abstraction 자체도 새로운 이해 비용이 될 수 있다. |
| caller 의미와 maintainer 이유의 소유 위치를 구분한다. | 독자가 다른 정보를 같은 위치에 쌓지 않고, 넓은 정책의 중복과 drift를 줄이기 위해서다. |
| test는 이해와 validation의 근거로 사용하되 contract authority로 승격하지 않는다. | 현재 behavior를 빠르게 복원하면서도 stale 또는 불완전한 test가 요구사항을 대신하는 것을 방지한다. |
| repository navigation과 다른 품질 작업은 흡수하지 않는다. | 책임을 넓히면 스킬의 trigger, scope와 종료 조건이 흐려진다. |
| 병목이 해소되면 중단한다. | 추가 정리가 가능하다는 이유만으로 작업을 계속하면 스킬의 목적이 코드 명확화에서 일반 품질 개선으로 변한다. |
