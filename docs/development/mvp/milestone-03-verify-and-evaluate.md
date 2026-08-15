# Milestone 03: Verify and Evaluate

## Goal

Approved recovery가 실제로 incident를 해소했는지 검증하고, success·failure·retry 결과를 다음 판단에 사용할 수 있는 evidence로 남긴다.

## Proof

- Recovery 후 expected partition content와 profile state가 복원된다.
- Post-recovery lifecycle에서 target incident가 해소된다.
- Downstream dbt verification이 expected state를 확인한다.
- Failure가 mutation 전인지 후인지와 필요한 reconciliation action을 구분할 수 있다.
- 같은 approval의 retry는 duplicate mutation이나 semantic drift 없이 verification을 재개한다.

## Done When

Detection부터 recovery, data/dbt verification과 failure/retry evidence까지 하나의 deterministic end-to-end acceptance로 재현할 수 있다.

이 milestone의 완료가 현재 MVP의 완료 경계다.

## Boundary

이 milestone은 **복구 결과의 검증과 evidence**를 소유한다. 다른 incident 유형 확장이나 운영 control-plane은 후속 범위다.

## References

- [MVP](README.md)
- [MVP Status](status.md)
- [Reliability MVP Goal](reliability.md)
