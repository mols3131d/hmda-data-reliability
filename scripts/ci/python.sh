#!/usr/bin/env bash
# 저장소 루트와 준비된 locked 환경에서 변경 Python의 lint 및 타입 검사를 실행한다.
# base와 head는 기본 HEAD^1, HEAD이며 타입 검사 범위는 FULL_TYPE과 TYPE_TARGETS로 받는다.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/changed_files.sh"

files=()
collect_changed_files files "${1:-HEAD^1}" "${2:-HEAD}" '*.py'
# lint와 formatting 검사는 현재 존재하는 변경 파일로 한정한다.
if ((${#files[@]})); then
	uv run --no-sync ruff check "${files[@]}"
	uv run --no-sync ruff format --check "${files[@]}"
fi

# 영향 범위가 넓으면 전체 타입 검사를 한 번 실행하고 scoped 검사는 생략한다.
if [[ "${FULL_TYPE:-false}" == true ]]; then
	uv run --no-sync ty check --exclude 'inbox/**'
	exit 0
fi

# domain과 consumer 대상에 변경 파일도 포함해 직접 수정한 코드의 타입 검사가 빠지지 않게 한다.
read -r -a type_targets <<<"${TYPE_TARGETS:-}"
type_targets+=("${files[@]}")
if ((${#type_targets[@]})); then
	uv run --no-sync ty check "${type_targets[@]}"
fi
