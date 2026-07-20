---
name: iceberg-code-review
description: >
  USE WHEN: PR, diff, commit, file, function, code snippet 리뷰 또는 `__summary__.md`와
  finding별 상세 문서가 필요할 때.
  EXCLUDES: 코드 수정·리팩터링 구현, 일반 코드 설명, 비코드 문서 리뷰.
---

## Rules

1. 코드 리뷰만 수행. 수정 금지.
2. `__summary__.md`에 가장 치명적인 finding과 전체 결론부터 작성.
3. `full`은 배경, 근거, 영향, 권장 조치, 검증을 finding별 상세 문서에 작성.
4. 군더더기와 주관적 수식어 제거.

## Severity

| severity | emoji | callout | description |
| :--- | :---: | :--- | :--- |
| `bug` | 🔴 | `CAUTION` | 동작 오류, incident 유발 |
| `risk` | 🟡 | `WARNING` | 취약한 동작: race, null guard 누락, error 무시 |
| `nit` | 🔵 | `NOTE` | style, naming, 미세 최적화. 무시 가능 |
| `q` | ❓ | `TIP` | 제안이 아닌 판단에 필요한 질문 |

## Status

| status | description |
| :--- | :--- |
| `open` | 확인 또는 수정 필요 |
| `resolved` | 수정 후 검증 완료 |
| `dismissed` | 수정하지 않기로 결정 |

## Arguments

미지정 시 `lite` 사용.

| argument | workflow | output |
| :--- | :--- | :--- |
| `lite` | `./workflows/summary.md` | `__summary__.md` |
| `full` | `./workflows/summary.md`, `./workflows/finding-details.md` | `__summary__.md`, finding별 상세 문서 |

## References

| path | description |
| :--- | :--- |
| `./examples/` | 완성된 리뷰 문서 예시 |
| `./templates/` | 요약·상세 finding 문서 템플릿 |
