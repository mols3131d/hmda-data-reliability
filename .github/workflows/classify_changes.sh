#!/usr/bin/env bash
set -euo pipefail

output_target=""
use_stdin=false
list_markdown_paths=false

for arg in "$@"; do
  case "$arg" in
    --stdin)
      use_stdin=true
      ;;
    --markdown-paths)
      list_markdown_paths=true
      ;;
    *)
      output_target="$arg"
      ;;
  esac
done

get_paths() {
  if [[ "$use_stdin" == "true" ]]; then
    cat
  else
    git diff --name-only HEAD^1 HEAD
  fi
}

is_markdown_validation_path() {
  local path="$1"

  case "$path" in
    *.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if [[ "$list_markdown_paths" == "true" ]]; then
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    [[ -f "$path" ]] || continue
    is_markdown_validation_path "$path" && printf '%s\n' "$path"
  done < <(get_paths)
  exit 0
fi

json=false
markdown=false
inbox=false
openspec=false
openspec_archived=false
openspec_bulk=false
tests=false
toml=false
python=false
lefthook=false
routes=false
runtime_smoke=false
architecture=false
full_unit=false
full_tests=false
full_type=false
openspec_spec_targets=()
openspec_change_targets=()
targets=()
type_targets=()

add_target() {
  local target="$1"
  local existing
  for existing in "${targets[@]}"; do
    [[ "$existing" == "$target" ]] && return
  done
  targets+=("$target")
}

add_type_target() {
  local target="$1"
  local existing
  for existing in "${type_targets[@]}"; do
    [[ "$existing" == "$target" ]] && return
  done
  type_targets+=("$target")
}

add_focused_test() {
  local target="$1"
  tests=true
  add_target "$target"
  add_type_target "$target"
}

add_openspec_spec_name() {
  local target="$1"
  local existing
  for existing in "${openspec_spec_targets[@]}"; do
    [[ "$existing" == "$target" ]] && return
  done
  openspec_spec_targets+=("$target")
}

add_openspec_change_name() {
  local target="$1"
  local existing
  for existing in "${openspec_change_targets[@]}"; do
    [[ "$existing" == "$target" ]] && return
  done
  openspec_change_targets+=("$target")
}

mark_full_test_scope() {
  tests=true
  full_tests=true
  full_unit=true
  full_type=true
}

is_valid_openspec_name() {
  [[ "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

add_related_openspec_changes() {
  local capability="$1"
  local change_dir
  local change
  local related_path

  if [[ ! -d openspec/changes || -L openspec/changes ]]; then
    mark_full_test_scope
    return
  fi

  for change_dir in openspec/changes/*; do
    [[ -e "$change_dir" || -L "$change_dir" ]] || continue
    if [[ -L "$change_dir" ]]; then
      mark_full_test_scope
      continue
    fi
    [[ -d "$change_dir" ]] || continue

    change="${change_dir##*/}"
    [[ "$change" == archive ]] && continue
    related_path="$change_dir/specs/$capability"

    if [[ -L "$related_path" ]]; then
      mark_full_test_scope
    elif [[ -e "$related_path" && ! -d "$related_path" ]]; then
      mark_full_test_scope
    elif [[ -d "$related_path" ]]; then
      if is_valid_openspec_name "$change"; then
        add_openspec_change_name "$change"
      else
        mark_full_test_scope
      fi
    fi
  done
}

add_openspec_spec_target() {
  local capability="$1"

  case "$capability" in
    data-operations-*)
      add_focused_test tests/data_operations
      ;;
    data-platform-dbt-analytics)
      add_focused_test tests/dbt
      ;;
    data-platform-duckdb-access)
      add_focused_test tests/data_platform
      ;;
    hmda-data-eda-descriptive-evidence)
      add_focused_test tests/hmda_data/eda
      ;;
    hmda-data-ingestion|hmda-data-synthetic-defects)
      add_focused_test tests/hmda_data
      ;;
    orchestration-pipeline)
      add_focused_test tests/orchestration
      add_focused_test tests/data_operations/test_quality_gate.py
      add_focused_test tests/data_operations/test_dbt_runner.py
      add_focused_test tests/reliability/test_quality_gate.py
      ;;
    reliability-agentic-review)
      add_focused_test tests/review_ai
      add_focused_test tests/runtime_ai
      ;;
    reliability-*)
      add_focused_test tests/reliability
      ;;
    *)
      openspec_bulk=true
      mark_full_test_scope
      ;;
  esac

  [[ "$openspec_bulk" == true ]] || add_related_openspec_changes "$capability"
}

