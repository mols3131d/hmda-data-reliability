# Logging

Logging은 runtime clarification의 기본값이 아니다. **시간적 흐름이나 내부 결정이 다른 surface로는 복원되지 않을 때** 사용한다.

## Prefer Existing Logging Surface

- 일반 Python module은 기존 project logger 사용 방식을 따른다.
- framework가 실행 경계를 소유하면 framework-native logger와 metadata를 우선한다.
- library/module code에서 global logging configuration을 새로 설정하지 않는다. 설정은 entrypoint 책임으로 둔다.

새 logger wrapper, handler, formatter 또는 logging dependency는 runtime clarification만을 위해 만들지 않는다.

## Log Events, Not Narration

좋은 log는 사건과 필요한 context를 남긴다.

```python
_LOGGER.debug(
    "HMDA 원천 적재 완료",
    extra={"table_name": table_name, "source_count": count, "row_count": rows},
)
```

피한다.

```python
_LOGGER.debug("이제 파일을 읽기 시작합니다")
_LOGGER.debug("파일을 다 읽었습니다")
_LOGGER.debug("다음 단계로 이동합니다")
```

함수 entry/exit를 기계적으로 기록하지 않는다.

## Context

Message는 사건을 짧게 표현하고, 비교·검색·진단에 필요한 값은 structured context로 둔다.

우선할 수 있는 값:

- operation target 또는 stable identifier
- 선택된 branch/result
- count, status, bounded duration 같은 작은 값
- failure를 특정하는 단계나 대상

전체 request, model dump, raw row, secret, 무제한 stdout/stderr를 `extra`에 넣지 않는다.

## Duplication

같은 failure나 state transition을 여러 계층에서 반복 logging하지 않는다.

- 하위 계층이 충분한 context와 함께 exception을 올리면 상위 계층은 단순 반복 log를 피한다.
- 상위 계층이 새로운 execution boundary나 operator-visible 의미를 추가할 때만 별도 event를 고려한다.
- exception stack이 필요한 경계와 structured error context만 필요한 경계를 구분한다.

## Level

주변 코드와 framework convention을 우선한다. 일반적으로 내부 진단 세부사항은 `debug`, 정상적인 operator-visible 경계 결과는 `info`, 실제 실패는 해당 실패를 소유하는 경계에서 기록한다.

level 선택보다 **event가 필요한가**를 먼저 판단한다.

## Final Check

로그를 추가한 뒤 확인한다.

- 이 event가 없으면 실제로 어떤 질문에 답할 수 없는가?
- 기존 result, metadata 또는 exception context와 중복되는가?
- 반복 실행에서 noise가 과도하지 않은가?
- 값의 크기와 민감도가 안전한가?
- event를 삭제해도 runtime 이해가 유지된다면 삭제한다.
