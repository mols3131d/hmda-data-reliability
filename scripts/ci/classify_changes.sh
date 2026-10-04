#!/usr/bin/env bash
# 저장소 루트에서 변경 경로를 검증 선택 값과 테스트 대상으로 분류한다.
# 기본 입력은 HEAD^1과 HEAD의 차이이며, --stdin은 줄 단위 경로 입력을 받는다.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/classify_openspec.sh"

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
		git -c core.quotePath=false diff --name-only HEAD^1 HEAD
	fi
}

# 비교 실패가 반복문의 입력 처리에 가려지지 않도록 먼저 성공 여부를 확인한다.
paths=$(get_paths)

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

# 이 모드는 현재 존재하는 Markdown 경로만 출력하고 검증 선택 값은 출력하지 않는다.
if [[ "$list_markdown_paths" == "true" ]]; then
	while IFS= read -r path; do
		[[ -z "$path" ]] && continue
		[[ -f "$path" ]] || continue
		is_markdown_validation_path "$path" && printf '%s\n' "$path"
	done <<<"$paths"
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
tach=false
full_unit=false
full_tests=false
full_type=false
openspec_spec_targets=()
openspec_change_targets=()
targets=()
ci_targets=()
type_targets=()

# 대상 배열은 최초 선택 순서를 유지하면서 중복을 제거한다.
add_target() {
	local target="$1"
	local existing
	for existing in "${targets[@]}"; do
		[[ "$existing" == "$target" ]] && return
	done
	targets+=("$target")
}

# 전체 unit 검사에서도 CI의 non-unit 계약 검사가 빠지지 않도록 별도로 기록한다.
add_ci_target() {
	local target="$1"
	local existing
	for existing in "${ci_targets[@]}"; do
		[[ "$existing" == "$target" ]] && return
	done
	ci_targets+=("$target")
	add_target "$target"
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
	[[ -d "src/hmda_reliability/$domain" ]] &&
		add_type_target "src/hmda_reliability/$domain"
	[[ -d "tests/$domain" ]] && add_type_target "tests/$domain"
}

# 변경 domain뿐 아니라 영향을 받는 consumer의 테스트와 타입 검사도 선택한다.
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

	# 하나의 경로가 여러 검증을 요구할 수 있으므로 검증 종류별 조건은 독립 적용한다.
	case "$path" in
	.rulesync/rules/* | .rulesync/skills/*/SKILL.md | rulesync.jsonc | rulesync.lock | skills-lock.json | .agents/route/* | scripts/agent_routes/*)
		routes=true
		;;
	esac

	case "$path" in
	*.json | *.jsonc)
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
	*.py | .python-version | pyproject.toml | uv.lock)
		python=true
		;;
	esac

	case "$path" in
	.python-version | tach.toml | pyproject.toml | uv.lock | src/*.py | tests/scripts/test_tach*.py | tests/review_ai/test_dependency_boundaries.py)
		tach=true
		;;
	esac

	# Spec 문서도 실행 테스트를 선택하므로 일반 Markdown 처리를 끝내기 전에 분류한다.
	classify_openspec_path "$path"

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
	.python-version | pyproject.toml | uv.lock)
		tests=true
		runtime_smoke=true
		full_unit=true
		full_type=true
		;;
	dbt/*.sql | dbt/*.yml | dbt/*.yaml)
		tests=true
		for target in dbt data_operations reliability orchestration; do
			add_target "tests/$target"
		done
		;;
	.github/workflows/* | scripts/ci/*)
		# CI 자체 변경은 계약 테스트로 보호하되 무관한 domain 검증까지 넓히지 않는다.
		tests=true
		add_ci_target tests/scripts/ci
		;;
	scripts/agent_routes/*.py)
		add_focused_test tests/scripts/test_generate_agent_routes.py
		add_type_target scripts/agent_routes
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
	scripts/biome.py | scripts/tombi.py)
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
		shared | configs | utils)
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
	tests/scripts/ci/test_ci_classifier_openspec.py | tests/scripts/ci/test_ci_classifier_python.py)
		[[ -f "$path" ]] && {
			tests=true
			add_target "$path"
		}
		;;
	tests/scripts/ci/test_*.py)
		[[ -f "$path" ]] && {
			tests=true
			add_ci_target "$path"
		}
		;;
	tests/scripts/ci/*.py | tests/scripts/__init__.py)
		tests=true
		add_ci_target tests/scripts/ci
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
		data_operations | data_platform | dbt | hmda_data | orchestration | reliability | review_ai | runtime_ai)
			add_target "tests/$domain"
			;;
		*)
			full_unit=true
			full_type=true
			;;
		esac
		;;
	src/hmda_reliability/* | tests/*)
		tests=true
		full_unit=true
		full_type=true
		;;
	*.py)
		full_type=true
		;;
	esac
done <<<"$paths"

# Actions가 소비하는 key=value 형식을 유지하며 지정한 출력 파일에는 이어 쓴다.
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
	echo "tach=$tach"
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
	printf 'ci_targets='
	printf '%s ' "${ci_targets[@]}"
	echo
	printf 'type_targets='
	printf '%s ' "${type_targets[@]}"
	echo
}

if [[ -n "$output_target" ]]; then
	write_outputs >>"$output_target"
else
	write_outputs
fi
