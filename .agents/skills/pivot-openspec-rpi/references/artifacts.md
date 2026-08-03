# Artifacts

RPI(Research → OpenSpec → Implement → Review) 아티팩트의 저장 경로, 수명주기, Git 추적 및 참조 규칙의 canonical source다. 다른 RPI reference는 이 규칙을 복제하지 않고 필요할 때 이 문서를 따른다.

## Artifact Operating Model

RPI의 각 Phase에서 소유 및 관리하는 산출물의 상세 규격입니다.

| Phase | Artifact Type | Canonical Path | Git Tracking | relatedArtifacts Rule |
| :--- | :--- | :--- | :---: | :--- |
| **Research** | Research Bundle | `openspec/research/{research-id}/research.md` 또는 `openspec/research/archive/{research-id}/research.md` | **Optional** (보관 승인 시에만) | `OpenSpec change` 또는 `spec` ID만 포함 가능 (리서치/리뷰 자체는 포함 금지) |
| **OpenSpec** | Spec Artifacts | `openspec/changes/{change-id}/`의 `proposal.md`, `design.md`, `tasks.md`; `openspec/specs/` | **Required** (항상 추적) | 연관된 `change-id`만 포함 |
| **Implement** | Source & Test | `src/project_pivot/` 및 `tests/` 하위 소스 코드 및 테스트 파일 | **Required** (항상 추적) | N/A |
| **Review** | Review Report | `openspec/reviews/{change-id}/{sequence}-{review-title}.md` | **Required** (항상 추적) | 연관된 `change-id`만 포함 |

---

## 1. Research Artifact Lifecycle

Research 단계의 산출물은 기본적으로 **번들 디렉토리** 단위로 구성되며, 수명주기에 따라 임시 문서와 보관 문서로 엄격히 구분됩니다.

### 임시 문서 (Temporary Document)

- **목적**: 변경의 요구사항이나 설계 방향성을 파악하기 위한 예비 조사 자료.
- **경로**: `openspec/research/{research-id}/`
- **Git 추적**: `.gitignore`에 의해 자동으로 차단되며 Git 히스토리에 포함하지 않습니다.
- **연결 제한**: 다른 어떠한 아티팩트(OpenSpec change, Review 등)에서도 임시 리서치 경로를 직접 참조하거나 링크를 생성할 수 없습니다.

### 영구 보관 문서 (Archived Document)

- **승격 조건**: 조사의 결과가 아키텍처 결정, 대안 비교 또는 향후 개발 방향에 지속적인 지식 자산으로서의 가치를 지닌다고 판단될 때.
- **승격 절차**:
  1. 에이전트는 리서치 완료 시 사용자(Human)에게 보관을 제안할 수 있습니다.
  1. 사용자의 최종 승인(Research archive gate) 획득 시 번들 디렉토리 전체를 `openspec/research/archive/{research-id}/` 하위로 이동합니다.
  1. 이동한 디렉토리는 Git 추적 대상으로 전환되어 커밋에 포함됩니다.
- **연결 허용**: `archive/` 하위 아티팩트만 OpenSpec 또는 Review 본문에서 일반 Markdown 링크로 참조할 수 있습니다. `relatedArtifacts`에는 Research ID를 넣지 않습니다.

---

## 2. Review Artifact Lifecycle

Review 아티팩트는 구현물과 설계의 정합성을 검증한 독립적 기록물입니다.

- **식별성**: 리뷰 보고서는 `{change-id}` 디렉토리 하위에 위치하여 어떤 변경을 검토했는지 식별합니다.
- **시퀀스 규칙**: 각 리뷰 시도는 3자리 순차 시퀀스 번호(`sequence`, 예: `001`, `002`)를 부여하여 이전 이력과 중복되지 않도록 신규 파일을 생성합니다.
- **보조 문서**: 동일한 리뷰 차수 내에서 추가 데이터나 세부 검증 흔적이 필요할 경우 `openspec/reviews/{change-id}/{sequence}-{review-title}-{extension}.md` 포맷으로 파일명 접미사를 덧붙여 생성합니다.

---

## 3. `relatedArtifacts` Rule

프론트매터(Frontmatter)의 `relatedArtifacts` 리스트는 아티팩트 간 관계 추적성(Traceability)을 위해 사용되며, 작성 시 다음 규칙을 절대 준수해야 합니다.

- **포함 대상**: 오직 **OpenSpec change ID** 또는 **OpenSpec spec ID**만 포함할 수 있습니다.
- **포함 배제**: 리서치(Research) 아티팩트 ID나 리뷰(Review) 아티팩트 ID는 `relatedArtifacts` 리스트에 포함할 수 없습니다.
- **참조 표현**: 보관된 Research 또는 Review와의 관계는 본문 영역(Body)의 일반 Markdown 링크로만 표현합니다. 임시 Research 번들은 어떤 문서에서도 링크하지 않습니다.

---

## 4. Writing & Style Guidelines

모든 아티팩트 작성 시 인간과 에이전트 모두의 가독성을 높이기 위해 다음 스타일 가이드를 준수합니다.

- **Summary/Overview 전면 배치**: 모든 보고서 형태 문서의 시작부에 `Summary` 또는 `Overview` 헤더를 최상위 수준으로 수록합니다.
- **비주얼 컴포넌트 활용**: Mermaid 다이어그램, 테이블, GFM 콜아웃(GFM Callouts), 풋노트, 이모지를 적극적으로 활용하여 텍스트 밀도를 조절합니다.
- **ASCII 시각화 지양**: 흐름도나 상태 기계 등을 텍스트 그래픽(ASCII)으로 나타내지 않고, 반드시 Mermaid 구문을 사용하여 렌더링 호환성을 보장합니다.
