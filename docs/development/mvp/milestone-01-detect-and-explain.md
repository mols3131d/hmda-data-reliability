# Milestone 01: Detect and Explain

## Goal

Controlled `volume_drop`을 데이터 변경 없이 탐지하고, 무엇이 잘못됐고 어디에 영향이 있는지 검토 가능한 evidence로 설명한다.

## Proof

- Clean baseline에서는 incident와 remediation draft가 생성되지 않는다.
- Controlled `volume_drop`에서는 detection evidence, downstream impact와 remediation draft가 생성된다.
- 분석 결과는 같은 입력과 baseline에서 결정론적으로 재현된다.
- Reliability lifecycle은 approval, recovery와 report write를 수행하지 않는다.

## Done When

Clean case와 defect case를 명확히 구분하고, defect의 incident·impact·remediation evidence를 read-only lifecycle 하나로 재현할 수 있다.

## Boundary

이 milestone은 이상을 **판단하고 설명하는 단계**다. Candidate validation, approval과 target mutation은 다음 milestone이 소유한다.

## References

- [MVP](README.md)
- [Reliability MVP Goal](reliability.md)
- [Reliability Domain](../../domains/reliability.md)
