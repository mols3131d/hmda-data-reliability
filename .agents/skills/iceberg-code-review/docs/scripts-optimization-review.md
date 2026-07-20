# Scripts 최적화 검토

## 핵심 문제

Placeholder 규칙과 template이 충돌한다.

- 현재 parser: 영문, 한글, underscore로 구성된 `{{이름}}`만 인식
- `{{0}}`, `{{...}}`: 인식하지 않음
- 이름 기반 placeholder인 `{{pass_count}}`, `{{another_finding}}`으로 교체 필요

## 우선순위

1. Validation endpoint 통합
2. Placeholder와 template 문법 통일
3. PyYAML 기반 front matter 검증
4. Front matter 분리 로직 공통화
5. 모든 validation 오류를 한 번에 반환
6. `examples/`를 회귀 테스트에 포함
7. 파일 입출력에 UTF-8 명시

## Validation endpoint

단일 CLI와 subcommand 방식 권장.

```text
scripts/
├── validate.py
├── validators.py
├── create_summary.py
├── create_finding.py
└── shared.py
```

```bash
python3 ./scripts/validate.py all review.md
python3 ./scripts/validate.py structure review.md
python3 ./scripts/validate.py frontmatter review.md
python3 ./scripts/validate.py placeholders review.md
python3 ./scripts/validate.py comments review.md
```

Workflow에서는 한 번만 실행한다.

```bash
python3 ./scripts/validate.py all "{review_file_path}"
```

통합 후 `validate_review_file.py`, `validate_no_comments.py`는 제거한다. 별도 `validate_placeholders.py`는 만들지 않는다.

## 추가 검사 후보

실제 불일치가 발생하면 추가한다.

- Summary의 finding link와 상세 파일 일치
- Summary 집계와 상세 finding 수 일치

## 주석 제거

범용 제거 script는 만들지 않는다.

- 보존할 YAML·Markdown comment를 삭제할 위험
- Markdown 간격과 rendering 변경 가능
- Parser 오판 시 내용 손실

LLM이 작성 지침 comment를 제거하고 validator가 잔여 comment를 검사한다.

자동 제거가 필요하면 전용 marker만 대상으로 한다.

```yaml
# iceberg: 작성 후 제거
```

```md
<!-- iceberg: 작성 후 제거 -->
```

## Front matter 검증

타입별 검증은 필요하지만 script를 분리하지 않는다. 하나의 schema map과 PyYAML을 사용한다.

### `code-review-summary`

- 필수: `title`, `date`, `type`
- `date`: `yyyy-MM-dd`

### `code-review-finding`

- 필수: `title`, `description`, `type`, `severity`, `status`
- `severity`: `bug | risk | nit | q`
- `status`: `open | resolved | dismissed`
- `title`: 파일명과 일치

모든 필수 문자열은 빈 값을 허용하지 않는다.

## Template 생성

Template 전체를 Python 문자열로 옮기지 않는다. Markdown template을 유지하고 생성 script가 결정 가능한 값만 치환한다.

- Summary script: `date`
- Finding script: `domain`, `finding`, `status`, `type`
- LLM: `description`, `severity`, `Observation`, `Impact`, `Recommendation`, `Verification`

```text
Markdown template
    생성 script가 결정값 치환
        LLM이 의미 기반 내용 작성
            validate.py all
```

## 결론

`validate.py`와 `validators.py`로 validation을 통합한다. Template은 유지하되 placeholder 문법을 먼저 통일한다. 범용 주석 제거 script는 추가하지 않는다.
