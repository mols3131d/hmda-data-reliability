# dbt

`dbt/` 작업에만 필요한 authoring 규칙이다. Capability behavior와 model semantics의 canonical contract는 owning OpenSpec이 소유하며, dbt configuration과 tests는 implementation과 verification evidence로 유지한다.

- `dbt_project.yml`, `models/sources.yml`과 model schema files의 기존 ownership을 재사용하고 같은 설정을 SQL model에 중복하지 않는다.
- Schema 이름은 `generate_schema_name` macro를 통해 결정하며 model에 environment prefix를 hard-code하지 않는다.
- 가능한 경우 ad-hoc SQL test보다 YAML declarative test를 우선한다.
- Grain, null semantics, metric 또는 source contract를 변경하면 owning Spec과 관련 tests를 함께 갱신한다.
