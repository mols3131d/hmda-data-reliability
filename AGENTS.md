# Rules

## Code Style

- **SRP**: Keep functions/classes focused. Extract helpers only to reduce complexity/duplication.
- **One Class per File**: Put major classes/models in individual files (SRP).

## Directory Structure

| Dir | Role |
| --- | --- |
| **`src/`** | Main Python package. |
| **`tests/`** | Test suites by domain. |
| **`dbt/`** | dbt project, models, macros, and generated artifacts. |
| `data/` | DuckDB files, source data, and metadata. |
| `notebooks/` | Marimo notebooks and notebook support files. |
| `docs/` | Public project documentation. |
| `scripts/` | Repository setup and utility scripts. |
| `openspec/` | Change proposals, specifications, and related configuration. |
| `sandboxes/` | Experimental scripts and isolated work areas. |
