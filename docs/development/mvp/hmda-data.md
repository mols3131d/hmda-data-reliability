# MVP Domain: HMDA Data

## Mission

Project Pivot이 검증할 수 있는 **신뢰 가능한 local source를 DuckDB Bronze까지 안전하게
적재하고 재현 가능한 failure case를 제공한다.**

HMDA Data domain은 Source→Bronze boundary를 소유한다. 데이터의 의미를 incident로 판단하거나
dbt analytical layer를 구성하지 않고, downstream이 같은 logical Bronze state를 다시 관찰할
수 있게 하는 것이 MVP 책임이다.

## MVP Contribution

- local HMDA source를 발견하고 입력 계약에 맞는지 검증한다.
- 원천을 변경하지 않고 DuckDB Bronze에 전체 또는 partition 단위로 적재한다.
- 반복 적재와 recovery 비교에 필요한 source/partition identity와 provenance를 유지한다.
- 정상 상태와 대표 synthetic failure를 재현 가능한 데이터 case로 제공한다.
- downstream Data Platform과 Reliability가 같은 logical Bronze state를 식별할 수 있게 한다.

## Done When

같은 source와 case definition에서 동일한 logical Bronze input을 다시 구성할 수 있고,
정상 case와 synthetic failure가 원천 훼손 없이 downstream에 전달된다.

완료 판단은 파일 수나 fixture 수가 아니라 다음 proof로 한다.

- source validation이 잘못된 입력을 명시적으로 거부한다.
- Source→Bronze 적재가 원천을 mutation하지 않고 반복 가능한 logical state를 만든다.
- partition replacement가 stale target이나 invalid candidate를 mutation 전에 차단한다.
- synthetic case의 identity와 기대 defect가 재현된다.
- recovery 이후 target content를 원래 기대 상태와 비교할 기준을 제공한다.

## Boundary

**Owns**

- HMDA source discovery와 validation
- Source→DuckDB Bronze load semantics
- source/partition identity와 provenance
- synthetic data case 생성

**Does not own**

- dbt staging/mart transformation과 artifact lifecycle
- cross-domain stage execution/promotion policy
- incident 판단과 remediation
- Agentic reasoning, approval과 recovery policy

## Acceptance Evidence

- `src/project_pivot/hmda_data/`
- `tests/hmda_data/`
- 관련 HMDA ingestion / synthetic-case OpenSpec

## References

- [MVP](README.md)
- [HMDA Data Domain](../../domains/hmda-data.md)
