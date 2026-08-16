# MVP Domain: HMDA Data

## Mission

Project Pivot이 검증할 수 있는 **신뢰 가능한 local input와 재현 가능한 failure case**를 제공한다.

HMDA Data domain은 데이터의 의미를 추론하거나 incident를 판단하지 않는다. 원천을 안전하게
다루고, downstream Data Lake와 Reliability가 같은 입력을 다시 관찰할 수 있게 하는 것이
MVP에서의 책임이다.

## MVP Contribution

- local HMDA source를 발견하고 입력 계약에 맞는지 검증한다.
- 원천을 변경하지 않고 Bronze에 적재할 수 있는 안정적인 입력을 제공한다.
- logical partition과 실제 content를 구분할 수 있는 identity를 유지한다.
- 정상 상태와 대표 synthetic failure를 재현 가능한 데이터 case로 제공한다.
- downstream에서 evidence로 연결할 수 있는 source/partition provenance를 보존한다.

## Done When

같은 source와 case definition에서 동일한 logical input을 다시 구성할 수 있고,
정상 case와 synthetic failure가 원천 훼손 없이 Bronze와 Reliability에 전달된다.

완료 판단은 파일 수나 fixture 수가 아니라 다음 proof로 한다.

- source validation이 잘못된 입력을 명시적으로 거부한다.
- 반복 실행이 source를 mutation하지 않는다.
- synthetic case의 identity와 기대 defect가 재현된다.
- recovery 이후 target content를 원래 기대 상태와 비교할 기준을 제공한다.

## Boundary

**Owns**

- HMDA source discovery와 validation
- Bronze ingestion을 위한 source contract
- source/partition identity
- synthetic data case 생성

**Does not own**

- dbt transformation과 artifact lifecycle
- stage execution/promotion policy
- incident 판단과 remediation
- Agentic reasoning, approval과 recovery policy

## Acceptance Evidence

- `src/project_pivot/hmda_data/`
- `tests/hmda_data/`
- 관련 HMDA ingestion / synthetic-case OpenSpec

## References

- [MVP](README.md)
- [HMDA Data Domain](../../domains/hmda-data.md)
