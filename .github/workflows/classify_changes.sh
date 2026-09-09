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
tests=false
toml=false
python=false
lefthook=false
routes=false
full_unit=false
full_type=false
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
    openspec/changes/archive/*)
      openspec=true
      openspec_archived=true
      ;;
    openspec/*)
      openspec=true
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
      add_target tests/test_ci_classifier.py
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
  echo "tests=$tests"
  echo "toml=$toml"
  echo "python=$python"
  echo "lefthook=$lefthook"
  echo "routes=$routes"
  echo "full_unit=$full_unit"
  echo "full_type=$full_type"
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
