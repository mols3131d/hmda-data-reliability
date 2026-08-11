# MVP Goal: Reliability

## Goal

하나의 controlled `volume_drop`을 evidence와 함께 탐지하고, 검증된 proposal에 대한 외부 approval 뒤 안전하게 복구한 다음 결과와 실패 경로를 재현 가능한 evidence로 남긴다.

## Analysis

- clean baseline은 incident와 remediation draft를 만들지 않는다.
- controlled `volume_drop`은 row-count evidence, downstream impact와 remediation draft를 만든다.
- proposal은 target content identity와 dbt projection identity를 recovery 조건에 결합한다.

## Safety And Recovery

- incomplete approval, stale target, diverged target과 invalid candidate는 target mutation 전에 차단한다.
- before state에서는 승인된 compare-and-replace recovery를 수행한다.
- expected after state에서는 duplicate mutation 없이 verification을 재개한다.
- recovery 뒤 partition content와 downstream dbt validation을 다시 확인한다.

## Evaluation

- success와 expected safety failure를 structured evaluation result로 표현한다.
- failure stage, mutation 여부, reconciliation과 artifact projection을 evidence에 남긴다.
- retry가 duplicate mutation이나 semantic drift를 만들지 않는지 확인한다.

## Done When

[`docs/mvp.md`](../../mvp.md)의 end-to-end proof를 deterministic acceptance로 재현하고 실패 경로의 evidence까지 검증할 수 있다.

## Non-Goals

- 다른 incident 유형의 recovery 확장
- approval UI와 security-grade authorization
- multi-host writer coordination과 자동 recovery

## References

- [Reliability Domain](../../domains/reliability.md)
- [MVP Goal](../../mvp.md)
- `tests/reliability/`
