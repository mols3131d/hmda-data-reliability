---
type: openspec-spec-driven-tdd-design
category: design
title: Synthetic Source Preservation Guard
description: 입력 경로와 삭제 예정 case directory의 충돌을 정리 동작 전에 판별하는 경계를 명확히 합니다.
---

## Technical Delta

기존 writer의 case directory 삭제 전에 실제 source 경로와 삭제 범위를 비교하는 검증을 둔다. 경로 문자열만 비교하지 않고 정규화한 경로(상대경로·심볼릭 링크 별칭 포함)를 기준으로 case directory 내부 원본을 거부한다. DuckDB의 `glob`으로 reader가 선택하는 실제 입력 파일을 확인하고, 입력 파일과 상위 디렉터리의 중간 심볼릭 링크까지 따라가 삭제되는 경로가 있으면 거부한다. 최종 원본과 입력 해석에 필요한 경로를 구분해, 재생성되는 case directory를 거쳐 `..`로 빠져나가는 기존의 유효한 입력은 유지한다. 세 public generator가 이 검증을 공유하고, 충돌이 없을 때의 기존 출력 교체 방식은 유지한다.
