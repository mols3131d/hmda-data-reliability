# Vision: Evidence-First Data Reliability

> **Goal:** HMDA 데이터 품질 이상을 근거와 함께 재현·검증하고, 위험한 recovery는 사람의 통제 아래 수행하는 local Data Reliability system을 만든다.

Project Pivot의 핵심 가치는 단순한 pipeline success가 아니라 **어떤 데이터 상태를 신뢰할 수 있는지, 어떤 문제를 어떤 evidence로 판단했는지, 어떤 recovery가 왜 허용됐는지 다시 설명할 수 있는 것**이다.

## Product Thesis

1. **Trusted data state** — source에서 analytical layer까지 재현 가능한 데이터 상태를 만든다.
2. **Deterministic reliability** — incident와 핵심 safety 판단은 코드와 evidence로 검증한다.
3. **Evidence-bound AI** — AI는 deterministic evidence와 기존 remediation 결과를 설명·검토하는 제한된 layer로 사용한다.
4. **Human-controlled mutation** — 위험한 state change는 검증된 proposal과 외부 human approval 뒤에만 수행한다.
5. **Replayable evaluation** — synthetic case와 deterministic evaluator로 판단·복구 품질을 반복 검증한다.

## Principles

- **Evidence-first** — profile, metadata, lineage와 실행 결과를 판단 근거로 남긴다.
- **Deterministic core** — LLM availability나 표현 변화가 detection, approval authority와 recovery safety를 결정하지 않는다.
- **Bounded automation** — automation은 owning domain contract와 human approval boundary를 우회하지 않는다.
- **Reproducible** — 같은 입력·설정·revision의 결과를 다시 설명할 수 있어야 한다.
- **Local-first** — portfolio 범위에서는 복잡한 cloud/distributed infrastructure보다 reliability contract와 검증 가능성을 우선한다.

## Boundaries

Project Pivot은 local HMDA reliability system에 집중한다. 대규모 distributed lakehouse, 승인 없는 autonomous recovery, 범용 autonomous RCA, production-grade authorization/audit platform은 이 비전의 필수 전제가 아니다.

이 문서는 장기 방향과 원칙만 소유하며 현재 phase, 구현 상태와 진행률을 기록하지 않는다.
