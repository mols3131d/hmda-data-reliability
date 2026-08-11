# MVP Goal: Reliability

## Goal

하나의 controlled `volume_drop`을 evidence와 함께 탐지하고, 검증된 proposal에 대한 외부 approval 뒤 안전하게 복구한 다음 결과와 실패 경로를 재현 가능한 evidence로 남긴다.

## Outcomes

### Analysis

- clean baseline에는 incident와 remediation draft가 없다.
- controlled `volume_drop`에는 detection evidence, downstream impact와 remediation draft가 있다.
- recovery proposal은 승인 대상과 현재 target/dbt evidence를 식별할 수 있다.

### Recovery Safety

- incomplete approval, invalid candidate, stale target과 diverged target은 mutation 전에 차단된다.
- 승인된 recovery는 기대한 partition content를 복원하고 downstream validation을 통과한다.
- 이미 복원된 target의 retry는 duplicate mutation 없이 필요한 verification을 재개한다.

### Evidence

- success와 expected safety failure를 구조화된 결과로 구분할 수 있다.
- failure가 mutation 전인지 후인지와 다음 reconciliation action을 확인할 수 있다.
- retry가 duplicate mutation이나 semantic drift를 만들지 않는다.

## Done When

[`docs/mvp.md`](../../mvp.md)의 end-to-end proof와 주요 failure path를 deterministic acceptance로 재현할 수 있다.

## Non-Goals

- 다른 incident 유형의 recovery 확장
- approval UI와 security-grade authorization
- multi-host writer coordination과 자동 recovery

## References

- [Reliability Domain](../../domains/reliability.md)
- [MVP Goal](../../mvp.md)
- `tests/reliability/`
