## 출력 형식

JSON 객체 하나만 반환한다. 응답에 마크다운 제목·목록·코드 펜스나 JSON 밖의 설명문을 덧붙이지 않는다.

다음 필드를 포함한다.

- `incident_id`, `incident_type="null_spike"`, `target_column`
- `deterministic_facts`: `baseline_null_rate`, `current_null_rate`, `delta`, `threshold`
- 비어 있지 않은 `review_summary`와 `evidence_used`
- `findings`: `kind`, `description`, `evidence_refs`를 포함한다.
  `kind`는 `observation`, `concern`, `omission`, `uncertainty` 중 하나다.
- `uncertainties`
- `utility_contributions`: `kind`, `description`, `evidence_refs`와 해당하는 경우 `priority`를 포함한다.
  `kind`는 `evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty` 중 하나다.
- `advisory_recommendation`: `support`, `needs_human_review`, `insufficient_evidence` 중 하나.
