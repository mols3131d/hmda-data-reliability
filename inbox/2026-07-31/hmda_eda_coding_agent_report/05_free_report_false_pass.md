---
title: "자유 보고서: False Pass 방지의 의미"
description: "이번 HMDA EDA 작업의 의미와 evidence 품질, false pass 방지에 대한 자유 보고서다."
date: 2026-07-31
---

# 자유 보고서: False Pass 방지의 의미

이번 작업의 핵심은 metric을 더 많이 출력하는 것이 아니라 evidence가 실제로
무엇을 증명하는지 강제하는 것이었다.

Manifest에 file hash와 expected invariant가 기록되어 있어도 validator가 일부
field만 읽으면 report는 풍부해 보이면서 false pass를 허용한다. 특히 null이 0인
column은 값 자체가 눈에 띄지 않아 map에서 빠져도 통과하기 쉽다. 이번 변경은
required column의 key coverage와 typed contract를 함께 강제해 이 빈틈을 줄였다.

Memory runner에서도 process exit code만으로 성공을 판단하면 malformed report,
missing worker output, timeout, OOM이 모두 같은 결과로 뭉개진다. 이번 구현은
resource status, output validation, failure reason, temp disk evidence를 한 run의
결과로 남긴다. 실패를 숨기는 대신 다음 조사를 위한 evidence로 바꾸는 방향이다.

다만 validation의 강도와 workload의 대표성은 다른 문제다. 작은 deterministic
fixture에서 contract와 runner semantics가 검증됐다는 사실은 fixture 계약의
품질을 보여줄 뿐, full source의 memory safety를 보장하지 않는다. 따라서 이
작업의 성공 기준은 “full source가 안전하다”가 아니라 다음 세 가지다.

1. fixture manifest가 모호하거나 불완전하면 workload를 유효한 memory test로
   통과시키지 않는다.
1. auxiliary output이 손상되거나 run이 실패해도 cleanup과 final report가 남는다.
1. 저장된 report가 정확한 fixture bytes와 manifest digest로 재현 가능하다.

다음 작업자가 기억해야 할 가장 중요한 것은 pass 결과보다 미실행 경계다. 현재
focused correctness test와 static check는 통과했지만, 실제 3 GiB hard-limit
process-level memory gate는 별도로 실행해야 한다. 이 경계를 보고서와 report
artifact에 계속 남겨야 representative fixture evidence가 full-source 보증으로
과대 해석되지 않는다.

이번 변경은 작지만 운영상 의미가 있다. 검증 실패를 “결과 없음”으로 끝내지 않고
실패 원인과 입력 provenance를 함께 보존하면, 다음 세션은 동일한 workload를
재현하고 실패 원인을 좁힐 수 있다. 이는 memory budget validation을 일회성
실행이 아니라 추적 가능한 evidence 생산 과정으로 바꾼다.
