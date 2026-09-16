---
type: openspec-spec-driven-tdd-design
category: design
title: "MVP Proof Evidence Recording"
description: "Proof revision을 변경하지 않고 실행 증거를 보존한다."
---

## Technical Delta

Final 실행 전에 tracked 준비 문서를 커밋하고, 실행 기록은 ignored `.local/pr239/proofs/<SHA>/`와 PR metadata에 저장한다. 기존 architecture와 test/live entrypoint를 사용하며 application technical delta는 없다.

Classifier test helper에 optional working root를 주고, active Change와 canonical capability directory를 `tmp_path` 아래 fixture로 만든다. 실제 classifier script를 그 working root에서 실행한다. Active Change 유무를 테스트가 통제하며 product classifier와 assertion을 대체하지 않는다.
