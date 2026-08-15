# Milestone 02: Approve and Recover

## Goal

검증된 recovery proposal과 외부 approval을 실제 mutation의 경계로 사용해, 승인된 `volume_drop` target만 안전하게 복구한다.

## Proof

- Candidate validation은 current target과 shared current dbt evidence를 변경하지 않는다.
- Approval은 incident, target과 검증된 recovery proposal에 결합된다.
- Incomplete approval, invalid candidate, stale target과 diverged target은 mutation 전에 차단된다.
- Approved recovery는 기대한 partition content를 복원한다.

## Done When

정확히 검증되고 승인된 proposal만 target mutation을 허용하며, 승인 범위를 벗어난 상태에서는 기존 데이터를 변경하지 않음을 재현할 수 있다.

## Boundary

이 milestone은 **mutation authorization과 recovery safety**를 소유한다. Approval UI, security-grade authorization과 자동 승인은 MVP 범위가 아니다.

## References

- [MVP](README.md)
- [Reliability MVP Goal](reliability.md)
- [Architecture](../../ARCHITECTURE.md)
