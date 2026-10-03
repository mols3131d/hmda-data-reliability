#!/usr/bin/env bash

# classifier가 source로 불러오는 OpenSpec 분류 정책이며 직접 실행하는 파일이 아니다.
# 호출자의 선택 상태와 대상 배열을 갱신하고 add_focused_test를 함께 사용한다.
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

# 영향 범위를 좁힐 수 없으면 resource 테스트를 제외한 전체 테스트와 타입 검사를 선택한다.
mark_full_test_scope() {
  tests=true
  full_tests=true
  full_unit=true
  full_type=true
}

is_valid_openspec_name() {
  [[ "$1" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

# 같은 capability의 delta를 가진 active Change를 찾고 archive는 탐색에서 제외한다.
add_related_openspec_changes() {
  local capability="$1"
  local change_dir
  local change
  local related_path

  # 검사하는 inventory 경로가 없거나 불안전하면 관련 변경이 없다고 단정하지 않는다.
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

# 알려진 capability는 대응 테스트로 좁히고 미매핑 capability는 전체 검증으로 넓힌다.
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

# canonical Spec, active Change, archive와 공통 설정은 서로 다른 검증 대상을 선택한다.
classify_openspec_path() {
  local path="$1"
  local capability
  local change

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
}