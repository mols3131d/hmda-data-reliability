---
title: "이번 작업에서 어려웠던 일"
description: "HMDA EDA contract와 memory runner 수정 과정에서 발생한 기술적 어려움과 해결 방법을 기록한다."
date: 2026-07-31
---

# 이번 작업에서 어려웠던 일

## Typed contract와 기존 public API의 균형

기존 manifest는 `dict[str, Any]` 중심이라 typed nested model로 바꾸면 생성 경로,
validation, test assertion이 모두 영향을 받는다. public function 이름은 유지하고
`files`와 `expected`의 내부 구조만 typed model로 교체했다. 생성기와 validator가
같은 Pydantic model을 사용하도록 해 계약 중복을 줄였다.

## Zero-null column 누락 문제

기존 evidence validation은 manifest에 기록된 null field만 순회했다. 그 결과
null count가 0인 required column이 evidence에서 빠져도 통과할 수 있었다. 단순 값
비교로는 해결되지 않으므로 schema, null count, null rate의 key set을 모두 7개
required column과 비교하도록 변경했다.

## Activity-year cardinality와 skew의 상호 검증

cardinality만 기록하면 expected count가 달라져도 발견하지 못한다. count 합계,
skew key set, skew 합계, count 기반 비율을 함께 검증해야 했다. 부동소수점 비교는
`math.isclose`로 제한된 허용 오차를 사용했다.

## Runner 예외와 cleanup/report 순서

기존 runner는 GNU `time` parse error나 worker JSON error가 발생하면 예외가 `_run_once`
밖으로 전파되어 cleanup과 final report가 생략될 수 있었다. process/resource 상태,
time report, worker output, temp disk 측정을 독립적인 failure source로 모으고
`finally`에서 directory를 제거하도록 재구성했다.

## Mypy module resolution

초기 mypy 호출에서는 `scripts/run_hmda_eda_memory.py`가 서로 다른 module name으로
중복 해석됐다. package/test surface와 standalone runner를 분리하고
`MYPYPATH=src --explicit-package-bases`를 사용해 invocation 문제와 실제 type
error를 구분했다.

## Memory test 범위와 검증 비용

5M-row process-level workload를 일반 pytest에 포함하면 개발 feedback이 무거워진다.
따라서 작은 unit/component test로 failure path를 검증하고 실제 workload는
`memory` marker로 분리했다. 이 때문에 ordinary pytest가 pass해도 hard-limit
memory gate를 통과했다는 의미는 아니다.

## Formatter warning

보고서 Markdown은 `rumdl fmt`를 통과했지만 repository 설정의 `MD054: style`
unknown-option warning이 함께 표시됐다. 문서 자체의 formatting failure는 아니지만
repository Markdown 설정은 별도 정리 대상이다.
