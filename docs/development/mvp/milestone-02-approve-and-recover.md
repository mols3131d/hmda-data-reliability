# Milestone 02: Approve and Recover

## Goal

검증된 recovery proposal과 외부 approval을 실제 state change의 경계로 사용해 승인된 recovery만 안전하게 수행한다.

## Proof

- Recovery 후보 검증은 current state를 변경하지 않는다.
- Approval은 검증된 proposal과 승인 당시 target state에 결합된다.
- 불완전한 approval, 유효하지 않은 후보 또는 승인 이후 달라진 target은 변경 전에 차단된다.
- 승인된 recovery는 target을 기대한 데이터 상태로 복원한다.

## Done When

정확히 검증되고 승인된 recovery만 state change를 허용하며, 승인 범위를 벗어난 경우 기존 state를 보존함을 재현할 수 있다.

## Boundary

이 milestone은 **recovery authorization과 mutation safety**를 소유한다. Approval UI, security-grade authorization과 자동 승인은 MVP 범위가 아니다.

## References

- [MVP](README.md)
- [Reliability MVP Goal](reliability.md)
- [Architecture](../../ARCHITECTURE.md)
