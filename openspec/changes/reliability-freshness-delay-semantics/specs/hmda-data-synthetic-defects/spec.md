---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-synthetic-defects
description: Source schema를 변경하는 legacy freshness synthetic case를 제거한다.
tags:
  - "domain:reliability"
  - "capability:hmda-data-synthetic-defects"
  - "freshness-delay"
---

## REMOVED Requirements

### Requirement: Freshness delay case

- **Reason** - Source HMDA row에 synthetic `observed_at` column을 추가하면 Bronze ingestion freshness가 아니라 source schema change와 임의 observation metadata를 함께 만든다.
- **Migration** - Freshness behavior는 isolated disposable DuckDB의 기존 `ingested_at`만 변경하는 `evaluate_freshness_delay_vertical_slice`를 사용한다.
