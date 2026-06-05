---
id: "001"
title: "로컬 재현 가능한 MVP 런타임"
status: "accepted"
date: "2026-06-05"
description: "로컬에서 전체 incident workflow를 반복 실행할 수 있게 한다."
categories:
    - "architecture"
tags:
    - "runtime"
    - "mvp"
    - "reproducibility"
related-files:
    - "docs/vision.md"
    - "docs/architecture.md"
---

# ADR-001: 로컬 재현 가능한 MVP 런타임

## Context (배경)

이 프로젝트의 목적은 production cloud 배포가 아니라 Data Reliability Incident lifecycle을 재현 가능하게 보여주는 것이다. 포트폴리오 사용자는 로컬 환경에서 ingestion, profiling, detection, RCA, remediation, evaluation 흐름을 반복 실행할 수 있어야 한다.

## Decision (결정)

MVP는 로컬 실행을 기준으로 구성한다. 로컬 query engine, 로컬 파일 기반 저장소, 로컬 orchestration 실행을 우선하고, cloud warehouse나 managed service는 확장 방향으로만 둔다.

## Consequences (결과)

- 긍정적 영향: 설치와 데모가 단순해지고, 동일한 synthetic incident를 반복 평가할 수 있다.
- 부정적 영향 및 리스크: 실제 운영 규모의 보안, 비용, 네트워크, 권한 모델은 직접 검증하지 못한다.
- 후속 작업: 로컬 경로와 실행 명령을 README와 backlog에 명확히 정리한다.

## Alternatives Considered (검토한 대안)

| 대안 | 채택하지 않은 이유 |
|---|---|
| Cloud warehouse 우선 구성 | MVP 목표가 운영 배포보다 workflow 검증에 있다. |
| Spark cluster 구성 | 대규모 처리 성능보다 재현성과 반복 평가가 더 중요하다. |

---

- Decided by: 프로젝트 작성자
