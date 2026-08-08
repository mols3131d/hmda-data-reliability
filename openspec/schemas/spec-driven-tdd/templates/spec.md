---
type: openspec-spec-driven-tdd-spec
category: spec
title: <capability-name>
description: <Capability가 보장하거나 변경하는 행동을 짧게 설명한다.>
# OPTIONAL PARSABLE TAGS: Proposal의 domain/subdomain/free tags를 상속하고,
# 정확히 하나의 capability 태그를 파일 경로와 일치시킨다.
tags:
  - "domain:domain-name"
  - "subdomain:subdomain-name"
  - "capability:capability-name"
  - "tag-name"
---

<!--
형식 규칙:
- OpenSpec delta 헤더와 `### Requirement:`, `#### Scenario:` 형식은 파싱 계약으로 유지한다.
- 하나의 파일은 하나의 Capability를 다룬다.
- `capability:<name>` 태그는 파일 경로 `specs/<name>/spec.md`와 일치시킨다.
- Requirement는 SHALL 또는 MUST를 사용한다.
- 모든 Requirement에는 하나 이상의 Scenario가 있어야 한다.
- WHEN과 THEN은 필수이며 GIVEN과 AND는 필요할 때만 사용한다.
- New Capability는 50자 이상의 Purpose를 작성하고, 기존 Capability 변경에서는 Purpose를 삭제한다.
- 사용하지 않는 변경 유형은 섹션 전체를 삭제한다.
-->

<!-- OPTIONAL SECTION: New Capability의 delta spec에서만 파일 첫 본문으로 유지한다.
Archive 시 새 main spec의 Purpose로 복사되므로 50자 이상의 완전한 설명을 작성한다.
기존 Capability의 delta spec에서는 이 섹션을 삭제한다. -->

## Purpose

<Capability가 존재하는 이유와 제공하는 핵심 가치를 50자 이상으로 설명한다.>

<!-- OPTIONAL SECTION: 새로운 Requirement가 있을 때만 유지한다. -->

## ADDED Requirements

### Requirement: <requirement name>

<시스템이 보장해야 하는 행동을 SHALL 또는 MUST로 작성한다.>

#### Scenario: <scenario name>

- **GIVEN** - <중요한 사전 상태>
- **WHEN** - <행동을 유발하는 조건 또는 입력>
- **THEN** - <관찰되어야 하는 결과>
- **AND** - <추가 조건 또는 결과>

<!--
OPTIONAL SECTION: 기존 Requirement의 행동이나 계약이 바뀔 때만 유지한다.
기존 Requirement와 모든 Scenario를 변경 후의 완전한 형태로 작성한다.
-->

## MODIFIED Requirements

### Requirement: <existing requirement name>

<변경 후 시스템이 보장해야 하는 전체 행동>

#### Scenario: <scenario name>

- **GIVEN** - <중요한 사전 상태>
- **WHEN** - <행동을 유발하는 조건 또는 입력>
- **THEN** - <변경 후 관찰되어야 하는 결과>
- **AND** - <추가 조건 또는 결과>

<!-- OPTIONAL SECTION: 기존 Requirement를 제거할 때만 유지한다. -->

## REMOVED Requirements

### Requirement: <existing requirement name>

- **Reason** - <제거 이유>
- **Migration** - <전환 방법 또는 대체 행동>

<!-- OPTIONAL SECTION: 행동은 유지하고 이름만 바뀔 때만 유지한다. -->

## RENAMED Requirements

- **FROM** - `### Requirement: <old requirement name>`
- **TO** - `### Requirement: <new requirement name>`
