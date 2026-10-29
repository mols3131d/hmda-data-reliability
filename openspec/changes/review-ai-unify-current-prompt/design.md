---
type: openspec-spec-driven-tdd-design
category: design
title: Unify Current Review Prompt
description: 현재 staged 진입점을 공통으로 사용하고 과거 실행·렌더러를 명시적 legacy 경계로 옮깁니다.
---

## Technical Delta

기존 service 구현은 legacy/service.py로 이동한다. review_ai.review_null_spike와 review_ai.service.review_null_spike는 현재 staged 함수를 노출한다. 기존 staged 명칭은 같은 실행의 alias로 유지한다. 반환형은 의도적으로 StagedReviewResult로 전환한다. 기존 JSON 계약을 원하는 호출자는 legacy를 import하고 PromptIdentity를 명시한다.

공유 prompt 모듈은 canonical projection·직렬화·공통 반환형만 소유한다. 버전 맵과 structured renderer는 prompt/legacy로 이동한다. 지금 조립된 v1/v2/v3 본문을 immutable Markdown snapshot으로 보존해 현재 공유 정책을 수정해도 기존 digest가 바뀌지 않게 한다. 초기의 영어 prompt 등 더 오래된 기록은 계속 해당 project_revision으로 재현한다. 현재 language.md는 일반 한국어 정책으로 만들고 세 단계 조합에서 사용한다.

CLI reviewer 기본값은 현재 API이며 legacy provider는 명시적 분기에서만 import한다. MODE=legacy와 LEGACY_PROMPT_VERSION은 함께 명시해야 한다. 옛 MODE=structured는 provider 호출 전에 이전 방법을 안내하며 거부한다. 남은 PROMPT_VERSION은 현재 경로에서 무시하고 키 이름만 안내한다. Legacy의 환경 기본 timeout·retry는 기존 structured 의미를 유지한다.

main의 과거 checkout은 환경 변수만으로 새 코드가 되지 않는다. 실행 안내에 PR 작업 폴더를 명시한다. main의 checkout·첨부된 read-only .env·모델 설정은 변경하지 않는다.
