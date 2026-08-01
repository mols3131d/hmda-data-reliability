---
type: openspec-rpi
title: "Review: <change-id>"
description: "<검증한 change와 status 요약>"
category: review
status: pending
relatedArtifacts:
    - <research-id>
    - <change-id>
---

# Review: <change-id>

## Summary

<verdict와 가장 중요한 evidence를 설명하는 한 문단>

## Reconciliation

| Axis | Result | Evidence |
| --- | --- | --- |
| Completeness | Pass / Fail / Unknown | `<spec or task>` ↔ `<implementation>` |
| Correctness | Pass / Fail / Unknown | `<requirement>` ↔ `<test or runtime result>` |
| Coherence | Pass / Fail / Unknown | `<proposal/design/task>` ↔ `<diff>` |
| Regression | Pass / Fail / Unknown | `<existing contract>` ↔ `<check>` |
| Evidence | Pass / Fail / Unknown | `<actual command and result>` |
| Risk | Pass / Fail / Unknown | `<assumption or residual risk>` |

## Findings

| Level | Owner | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| Blocker / Major / Minor / Note | Research / OpenSpec / Implement | <finding> | `<path:line>` 또는 command/result | <정확한 next action> |

## Validation Observed

| Check | Result | Notes |
| --- | --- | --- |
| `<command>` | Pass / Fail / Not run | <실제 output 요약 또는 이유> |

## Amendments

| Amendment | Reflected in OpenSpec? | Review impact |
| --- | --- | --- |
| <구현 중 변경> | Yes / No | <영향> |

## Route

| Status | Next action |
| --- | --- |
| approved | OpenSpec으로 archive |
| changes_requested | <Research / OpenSpec / Implement>로 돌아간 후 fresh Review |
| blocked | <blocker> 해결 후 fresh Review |
