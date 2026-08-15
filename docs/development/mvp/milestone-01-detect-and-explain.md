# Milestone 01: Detect and Explain

## Goal

Controlled `volume_drop`을 current state 변경 없이 구분하고, 무엇이 잘못됐고 어디에 영향이 있는지 검토 가능한 evidence로 설명한다.

## Proof

- Clean baseline과 controlled defect를 명확하게 구분할 수 있다.
- Defect의 원인 판단, downstream impact와 가능한 remediation 근거가 함께 제시된다.
- 같은 입력과 baseline에서 같은 판단을 재현할 수 있다.
- 분석 과정은 current data 또는 실행 상태를 변경하지 않는다.

## Done When

Clean case와 defect case를 재현 가능하게 구분하고, defect의 의미와 영향을 read-only evidence로 설명할 수 있다.

## Boundary

이 milestone은 이상을 **판단하고 설명하는 것**까지 소유한다. Recovery 후보 검증, approval과 실제 state change는 다음 milestone의 범위다.

## References

- [MVP](README.md)
- [Reliability MVP Goal](reliability.md)
- [Reliability Domain](../../domains/reliability.md)
