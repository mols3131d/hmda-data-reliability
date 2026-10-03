#!/usr/bin/env bash
# classifier가 선택한 SPEC_TARGETS와 CHANGE_TARGETS를 저장소 루트에서 검증한다.
# BULK와 ARCHIVED는 전체 또는 보관된 항목의 검증 여부를 제어한다.
set -euo pipefail

validate=(
  npm exec --yes --package @fission-ai/openspec@1.12.0 --
  openspec validate
)

# 전체 검증이 선택되면 개별 대상을 다시 검증하지 않는다.
if [[ "${BULK:-false}" == true ]]; then
  "${validate[@]}" --all --strict
  exit 0
fi

# 대상 값은 공백으로 구분된 이름이며 canonical Spec과 active Change는 strict로 검증한다.
read -r -a specs <<< "${SPEC_TARGETS:-}"
for target in "${specs[@]}"; do
  "${validate[@]}" "$target" --type spec --strict
done

read -r -a changes <<< "${CHANGE_TARGETS:-}"
for target in "${changes[@]}"; do
  "${validate[@]}" "$target" --type change --strict
done

if [[ "${ARCHIVED:-false}" == true ]]; then
  "${validate[@]}" --archived
fi

# 검증 step이 선택됐는데 대상이 없으면 조용히 성공하지 않고 분류 누락으로 실패한다.
if ((${#specs[@]} == 0 && ${#changes[@]} == 0)) && [[ "${ARCHIVED:-false}" != true ]]; then
  echo "OpenSpec changed paths were not assigned a validation target" >&2
  exit 1
fi