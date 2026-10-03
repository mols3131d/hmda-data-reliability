#!/usr/bin/env bash

# 직접 실행하지 않고 source로 불러오는 변경 파일 수집 helper다.
# 인자는 결과 배열 이름, base, head, 선택적인 Git 경로 패턴 순서다.
collect_changed_files() {
  local -n collected="$1"
  local base="$2"
  local head="$3"
  shift 3
  local paths path

  # Git 비교 실패는 빈 변경 목록으로 취급하지 않고 호출자에게 전파한다.
  paths=$(git -c core.quotePath=false diff --name-only "$base" "$head" -- "$@") || return
  collected=()
  # 삭제된 파일은 도구 입력에서 제외하고 공백이 포함된 경로는 그대로 유지한다.
  while IFS= read -r path; do
    [[ -f "$path" ]] && collected+=("$path")
  done <<< "$paths"
  return 0
}