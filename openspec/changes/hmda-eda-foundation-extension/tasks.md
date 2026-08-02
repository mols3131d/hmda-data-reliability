---
type: openspec-rpi
category: tasks
relatedArtifacts:
  - hmda-eda-foundation-extension
title: "HMDA foundation EDA extension tasks"
description: "descriptive EDA evidence 확장과 MVP readiness 검증을 구현하는 task 목록"
---

## 1. EDA Evidence Contract

- [ ] 1.1 `analyze_hmda_csv`에 핵심 code field의 count/share distribution evidence를 추가한다.
- [ ] 1.2 `loan_amount`와 `income`의 non-null count, five-number summary와 configured suspicious condition evidence를 추가한다.
- [ ] 1.3 `activity_year + state_code + loan_purpose` grain aggregate와 coverage evidence를 추가한다.
- [ ] 1.4 unknown code와 numeric anomaly를 raw 보존형 observation으로 직렬화하고 기존 evidence key와 backward compatibility를 유지한다.

## 2. Deterministic Tests And Fixtures

- [ ] 2.1 작은 HMDA fixture에 code distribution, numeric summary, anomaly count, grain expected values를 추가한다.
- [ ] 2.2 valid, unknown-code, suspicious-numeric, missing-column 입력에 대한 EDA contract test를 추가한다.
- [ ] 2.3 원천 byte 보존, connection close, partial evidence 미생성 regression test를 유지·보강한다.

## 3. Notebook And Runtime Validation

- [ ] 3.1 `notebooks/eda_mo.py`에 descriptive distribution, numeric summary, anomaly, grain evidence rendering을 추가한다.
- [ ] 3.2 valid fixture와 malformed fixture를 사용하는 notebook runtime smoke를 구현하고 실행 command를 고정한다.
- [ ] 3.3 representative EDA resource validation이 새 evidence 계산을 포함하도록 확인하고 memory/temp 결과를 기록한다.

## 4. Documentation And Foundation Evidence

- [ ] 4.1 `docs/references/hmda_eda.md`에 새 evidence key, metric definition, code reference, anomaly boundary와 validation command를 문서화한다.
- [ ] 4.2 foundation readiness 문서 또는 관련 evidence inventory에 MVP data information과 descriptive EDA capability를 연결한다.
- [ ] 4.3 raw → staging → mart grain, mart approval/denial grouping과 EDA interpretation이 일치하는지 문서와 test로 확인한다.

## 5. Focused Validation

- [ ] 5.1 EDA correctness, fixture, helper와 notebook smoke test를 실행한다.
- [ ] 5.2 `marimo check`, ruff/type diagnostics와 Markdown formatting을 실행한다.
- [ ] 5.3 기존 reliability/profile, dbt analytics와 전체 기본 test를 실행해 regression이 없는지 확인한다.
- [ ] 5.4 실제 source observation command를 실행하고 source path, 실행 시점, 주요 결과와 known anomaly를 report artifact에 기록한다.
