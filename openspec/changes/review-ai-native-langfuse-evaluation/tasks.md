---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Native Langfuse Review Evaluation
description: 원격 프롬프트와 SDK 실험을 기본 경로로 사용하고 중복 구현을 제거합니다.
tasks_completed: 5
tasks_total: 5
---

## Tasks

- [x] Langfuse native Prompt Management를 모든 검토의 단일 프롬프트 경로로 연결한다.
  - **Test first:** 세 prompt의 선조회·실행 중 version 고정·native compile의 history·공통 config와 원격 조회 실패를 검증한다.
  - **Done when:** 한국어 모듈은 seed로 남고 실행은 remote prompt만 사용하며 실패 시 fallback 없이 모델 호출 전에 종료한다.
- [x] 최초 등록과 SDK Dataset 실험을 작은 별도 진입점으로 제공한다.
  - **Test first:** setup에서만 쓰기가 발생하고 반복 실험은 기존 Dataset·task·SDK format을 사용하며 oracle을 provider에 주입하지 않는지 검증한다.
  - **Done when:** 선택적 Dataset version·prompt label을 사용할 수 있고 worker·별도 live CLI·native bootstrap·점수 조회 계층이 없다.
- [x] 실제 모델 호출 구간에 native generation을 연결한다.
  - **Test first:** 호출 범위·prompt/model/usage·전체 허용 메시지·raw 우선 저장·부분 실패와 관측 장애 시 core 결과 보존을 검증한다.
  - **Done when:** 사후 빈 관측과 전 artifact 재검증 없이 실제 호출·원문·collection을 연결한다.
- [x] SDK 기본 의존성과 표준 환경 설정으로 현재 실행을 통일한다.
  - **Test first:** SDK 설치 계약·기본 import·표준 제공자 환경·삭제된 설정/모듈 미제공을 검증한다.
  - **Done when:** SDK pin과 Runtime 예산은 유지하고 과거 opt-in·전용 외부 deadline·호환 설정을 제거한다.
- [x] 정본·개발·환경·인간 검토 안내를 native 책임 분담에 맞춘다.
  - **Done when:** 관련 테스트·정적 검사·문서·OpenSpec·배포 검증이 통과하고 실제 서버/UI·모델·사람 평가의 미검증 한계를 명시한다.

## Validation Boundary

실제 대상 서버의 등록·실험·UI와 모델 출력·사람 점수는 별도 증거다. 로컬 SDK 계약·fake transport·flush 반환을 실제 원격 적재나 품질 검증으로 기록하지 않는다.
