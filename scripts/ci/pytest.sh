#!/usr/bin/env bash
# 저장소 루트와 준비된 locked 환경에서 classifier가 선택한 테스트를 실행한다.
# FULL_TESTS, FULL_UNIT 순으로 우선하며 TARGETS와 CI_TARGETS는 공백 구분 경로를 받는다.
set -euo pipefail

common=(
	uv run --no-sync pytest
	-q
	-p no:sugar
	--color=no
	--tb=short
	-ra
)

selected_args=()
if [[ "${BOUNDARIES_CHECKED:-false}" == true ]]; then
	selected_args+=(--ignore=tests/review_ai/test_dependency_boundaries.py)
fi

# 전체 non-resource 검사는 CI component 테스트도 포함하므로 추가로 실행하지 않는다.
if [[ "${FULL_TESTS:-false}" == true ]]; then
	"${common[@]}" "${selected_args[@]}" -n auto -m "not memory and not stress"
	exit 0
elif [[ "${FULL_UNIT:-false}" == true ]]; then
	"${common[@]}" -n auto -m "unit and not memory and not stress"
	# unit fallback과 CI 변경이 겹치면 선택된 CI non-unit 계약 검사도 이어서 실행한다.
	read -r -a ci_targets <<<"${CI_TARGETS:-}"
	if ((${#ci_targets[@]})); then
		"${common[@]}" -m "not unit and not memory and not stress" "${ci_targets[@]}"
	fi
	exit 0
fi

# scoped 대상이 셋 이상일 때만 병렬 실행하고 memory와 stress는 모든 분기에서 제외한다.
read -r -a targets <<<"${TARGETS:-}"
if ((${#targets[@]} == 0)); then
	exit 0
elif ((${#targets[@]} >= 3)); then
	"${common[@]}" "${selected_args[@]}" -n auto -m "not memory and not stress" "${targets[@]}"
else
	"${common[@]}" "${selected_args[@]}" -m "not memory and not stress" "${targets[@]}"
fi
