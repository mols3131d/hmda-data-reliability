#!/usr/bin/env bash
set -euo pipefail

output_target="/dev/stdout"
use_stdin=false

for arg in "$@"; do
  case "$arg" in
    --stdin)
      use_stdin=true
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

json=false
markdown=false
tests=false
toml=false
python=false
lefthook=false
routes=false
full_unit=false
targets=()

add_target() {
  local target="$1"
  local existing
  for existing in "${targets[@]}"; do
    [[ "$existing" == "$target" ]] && return
  done
  targets+=("$target")
}

add_domain_closure() {
  local domain="$1"
  local target
  case "$domain" in
    data_platform)
      for target in \
        data_platform hmda_data reliability review_ai \
        data_operations orchestration dbt; do
        add_target "tests/$target"
      done
      ;;
    hmda_data)
      for target in \
        hmda_data reliability review_ai data_operations \
        orchestration dbt; do
        add_target "tests/$target"
      done
      ;;
    data_operations)
      for target in reliability data_operations orchestration; do
        add_target "tests/$target"
      done
      ;;
    reliability)
      for target in \
        reliability review_ai data_operations orchestration; do
        add_target "tests/$target"
      done
      ;;
    review_ai)
      add_target tests/review_ai
      ;;
    runtime_ai)
      for target in runtime_ai review_ai; do
        add_target "tests/$target"
      done
      ;;
    orchestration)
      add_target tests/orchestration
      ;;
    *)
      full_unit=true
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

  if [[ "$path" == *.md ]]; then
    [[ -f "$path" ]] && markdown=true
    continue
  fi

  case "$path" in
    lefthook.yml)
      lefthook=true
      ;;
    .python-version|pyproject.toml|uv.lock)
      tests=true
      full_unit=true
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
      tests=true
      add_target tests/test_generate_agent_routes.py
      ;;
    scripts/agent_assets.py)
      tests=true
      add_target tests/test_agent_assets.py
      ;;
    scripts/_commands.py|scripts/bootstrap.py|scripts/biome.py|scripts/tombi.py)
      tests=true
      add_target tests/test_commands.py
      ;;
    scripts/generate_docs_indexes.py)
      tests=true
      add_target tests/test_generate_docs_indexes.py
      ;;
    scripts/log_agent_event.py)
      tests=true
      add_target tests/test_log_agent_event.py
      ;;
    scripts/run_actual_source.py)
      tests=true
      add_target tests/hmda_data/eda/test_eda_evidence.py
      ;;
    scripts/run_agentic_review_live.py)
      tests=true
      add_target tests/review_ai/test_live_harness.py
      ;;
    scripts/*.py)
      tests=true
      full_unit=true
      ;;
    src/hmda_reliability/logger.py)
      tests=true
      add_target tests/test_log_agent_event.py
      ;;
    src/hmda_reliability/*/*)
      tests=true
      domain="${path#src/hmda_reliability/}"
      domain="${domain%%/*}"
      case "$domain" in
        shared|configs|utils)
          full_unit=true
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
          ;;
      esac
      ;;
    src/hmda_reliability/*|tests/*)
      tests=true
      full_unit=true
      ;;
  esac
done < <(get_paths)

{
  echo "json=$json"
  echo "markdown=$markdown"
  echo "tests=$tests"
  echo "toml=$toml"
  echo "python=$python"
  echo "lefthook=$lefthook"
  echo "routes=$routes"
  echo "full_unit=$full_unit"
  printf 'targets='
  printf '%s ' "${targets[@]}"
  echo
} >> "$output_target"