add_domain_target() {
  local domain="$1"
  add_target "tests/$domain"
  [[ -d "src/hmda_reliability/$domain" ]] && \
    add_type_target "src/hmda_reliability/$domain"
  [[ -d "tests/$domain" ]] && add_type_target "tests/$domain"
}

add_domain_closure() {
  local domain="$1"
  local target
  case "$domain" in
    data_platform)
      for target in \
        data_platform hmda_data reliability review_ai \
        data_operations orchestration dbt; do
        add_domain_target "$target"
      done
      ;;
    hmda_data)
      for target in \
        hmda_data reliability review_ai data_operations \
        orchestration dbt; do
        add_domain_target "$target"
      done
      ;;
    data_operations)
      for target in reliability data_operations orchestration; do
        add_domain_target "$target"
      done
      ;;
    reliability)
      for target in \
        reliability review_ai data_operations orchestration; do
        add_domain_target "$target"
      done
      ;;
    review_ai)
      add_domain_target review_ai
      ;;
    runtime_ai)
      for target in runtime_ai review_ai; do
        add_domain_target "$target"
      done
      ;;
    orchestration)
      add_domain_target orchestration
      ;;
    *)
      full_unit=true
      full_type=true
      ;;
  esac
}

while IFS= read -r path; do
  [[ -z "$path" ]] && continue

  case "$path" in
    .rulesync/rules/*|.rulesync/skills/*/SKILL.md|rulesync.jsonc|rulesync.lock|skills-lock.json|.agents/route/*|scripts/generate_agent_routes.py)
      routes=true
      ;;
  esac

  case "$path" in
    *.json|*.jsonc)
      [[ -f "$path" ]] && json=true
      ;;
  esac

  case "$path" in
    *.toml)
      [[ -f "$path" ]] && toml=true
      ;;
  esac

  case "$path" in
    scripts/biome.py)
      json=true
      ;;
    scripts/tombi.py)
      toml=true
      ;;
    scripts/bootstrap.py)
      json=true
      toml=true
      ;;
  esac

  case "$path" in
    *.py|.python-version|pyproject.toml|uv.lock)
      python=true
      ;;
  esac

  case "$path" in
    src/*.py|tach.toml|.python-version|pyproject.toml|uv.lock|tests/scripts/test_tach.py|.github/workflows/*)
      architecture=true
      ;;
  esac

  case "$path" in
    openspec/specs/*/*)
      openspec=true
      capability="${path#openspec/specs/}"
      capability="${capability%%/*}"
      if is_valid_openspec_name "$capability" && [[ -d "openspec/specs/$capability" ]]; then
        add_openspec_spec_name "$capability"
        add_openspec_spec_target "$capability"
      else
        openspec_bulk=true
        mark_full_test_scope
      fi
      ;;
    openspec/specs/*)
      openspec=true
      openspec_bulk=true
      ;;
    openspec/changes/archive/*/*)
      openspec=true
      openspec_archived=true
      ;;
    openspec/changes/*/*)
      openspec=true
      change="${path#openspec/changes/}"
      change="${change%%/*}"
      if is_valid_openspec_name "$change" && [[ -d "openspec/changes/$change" ]]; then
        add_openspec_change_name "$change"
      else
        openspec_bulk=true
      fi
      ;;
    openspec/changes/*|openspec/*)
      openspec=true
      openspec_bulk=true
      ;;
  esac

  if [[ "$path" == *.md ]]; then
    if [[ -f "$path" ]] && is_markdown_validation_path "$path"; then
      markdown=true
      [[ "$path" == inbox/* ]] && inbox=true
    fi
    continue
  fi

  case "$path" in
    lefthook.yml)
      lefthook=true
      ;;
    .python-version|pyproject.toml|uv.lock)
      tests=true
      runtime_smoke=true
      full_unit=true
      full_type=true
      ;;
    dbt/*.sql|dbt/*.yml|dbt/*.yaml)
      tests=true
      for target in dbt data_operations reliability orchestration; do
        add_target "tests/$target"
      done
      ;;
    .github/workflows/*)
      tests=true
      add_target tests/scripts/test_ci_classifier.py
      ;;
    scripts/generate_agent_routes.py)
      add_focused_test tests/scripts/test_generate_agent_routes.py
      ;;
    scripts/agent_assets.py)
      add_focused_test tests/scripts/test_agent_assets.py
      ;;
    scripts/_commands.py)
      for target in \
        tests/scripts/test_commands.py tests/scripts/test_tool_wrappers.py \
        tests/scripts/test_bootstrap.py tests/scripts/test_agent_assets.py; do
        add_focused_test "$target"
      done
      add_type_target scripts
      ;;
    scripts/bootstrap.py)
      add_focused_test tests/scripts/test_bootstrap.py
      ;;
    scripts/biome.py|scripts/tombi.py)
      add_focused_test tests/scripts/test_tool_wrappers.py
      ;;
    scripts/generate_docs_indexes.py)
      add_focused_test tests/scripts/test_generate_docs_indexes.py
      ;;
    scripts/validate_inbox_artifacts.py)
      add_focused_test tests/scripts/test_validate_inbox_artifacts.py
      ;;
    scripts/log_agent_event.py)
      add_focused_test tests/scripts/test_log_agent_event.py
      ;;
    scripts/run_actual_source.py)
      add_focused_test tests/hmda_data/eda/test_eda_evidence.py
      ;;
    scripts/run_agentic_review_live.py)
      add_focused_test tests/review_ai/test_live_harness.py
      ;;
    scripts/*.py)
      tests=true
      full_unit=true
      full_type=true
      ;;
    src/hmda_reliability/logger.py)
      tests=true
      add_target tests/scripts/test_log_agent_event.py
      full_type=true
      ;;
    src/hmda_reliability/*/*)
      tests=true
      domain="${path#src/hmda_reliability/}"
      domain="${domain%%/*}"
      case "$domain" in
        shared|configs|utils)
          full_unit=true
          full_type=true
          ;;
        *)
          add_domain_closure "$domain"
          ;;
      esac
      ;;
    tests/test_*.py)
      [[ -f "$path" ]] && {
        tests=true
        add_target "$path"
      }
      ;;
    tests/scripts/test_*.py)
      [[ -f "$path" ]] && {
        tests=true
        add_target "$path"
      }
      ;;
    tests/*/*)
      tests=true
      domain="${path#tests/}"
      domain="${domain%%/*}"
      case "$domain" in
        data_operations|data_platform|dbt|hmda_data|orchestration|reliability|review_ai|runtime_ai)
          add_target "tests/$domain"
          ;;
        *)
          full_unit=true
          full_type=true
          ;;
      esac
      ;;
    src/hmda_reliability/*|tests/*)
      tests=true
      full_unit=true
      full_type=true
      ;;
    *.py)
      full_type=true
      ;;
  esac
done < <(get_paths)

write_outputs() {
  echo "json=$json"
  echo "markdown=$markdown"
  echo "inbox=$inbox"
  echo "openspec=$openspec"
  echo "openspec_archived=$openspec_archived"
  echo "openspec_bulk=$openspec_bulk"
  echo "tests=$tests"
  echo "toml=$toml"
  echo "python=$python"
  echo "lefthook=$lefthook"
  echo "routes=$routes"
  echo "runtime_smoke=$runtime_smoke"
  echo "architecture=$architecture"
  echo "full_unit=$full_unit"
  echo "full_tests=$full_tests"
  echo "full_type=$full_type"
  printf 'openspec_spec_targets='
  printf '%s ' "${openspec_spec_targets[@]}"
  echo
  printf 'openspec_change_targets='
  printf '%s ' "${openspec_change_targets[@]}"
  echo
  printf 'targets='
  printf '%s ' "${targets[@]}"
  echo
  printf 'type_targets='
  printf '%s ' "${type_targets[@]}"
  echo
}

if [[ -n "$output_target" ]]; then
  write_outputs >> "$output_target"
else
  write_outputs
fi
