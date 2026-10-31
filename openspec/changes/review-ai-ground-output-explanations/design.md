---
type: openspec-spec-driven-tdd-design
category: design
title: Ground Review AI Output Explanations
description: 기존 prompt renderer와 평가 경계를 재사용하는 최소 후보를 정의합니다.
---

## Technical Delta

v3는 독립된 고정 instruction으로 등록한다. 과거 v1/v2 문자열을 조합·수정하지 않아 historical digest를 보존한다. 숫자 표시 field나 계산기를 input projection에 추가하지 않고, 기존 canonical facts와 단위 설명만 사용한다. 내용 예시를 제거하고 기존 field/type 설명을 유지해 복사 유입을 줄이는 후보로 삼는다.

품질 corpus는 test-only JSON으로 유지한다. 정답 수치는 독립 계산으로 고정하고 structured validator가 semantic negative control을 허용함을 명시적으로 검증한다. 실제 출력의 의미와 utility는 기존 human 평가 owner에 남긴다.
