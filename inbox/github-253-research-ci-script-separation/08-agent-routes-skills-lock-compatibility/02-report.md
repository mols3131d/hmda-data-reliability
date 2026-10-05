---
type: report
title: Agent Routes Implementation Results
description: PR 253 route 번들의 최종 로컬 구현, 검증한 파일 identity, 실제 Skills lock 실행 결과와 delivery 제한을 확인할 때 사용한다.
---

# Agent Routes Implementation Results

아래 초기 구현·검증·delivery 기록은 HEAD `cf9c1384bdd9c8c8cedc01c001f0806095ff766e` 당시 snapshot이다. 현재 PR의 필수 보완과 로컬 검증은 [2026-10-05 Merge Preparation](#2026-10-05-merge-preparation)을 따른다.

> [!IMPORTANT]
> 로컬 구현과 독립 리뷰를 완료했다. 최종 관련 suite는 178개 통과, 범위 밖 문서 이동에 따른 2개 실패다. 새 구현의 원격 CI는 실행하지 않았으며 commit·push·PR 수정도 수행하지 않았다.

## Implementation

[승인 계획](00-plan.md)에 따라 기존 단일 generator를 [scripts/agent_routes](../../../scripts/agent_routes/)의 metadata·sources·indexes·module CLI로 분리했다. 유일한 실행 경로는 `python -m scripts.agent_routes`다. 기존 `scripts/generate_agent_routes.py`는 삭제했고 wrapper, 옛 import re-export와 실행 alias를 남기지 않았다.

[Agent Assets](../../../scripts/agent_assets.py), [CI workflow](../../../.github/workflows/ci-lite.yml), [classifier](../../../scripts/ci/classify_changes.sh), 기존 테스트와 [현행 안내](../../../.rulesync/README.md)를 함께 이전했다. 번들 내부의 Python 변경은 route 검증, 기존 generator 테스트와 번들의 type check를 선택한다. 기존 bootstrap 실행 순서와 실패 우선순위는 유지했다.

[Sources](../../../scripts/agent_routes/sources.py)는 실제 Skills CLI version 1 lock의 optional `ref`·`skillPath`를 처리한다. 실제 commit의 archive에서 정확한 Skill 이름과 전체 폴더 `computedHash`를 검증한 뒤 immutable raw URL을 생성한다. Hash를 revision으로 취급하거나 `main`·경로를 추측하지 않는다. 이름 부재·중복, hash 불일치와 조회 실패는 실패로 남는다. Version과 hash가 없는 기존 explicit ref/path 입력은 보존한다. Vendor 계약과 역사적 내용 복원의 한계는 [Research](01-research.md)가 소유한다.

독립 리뷰의 세 finding을 기존 테스트에서 재현하고 수정했다. 검증된 경로의 예약문자는 URL path로 인코딩하고, explicit path가 있어도 이름 유일성을 검사한다. HTTP 전송 중단은 조회 오류 `2`로 처리하며 `--check`는 기존 route를 쓰지 않는다. 상세 판정과 비차단 coverage 한계는 [Review](03-review.md)에 기록했다. 현재 작업 트리의 generated route는 변경하지 않았다.

## Verification

Python 3.13.13의 repository 가상환경에서 실행했다. 아래 결과는 구현 담당자가 실행한 근거이며 리뷰어의 독립 실행 결과가 아니다.

| Check | Result | Evidence |
| --- | --- | --- |
| 기존 generator baseline | Pass | 구조 변경 전 기존 15개 테스트 통과. 실제 lock은 `incomplete Skills CLI lock entry: langfuse`로 실패했다. |
| Bundle-only migration | Pass | lock 수정 전 관련 57개 테스트와 CI no-project check 통과. |
| Review regressions | Pass | 경로 identity·explicit path 중복 검사 2개와 HTTP 읽기 2개를 수정 전 실패로 재현. 수정 후 경로/중복 2개, commits·archive·metadata 전송 중단 3개 통과. |
| 최종 관련 suite | Partial | 아래 pytest command에서 180개 중 178개 통과, 2개 범위 밖 실패. generator 33개와 Agent Assets 6개는 모두 통과했다. |
| Ruff check and format | Pass | 아래 5개 경로에 check와 format `--check` 통과. |
| Type check | Pass | 같은 5개 경로에 `ty check` 통과. HTTP fixture는 실제 `socketpair`와 `HTTPResponse`를 사용한다. |
| Editor diagnostics | Pass | 변경된 Python 파일에 새 진단 없음. |
| 현재 repository route check | Pass | CI no-project `--check` exit 0. 현재 branch에는 실제 Skills CLI lock이 없으므로 이것만으로 호환성을 주장하지 않는다. |
| 실제 lock 격리 생성/check | Pass | 아래 actual-lock 시나리오에서 최종 소스로 생성·check 각각 exit 0. |
| Diff whitespace | Pass | `git diff --check` 통과. |
| Markdown and Inbox artifacts | Pass | 현행 README와 08번 문서의 rumdl check 통과. Native validator 규칙으로 nested 문서 네 개의 frontmatter와 이름도 직접 검증했다. |
| Independent review | Clear | 두 차례 `changes_required` 이후 admitted finding 수정, 최종 fresh review `clear`. |
| 원격 Actions | Not Verified | 새 구현을 push하거나 원격 CI를 실행하지 않았다. |

```bash
uv run --no-sync pytest tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py tests/scripts/ci -q
uv run --no-sync ruff check scripts/agent_routes scripts/agent_assets.py tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py tests/scripts/ci/test_ci_classifier_python.py
uv run --no-sync ruff format --check scripts/agent_routes scripts/agent_assets.py tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py tests/scripts/ci/test_ci_classifier_python.py
uv run --no-sync ty check scripts/agent_routes scripts/agent_assets.py tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py tests/scripts/ci/test_ci_classifier_python.py
uv run --no-project --with 'PyYAML==6.0.3' python -m scripts.agent_routes --check
git diff --check
```

### Actual Lock Scenario

[PR #251 head](https://github.com/mols3131d/hmda-data-reliability/commit/7171e88719ae1c97ed7c1c7423363536ca93316c)의 version 1 `langfuse/skills` entry를 사용했다. `computedHash`는 `14afde211553546dc280bbdd25feff7d20b64b17f7c5d0976db192f5998b3709`이며 ref/path는 없다. `/tmp`의 임시 repository에 최종 bundle과 해당 lock만 두고 `PYTHONPATH`, `UV_ENV_FILE`, `GH_TOKEN`, `GITHUB_TOKEN`을 제거한 환경에서 위 no-project 명령의 생성 모드와 check 모드를 각각 실행했다. 실제 GitHub 조회를 사용했고 두 명령 모두 0을 반환했다. 임시 입력은 실행 종료 후 제거했다.

결과 Skill은 `langfuse`이며 source는 [검증한 commit의 metadata](https://raw.githubusercontent.com/langfuse/skills/b86532b77f16f1e27c7cffa32bb632aa3cd9a352/skills/langfuse/SKILL.md)다. 이 live 결과는 현재 upstream snapshot에 관한 근거이며 과거 revision 복원이나 향후 upstream 변경 후 성공을 보장하지 않는다. 외부 Skill을 현재 작업 트리에 설치하지 않았다.

### Out-of-Scope Failures

[기존 Markdown classifier 테스트](../../../tests/scripts/ci/test_ci_classifier.py)의 다음 두 사례는 병행 07번 문서 작업에서 삭제한 `docs/development/ci.md`를 여전히 입력으로 사용해 실패했다. Baseline HEAD에는 이 문서가 존재한다. Route 수정의 회귀나 baseline 자체의 실패로 분류하지 않았으며 다른 participant의 변경을 되돌리지 않았다.

- `test_changed_markdown_paths_are_selected[docs/development/ci.md]`
- `test_markdown_path_selection_stays_within_changed_scope`

## Exact State

Owning branch는 `agent/research-ci-script-separation`, baseline과 변경되지 않은 HEAD는 `cf9c1384bdd9c8c8cedc01c001f0806095ff766e`다. 변경은 uncommitted이므로 HEAD만으로 구현 상태를 식별할 수 없다. 아래 SHA-256은 마지막 소스·테스트 변경과 formatting 이후 구현 담당자가 계산했으며 최종 reviewer에게 전달한 대상이다. 08번 문서와 병행 07번 변경은 implementation fingerprint에서 제외한다.

| File | SHA256 |
| --- | --- |
| [.github/workflows/ci-lite.yml](../../../.github/workflows/ci-lite.yml) | `36c520b47a316cef81d405fe9d80672551f717106fe7e9ca2df4932ac6b420ed` |
| [.rulesync/README.md](../../../.rulesync/README.md) | `365436afd16595131b50f84c85937be2932fbba217d59b5852ec302a3e86cb2b` |
| [scripts/agent_assets.py](../../../scripts/agent_assets.py) | `7d2fdda5802590663e8a1b53d9932c6a2f32a4750e8b6901707de679771c2c1c` |
| [scripts/ci/classify_changes.sh](../../../scripts/ci/classify_changes.sh) | `9af0310edae3a3269e3d8ea4996dbf890bafbb5940e9db6d66790c38cba93d5e` |
| [scripts/agent_routes/__init__.py](../../../scripts/agent_routes/__init__.py) | `a30f04e41eebbec4be71db52d927398cf292cfcb41205723e4388683a6d2b2af` |
| [scripts/agent_routes/__main__.py](../../../scripts/agent_routes/__main__.py) | `d71975da6b9687fd3f6703069bd8053a74261cac2db17a50afe03a1cdc52a9a0` |
| [scripts/agent_routes/metadata.py](../../../scripts/agent_routes/metadata.py) | `36b5e3fa818e9d30a8849658ab9700966c6fc406c26c3fef833c13b9cf2c093c` |
| [scripts/agent_routes/sources.py](../../../scripts/agent_routes/sources.py) | `1a77579fc8d64a1bd92b9cc93a5d0ec2a67d17bb79d0b73221db2e71a3bd548e` |
| [scripts/agent_routes/indexes.py](../../../scripts/agent_routes/indexes.py) | `e564cbec4c84b1f0f0b31c638f9f12828fbc825848b8eb1234c219c3efb373f1` |
| [tests/scripts/test_generate_agent_routes.py](../../../tests/scripts/test_generate_agent_routes.py) | `45652df58358c54c25e52fd66c20fc8c387120117f198fdbef90a28dc46cd4ca` |
| [tests/scripts/test_agent_assets.py](../../../tests/scripts/test_agent_assets.py) | `9f90b17b451a954e6eef5dfc7bbb15870003e711671a9bc91f253b5ccc787f6f` |
| [tests/scripts/ci/test_ci_classifier_python.py](../../../tests/scripts/ci/test_ci_classifier_python.py) | `3c45645b14936d92367930c7d5c72f21dfdbac4b6b34da676738904b7fd72f69` |

## Delivery Boundary

Commit·push·PR 本문 갱신·Ready 전환·merge는 수행하지 않았다. 기존 PR 본문의 Skills lock 제외 항목은 추후 승인된 delivery에서 실제 추가 scope와 맞춰야 한다. 원격 전체 CI 성공은 prospective merge 상태에서 별도 확인해야 하며, 병행 문서 변경의 두 실패는 해당 작업 owner가 해결할 사항이다.

## 2026-10-05 Merge Preparation

사용자는 PR #253의 병합 가능한 품질을 요청하고 delivery 범위를 **로컬 보완·검증만**으로 선택했다. Base는 `5532dca2fd93696d40ba870471fa2359c5662335`, HEAD는 `ec81d5d3abb27b036a50ed79e73b18565199f394`다. 전체 PR와 로컬 F2 문서의 독립 리뷰는 `changes_required`였으며, R1 한 건을 `current_required`로 채택했다. 과거 `clear` 판정은 이번 보완 상태의 리뷰를 대신하지 않는다.

### Root Blob Lock

Skills CLI `1.7.0`의 [공식 npm 배포본](https://registry.npmjs.org/skills/-/skills-1.7.0.tgz)을 직접 읽었다. `tryBlobInstall()`은 ref가 없을 때만 실행되며 root Skill snapshot에서 `SKILL.md`만 남긴다. `runAdd()`는 성공한 설치의 `snapshotHash`를 project lock의 `computedHash`에 기록하며 `skillPath: SKILL.md`도 기록할 수 있다. 기존 parser는 root에서도 저장소 전체를 hash해 정상 blob lock을 거부했다. 정상 입력 회귀는 수정 전 `Skills CLI hash mismatch: alpha`로 실패했고 변경된 Skill 내용 거부는 통과했다.

[Source parser](../../../scripts/agent_routes/sources.py)는 전체 폴더 hash를 먼저 검증하고, ref가 없고 확인한 vendor 허용 owner인 `vercel`, `vercel-labs`, `heygen-com`, `remotion-dev` 또는 `zapier/connectors`의 root Skill일 때만 단일 파일 hash도 인정한다. Optional `skillPath`가 있어도 지원한다. 다른 source, 명시적 ref와 nested Skill의 전체 폴더 검증은 완화하지 않는다. Lock에는 blob·clone 설치 방식이 기록되지 않으므로 ref 없는 허용 source의 root는 두 vendor hash를 구별 없이 검증한다. 이 한계는 임의 hash 허용이나 내용 검증 생략을 뜻하지 않는다.

### Local Validation

Python 3.13.13의 기존 repository 환경에서 실행했다. 외부 Skill을 설치하거나 실제 network를 테스트에 사용하지 않았다.

| Check | Observed Result |
| --- | --- |
| 수정 전 관련 기준선 | CI·route·Agent Assets 200 passed |
| Root blob RED | 정상 입력 1 failed, 변경 내용 거부 1 passed; collection·fixture 오류 아님 |
| Root·nested 경계 | Blob의 path 유무·허용 source, root clone 성공·변경 거부, clone-only 입력과 nested 폴더 변경 거부: 12 passed |
| 최종 관련 suite | 아래 command로 211 passed; 이전 문서 경로 실패는 이미 전달된 수정으로 해소됨 |
| 변경 Python 정적 검사 | Ruff lint·format `--check`, ty, editor diagnostics 통과 |

```bash
uv run --no-sync pytest tests/scripts/ci tests/scripts/test_generate_agent_routes.py tests/scripts/test_agent_assets.py -q -p no:sugar -p no:cacheprovider --color=no --tb=short
uv run --no-sync ruff check scripts/agent_routes/sources.py tests/scripts/test_generate_agent_routes.py
uv run --no-sync ruff format --check scripts/agent_routes/sources.py tests/scripts/test_generate_agent_routes.py
uv run --no-sync ty check scripts/agent_routes/sources.py tests/scripts/test_generate_agent_routes.py
```

최종 로컬 implementation identity는 아래와 같다. 이 실행 결과와 새 독립 판정은 구분하며, 원격 CI 성공으로 간주하지 않는다.

| File | SHA256 |
| --- | --- |
| [scripts/agent_routes/sources.py](../../../scripts/agent_routes/sources.py) | `df4a2dff66c989df346931326c1bad891fad56a78b13e422192953b9efde58fc` |
| [tests/scripts/test_generate_agent_routes.py](../../../tests/scripts/test_generate_agent_routes.py) | `f5d3ce3e5f892566b249d254c5216291e254d64a8e045e0a5633a6f7bbe7b048` |

최종 로컬 여섯 파일 snapshot의 fresh `review-lead` 판정은 **`clear`**다. Quality·adversarial 검토를 통합해 R1 해소와 신규 필수 finding 부재를 확인했다. 이는 전체 PR 최초 리뷰 이후 변경한 보완 범위의 독립 판정이며 GitHub approval이나 merge 허가는 아니다. Reviewer는 소스·vendor·테스트·문서를 대조하고 editor diagnostics를 확인했지만, 위 pytest·Ruff·ty·Markdown 실행과 SHA-256 계산은 구현 담당자의 제공 근거이며 독립 재실행하지 않았다.

비차단 `follow_up`은 설치 provenance 강화다. Vendor hash는 구분자 없이 경로와 파일 바이트를 연결하므로 ref 없는 허용 root에서 서로 다른 blob·clone 파일 구성이 같은 해시 입력을 만들 수 있다. 추가 설치 방식·원본 revision 계약 없이는 두 형식을 구별할 수 없으며, 리뷰는 이 별도 requirement를 이번 필수 보완으로 확대하지 않았다. 해당 구성은 정적 추론이고 런타임 재현은 하지 않았다.

### Delivery Status

Commit·push·PR 본문 갱신·Ready 전환·승인·merge는 수행하지 않았다. 최신 성공한 원격 [CI run 37216063423](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37216063423)은 위 HEAD와 base의 prospective merge `0b02ef08a69e2e5b1992fb5dffe579a605e04f3e`를 검증했으며 이번 미커밋 보완은 포함하지 않는다. 이후 delivery를 승인하면 새 head의 CI를 별도로 확인해야 한다. Branch protection과 적용 rules 조회는 모두 403으로 approval 요구사항이 미확인이고 PR는 Draft다. 환경 분리·F3와 비차단 follow-up은 이번 필수 보완에 포함하지 않았다.
