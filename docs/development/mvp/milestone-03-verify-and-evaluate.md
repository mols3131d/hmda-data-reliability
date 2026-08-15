# Milestone 03: Verify and Evaluate

## Goal

Approved recovery가 실제로 incident를 해소했는지 검증하고, success·failure·retry 결과를 다음 판단에 사용할 수 있는 evidence로 남긴다.

## Proof

- Recovery 후 target이 기대한 데이터 상태로 복원된다.
- Post-recovery validation에서 대상 incident가 해소된다.
- Downstream validation이 복구된 state를 사용할 수 있음을 확인한다.
- Failure가 state change 전인지 후인지와 필요한 다음 action을 구분할 수 있다.
- Retry는 중복 state change나 semantic drift 없이 필요한 verification을 이어간다.

## Done When

Detection부터 recovery, verification과 failure/retry evidence까지 하나의 deterministic end-to-end acceptance로 재현할 수 있다.

이 milestone의 완료가 현재 MVP의 완료 경계다.

## Boundary

이 milestone은 **복구 결과의 검증과 evidence**를 소유한다. 다른 incident 유형 확장이나 운영 control-plane은 후속 범위다.

## References

- [MVP](README.md)
- [MVP Status](status.md)
- [Reliability MVP Goal](reliability.md)
