---
type: research
title: Langfuse Entry Evidence
description: PR 248의 SDK, 종료 제어와 annotation mapping 착수 조건을 확인한다.
---

# Langfuse Entry Evidence

2026-09-26, base `1d7e5c70baa03540644e0dac71b740330f3e58cb`, starting head `e8441fb896eb94d07aed492b1dce0c641df2b0eb` 기준이다. Canonicalization은 #250에서 완료됐고 remote branch에도 반영됐다. 공식 문서 접근은 이번 세션에 성공했다. 사용자는 destination이 없으며 로컬 구현·검증을 먼저 진행하도록 지정했다.

## Evidence

- [PyPI 4.15.6](https://pypi.org/project/langfuse/4.15.6/)을 임시 uv 환경에 설치하고 Python 3.13에서 import와 package version을 확인했다. Repository dependency는 아직 변경 전이다.
- [SDK reference](https://python.reference.langfuse.com/langfuse)는 수동 `start_observation`, private `tracer_provider`, `flush`, `shutdown`을 제공한다. 설치한 4.15.6 source에서도 확인했다. `resource_manager.py`의 `flush`는 score/media queue `join()`을 호출하며 전체 timeout 인자가 없다. 생성자 request timeout만으로 프로세스 종료 상한을 증명할 수 없다.
- [Advanced features](https://langfuse.com/docs/observability/sdk/advanced-features)는 global 등록 없는 별도 provider를 지원하지만 active context는 공유된다고 설명한다. 별도 단기 process는 parent 계측과 background thread를 격리할 수 있다.
- [Manual scores](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-ui)는 score별 comment를 제공하지만 comment는 optional이다. Repository에서는 다섯 항목 모두 0/1/2와 non-empty rationale가 있어야 complete다. UI 완료 표시를 이 판정으로 대신할 수 없다.
- [Annotation queues](https://langfuse.com/docs/evaluation/evaluation-methods/annotation-queues)는 score config를 선택하고 observation을 queue에 넣는 수동 경로를 제공한다. Queue 자동 provisioning이나 importer는 필요하지 않다. 특정 배포 UI는 미확인이다.

## Workflow Value

현재 `scripts/run_agentic_review_live.py`는 검증된 invocation path를 출력하고 `evaluation.py`는 다섯 criterion과 digest를 소유한다. 사람이 JSON의 input/output·model·revision을 오가며 읽는 단계와 별도 채점 입력을 observation 상세 화면으로 모을 수 있다는 가설이다. 항목별 판단과 근거 작성은 줄이거나 자동화하지 않는다. 대상 배포가 없어 실제 비용 절감을 측정하지 않았다.

## Decision Inputs

작은 child process를 harness가 timeout으로 종료하면 init/export/flush/shutdown 전체를 묶어 제한할 수 있다. Child에는 허용된 projection과 명시적 Langfuse credential만 전달하고 stdout/stderr는 노출하지 않는다. Export elapsed time은 model latency가 아니므로 observation 이름과 metadata에서 post-hoc projection임을 표시한다. SDK 반환은 `submitted_unverified`이며 원격 확인을 대신하지 않는다.

## Run Scope

Prepare: ready with limits. Goal은 로컬 구현과 offline 계약 검증 및 Draft PR 갱신이다. Live destination·human judgment는 현재 실행에서 제외하고 PR 전체 완료 조건으로 남긴다. Plan은 새 `review-ai-langfuse-projection` Change가 소유하며 archived utility Change를 재활성화하지 않는다. 구현 시 schema-specific RPI가 lifecycle을 소유한다.
