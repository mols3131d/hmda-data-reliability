## Context

profile snapshot slice는 partition별 row count, null rate, schema hash, freshness를 `ProfileSnapshot`으로 계산한다. 이번 slice는 baseline/current snapshot을 비교해 기본 품질 이상을 `Evidence`와 `Incident`로 승격한다.

Detector는 MVP의 첫 incident lifecycle 진입점이다. 아직 영구 저장소, impact analysis, remediation은 없으므로 출력 contract를 반환하는 pure Python 모듈로 시작한다.

## Goals / Non-Goals

**Goals:**

- baseline/current `ProfileSnapshot` 비교 API를 제공한다.
- volume drop, null spike, schema drift, freshness delay 4가지 rule을 구현한다.
- 탐지마다 `Evidence`와 `Incident`를 생성하고 `incident.evidence_refs`를 연결한다.
- threshold와 owner 설정을 Pydantic 모델로 고정한다.
- 테스트에서 의도한 incident type과 evidence payload를 검증한다.

**Non-Goals:**

- ML 기반 이상 탐지
- incident/evidence 영구 저장
- severity routing, catalog owner 조회
- impact analysis, remediation draft, approval/backfill 실행
- 여러 baseline window 통계 계산

## Decisions

### Detector 출력은 `DetectionResult`로 묶는다

각 탐지 결과는 `Incident`와 `Evidence`를 한 쌍으로 반환한다. downstream 단계는 `incident.evidence_refs`와 evidence id를 통해 연결한다.

대안: incident만 반환하고 evidence는 별도 저장소에서 조회. 아직 저장소가 없고 MVP slice가 작아야 하므로 제외한다.

### 비교 기준은 baseline/current snapshot 2개로 제한한다

첫 구현은 이전 정상 snapshot과 현재 snapshot을 직접 비교한다. row count drop과 null spike는 baseline 대비 변화율을 계산한다.

대안: 여러 baseline window 평균/표준편차 사용. 평가에는 좋지만 이번 slice의 목표인 기본 rule detector를 넘어서므로 제외한다.

### Rule threshold는 Pydantic config로 둔다

`DetectionThresholds`는 volume drop ratio, null spike delta, freshness delay minutes를 가진다. schema drift는 hash 불일치 자체를 이상으로 본다.

대안: YAML config. 운영에는 좋지만 아직 static contract 구현 단계라 Python 모델이 충분하다.

### Evidence payload는 detector 판단 근거를 보존한다

Evidence payload에는 baseline/current 주요 값과 threshold를 넣는다. Agent/RCA가 근거 없이 추론하지 않게 한다.

대안: summary 문자열만 저장. 후속 RCA/평가에서 수치 근거를 재사용하기 어려워 제외한다.

## Risks / Trade-offs

- [Risk] baseline 하나만으로 노이즈가 클 수 있다. -> MVP는 synthetic case 검증 우선이며 window baseline은 후속 확장으로 둔다.
- [Risk] 여러 rule이 동시에 탐지될 수 있다. -> detector는 모든 matching rule을 반환해 후속 triage가 선택 가능하게 한다.
- [Risk] threshold 기본값이 도메인별로 과하거나 약할 수 있다. -> request에서 명시적으로 override 가능하게 한다.
