---
type: openspec-spec-driven-tdd-design
category: design
title: Airflow data-plane orchestration adapter
description: Thin Airflow adapter over the existing Data Operations execution boundary with explicit task and asset evidence semantics.
---

## Approach

Keep orchestration as a two-task Airflow adapter. A framework-independent configuration converter creates the final `DataOperationRequest` from supported runtime overrides, environment values and request defaults. The raw task calls `load_raw_data()`. The analytics task calls `run_dbt_build()` and, only after a successful candidate result, calls `promote_dbt_artifacts()`. Airflow task state and logical asset update evidence are emitted independently; domain result objects are not transported between tasks.

## Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Airflow DAG | Task dependency, runtime policy, task state and logical asset identity | Ingestion, dbt execution, promotion, reliability lifecycle or recovery |
| Configuration adapter | Supported override precedence and `DataOperationRequest` construction | Domain validation rules or Airflow-specific business logic |
| Data Operations | HMDA load, dbt process, candidate artifact verification and current projection promotion | Full-pipeline orchestration or task transport |
| Reliability | Evidence contracts, incident lifecycle, approval, recovery and evaluation | Data-plane DAG execution |

## Decisions

### D1. Use one manual, non-retrying data-plane DAG

- **Decision:** Configure one DAG with `schedule=None`, `catchup=False`, `max_active_runs=1` and `retries=0`.
- **Rationale:** Preserve the migration boundary and exclude scheduling, retry and distributed execution features.
- **Trade-off:** Operational retry and scheduling remain explicit external concerns after this migration.

### D2. Use Airflow public authoring interfaces

- **Decision:** New DAG code uses `airflow.sdk` and TaskFlow tasks. No legacy internal import path, custom operator, plugin or executor is introduced.
- **Rationale:** Keep the adapter on the supported public authoring surface and minimize framework coupling.

### D3. Keep task payloads out of XCom

- **Decision:** Each task reconstructs the request from the runtime configuration adapter. Request and domain result objects, tables and frames are not returned as task payloads.
- **Rationale:** Avoid serializing domain state and make the dependency edge, rather than object transport, the execution contract.

### D4. Emit asset evidence only for completed data updates

- **Decision:** Define stable logical raw and analytics assets. A successful raw task may emit raw update evidence. The analytics task emits analytics update evidence only after dbt build and promotion complete successfully; skip and failure emit no analytics update evidence.
- **Rationale:** A task state is not proof that a data asset changed, and a skipped or failed analytics stage must not appear current.

### D5. Resolve dependencies without applying Airflow constraints globally

- **Decision:** Use Airflow 3.3.0 official constraints to validate the clean Airflow installation, then let the project resolver choose the final shared graph without those constraints. The locked graph must retain Airflow and satisfy `uv pip check`.
- **Rationale:** The official constraints pin `pathspec==1.1.1`, while the current dbt graph requires `<1.1`; the tested unconstrained project graph converges on `pathspec==1.0.4`, which satisfies Airflow's package requirement and dbt's requirement.
- **Trade-off:** The final lock is not an Airflow constraints file and requires explicit graph, import and runtime validation.

## Verification

Validate the adapter at four boundaries: DAG parse structure, configuration conversion, task execution semantics and Airflow runtime bootstrap. The execution matrix must observe raw success/failure, dbt disabled skip, dbt failure, promotion failure and invalid request behavior. Evidence assertions must distinguish task state from logical asset update evidence. Dependency validation must confirm the locked versions, `uv sync --locked`, core imports, `dbt --version`, pytest collection, focused orchestration tests and a local SQLite Airflow database bootstrap.

## Risks

- A future unconstrained resolver update could change shared dependency versions; review the lock diff and rerun the full dependency/import gate with each lock change.
- Airflow parse-time imports can accidentally perform file, database or process I/O; keep all domain calls inside task bodies and test module import separately.
- Promotion or asset-event ordering can falsely report analytics success; test both post-build promotion failure and the absence of analytics update evidence.

## Migration

- Add the Airflow dependency and regenerate the lock using the validated shared-graph strategy.
- Add the configuration adapter and Airflow DAG under the existing orchestration domain.
- Replace Dagster-focused tests and active references only after the Airflow structure and execution matrix pass.
- Update the canonical capability Specs and durable documentation; do not alter archive or historical inbox artifacts.
