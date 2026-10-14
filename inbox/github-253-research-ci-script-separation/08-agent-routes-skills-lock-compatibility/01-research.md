---
type: research
title: Agent Routes Lock Contract
description: 실제 Skills CLI lock의 revision·경로·hash 의미를 조사해 route 생성의 호환성 경계와 최소 수정 방향을 판단한다.
---

# Agent Routes Lock Contract

> [!IMPORTANT]
> 실패 원인은 CI 실행 방식이 아니라 optional인 `ref`·`skillPath`를 parser가 필수로 요구한 것이다. Version 1 lock은 폴더 hash를 제공하지만 Git commit은 제공하지 않는다. 실제 source revision의 폴더 내용이 hash와 같은 경우에만 immutable URL을 채택할 수 있다.

## Question

Skills CLI의 실제 version 1 lock에서 추측 없이 Skill metadata의 경로와 내용 고정 기준을 얻을 수 있는가?

## Scope

PR #253 branch의 route generator와 직접 소비하는 CLI·Agent Assets·CI·테스트만 조사했다. #251 애플리케이션 코드를 병합하거나 외부 Skill을 현재 작업 트리에 설치하지 않았다.

## Findings

### Actual Lock and CI Failure

현재 확인한 [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)의 head는 `7171e88719ae1c97ed7c1c7423363536ca93316c`다. 앞선 계획에 기록된 revision과 다르지만 [해당 lock](https://github.com/mols3131d/hmda-data-reliability/blob/7171e88719ae1c97ed7c1c7423363536ca93316c/skills-lock.json)은 동일한 version 1 `langfuse` entry를 담는다.

```json
{
  "source": "langfuse/skills",
  "sourceType": "github",
  "computedHash": "14afde211553546dc280bbdd25feff7d20b64b17f7c5d0976db192f5998b3709"
}
```

[CI run 37008116125](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37008116125)의 `Validate chatbot routes` step은 `error: incomplete Skills CLI lock entry: langfuse`로 실패했다. Job `110841105852`의 log를 직접 확인했다. Local 기준 `cf9c1384bdd9c8c8cedc01c001f0806095ff766e`에서도 실제 lock snapshot으로 같은 오류를 재현했다. 기존 15개 generator 테스트는 통과했으므로 실제 형식을 검출하지 못하는 fixture gap이 있었다.

### Vendor Hash Is Not a Revision

조회한 npm `skills` 배포 버전은 `1.7.0`이며 tag revision은 `5b1b4fe90fa9b5809d6db1e0ce97f5d2e3715fdc`다. 공식 [local-lock.ts](https://github.com/vercel-labs/skills/blob/5b1b4fe90fa9b5809d6db1e0ce97f5d2e3715fdc/src/local-lock.ts)는 `ref`와 `skillPath`를 optional로 선언한다. `computedHash`는 폴더 내 regular file을 재귀 수집하고 `.git`·`node_modules` 디렉터리를 제외한 뒤, 상대 경로를 Node.js `localeCompare`로 정렬해 `path + bytes`를 SHA-256에 순서대로 넣은 값이다. GitHub tree SHA인 global lock의 `skillFolderHash`와 다른 값이다.

공식 [add.ts](https://github.com/vercel-labs/skills/blob/5b1b4fe90fa9b5809d6db1e0ce97f5d2e3715fdc/src/add.ts)는 GitHub clone 설치에서 원본 `skill.path`의 hash를 project lock에 기록한다. 따라서 설치된 projection만 읽거나 Markdown 한 파일만 hash하는 것으로 같은 계약을 증명할 수 없다.

### Restore Does Not Locate Historic Content

공식 [install.ts](https://github.com/vercel-labs/skills/blob/5b1b4fe90fa9b5809d6db1e0ce97f5d2e3715fdc/src/install.ts)와 [update-source.ts](https://github.com/vercel-labs/skills/blob/5b1b4fe90fa9b5809d6db1e0ce97f5d2e3715fdc/src/update-source.ts)는 source와 optional ref·path를 재설치 입력으로 만든다. `computedHash`로 과거 commit을 찾지 않는다. Repository wrapper는 `skills@latest`를 사용하므로 이 조사는 관찰한 버전에 한정된다.

### Verified Source Snapshot

GitHub가 반환한 Langfuse default revision `b86532b77f16f1e27c7cffa32bb632aa3cd9a352`의 archive에서 실제 `skills/langfuse/SKILL.md`를 찾았다. 그 폴더의 hash는 #251의 `computedHash`와 같았다. 새 parser에 실제 snapshot을 주입해 다음 [immutable source](https://raw.githubusercontent.com/langfuse/skills/b86532b77f16f1e27c7cffa32bb632aa3cd9a352/skills/langfuse/SKILL.md)를 얻었고, 임시 repository에서 CI no-project 생성과 check가 모두 0을 반환했다.

## Implications

호환성 수정은 “누락 필드를 허용”하는 것만으로 끝나지 않는다. 실제 revision과 이름 기반 경로를 해석한 뒤 폴더 hash를 확인해야 한다. 불일치는 실패로 남기며, hash만으로 과거 revision을 복원한다는 주장은 하지 않는다. 기존 explicit ref/path 입력은 version·hash가 없는 legacy 형식으로 별도 보존한다.

구조 변경은 먼저 metadata·sources·indexes·module CLI로 분리하고 기존 15개 테스트의 동작을 보존했다. 이후 실제 version 1 회귀 테스트를 red→green으로 검증했다. 독립적인 책임별 파일 분리와 schema 수정의 근거를 구분한다.

## Open Questions

GitHub Actions에서 새 구현을 실행하지 않았다. 현재 API rate limit, private source와 upstream 변경 시 정상적인 실패가 가능하며, 원격 전체 CI 성공은 별도 push와 prospective merge 실행을 요구한다.
