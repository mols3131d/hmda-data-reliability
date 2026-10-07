#!/usr/bin/env bash
# 저장소 루트에서 변경 Markdown을 formatting하고 docs 아래 파일만 lint로 차단한다.
# base와 head 인자를 생략하면 prospective merge의 HEAD^1과 HEAD를 비교한다.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/changed_files.sh"

files=()
collect_changed_files files "${1:-HEAD^1}" "${2:-HEAD}" '*.md'
((${#files[@]})) || exit 0

# formatter 출력은 정보성 진단이지만 도구 자체가 실패하면 nonzero를 그대로 전파한다.
echo "Markdown formatting diagnostics (informational; docs lint runs separately):"
rumdl fmt "${files[@]}"
diff=$(git diff -- "${files[@]}")
# formatting 차이는 disposable 작업 공간의 수정 제안이며 branch에 반영하지 않는다.
if [[ -n "$diff" ]]; then
	echo "Markdown formatting suggestions (non-blocking):"
	printf '%s\n' "$diff"
	if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
		{
			echo "### Markdown formatting suggestions"
			echo
			echo "CI applied safe formatting changes only in its disposable workspace; formatting-only drift does not fail this check."
			echo
			echo '```diff'
			printf '%s\n' "$diff"
			echo '```'
		} >>"$GITHUB_STEP_SUMMARY"
	fi
fi

# docs 밖의 선택된 문서는 formatting만 수행하고 Markdown lint로 병합을 막지 않는다.
docs=()
for path in "${files[@]}"; do
	[[ "$path" == docs/* ]] && docs+=("$path")
done
if ((${#docs[@]})); then
	rumdl check "${docs[@]}"
fi
