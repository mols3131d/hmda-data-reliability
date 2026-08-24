# Documentation

Docstring과 comment는 같은 설명문이 아니다. 독자와 정보 수명이 다르다.

## Two Readers

| Reader | Primary surface | Needs |
| --- | --- | --- |
| Caller | name, signature, type, docstring, call site | 무엇을 믿고 사용할 수 있는지 |
| Maintainer | code, names, local comment, tests | 왜 이 구현·제약·순서가 필요한지 |

코드와 이름이 스스로 설명할 수 있는 정보는 prose로 반복하지 않는다.

## Docstrings

Docstring은 caller contract를 보완할 때 사용한다. 특히 다음 의미가 name, signature, type만으로 드러나지 않을 때 가치가 있다.

- 결과나 input/output의 비자명한 domain semantics
- precondition, ordering 또는 approval requirement
- caller가 처리해야 하는 exception
- externally visible 또는 destructive side effect
- 반복 호출, idempotency, overwrite, caching 같은 호출 의미

피한다:

- 함수 이름을 문장으로 다시 쓰기
- type annotation을 Args/Returns prose로 반복하기
- 내부 알고리즘 순서 설명하기
- caller가 의존하지 않는 미래 확장 설명하기

```python
# Weak
def load_partition(path: Path) -> LoadResult:
    """Load a partition from the given path."""

# Useful
def load_partition(path: Path) -> LoadResult:
    """Load one partition, replacing an existing load for the same partition key."""
```

## Comments

Comment는 code-local 이유를 설명한다.

좋은 대상:

- policy 또는 invariant의 로컬 적용 이유
- 비자명한 예외 처리 이유
- 순서가 중요한 이유
- 외부 시스템 제약
- 의도적으로 특이한 구현 선택의 이유

피한다:

- 다음 줄이 무엇을 하는지 설명
- 이름과 같은 내용을 반복
- 변경 이력·토론을 현재 규칙처럼 기록
- 더 명확한 이름이나 구조로 해결 가능한 혼란

```python
# Weak
# Validate the result.
validate(result)

# Useful
# Cleanup failure must not replace the original ingestion result or exception.
cleanup_staging()
```

## Contract Projection

DRY는 중요한 caller contract를 외부 문서에만 숨기는 이유가 아니다.

- 넓은 architecture·domain policy는 canonical 문서가 소유한다.
- API 사용에 필요한 precondition, destructive side effect, overwrite/idempotency 의미는 API 가까이에 최소한으로 남긴다.
- canonical 용어를 사용하고 새 동의어나 병렬 정의를 만들지 않는다.

즉, 넓은 정책을 복제하지 말고 **호출에 필요한 부분만 projection**한다.

## Final Pass

설명을 추가한 뒤 확인한다.

- 이름이나 구조 개선으로 prose를 없앨 수 있는가?
- 실제 caller 또는 maintainer가 이 정보를 필요로 하는가?
- 더 안정적인 owner에 있어야 할 넓은 정책을 복제했는가?
- 코드가 바뀌면 쉽게 거짓말이 될 설명인가?

불필요하거나 쉽게 stale 되는 설명은 줄이거나 제거한다.
