# Python Standard Logging

Python 표준 `logging`으로 선택한 log event를 구현하는 기준이다. **무엇을 log할지는 [Logging](logging.md)이 소유하고, 이 문서는 Python 표현만 다룬다.**

이 repository는 Python 3.13을 기준으로 한다. 기존 logger hierarchy와 application-owned configuration을 우선하고 clarification만을 위해 wrapper, handler 또는 logging framework를 만들지 않는다.

## Logger

일반 module은 module 이름 기반 logger를 사용한다.

```python
import logging

_LOGGER = logging.getLogger(__name__)
```

기존 logging helper를 사용하는 영역에서는 동일한 hierarchy를 유지하며 재사용한다.

- `Logger`를 직접 생성하지 않는다.
- root logger에 직접 기록하는 module code를 만들지 않는다.
- runtime value마다 동적인 logger name을 만들지 않는다.

## Configuration Ownership

handler, formatter, destination과 global level은 application/entrypoint가 소유한다.

일반 module code에서는 다음을 피한다.

```python
logging.basicConfig(...)
_LOGGER.addHandler(...)
_LOGGER.setLevel(...)
```

하위 module이 configuration을 고정하면 caller와 framework가 verbosity와 destination을 제어하기 어렵다.

## Message And Context

동적 값을 message에 넣어야 하면 logging argument formatting을 우선한다.

```python
_LOGGER.info("작업 완료: return_code=%s", result.return_code)
```

검색·비교해야 하는 값은 message 문자열에만 숨기지 않고 `extra` 같은 기존 structured context convention을 사용한다.

```python
_LOGGER.info(
    "데이터 적재 완료",
    extra={
        "table_name": "raw.records",
        "source_count": len(paths),
        "row_count": row_count,
    },
)
```

- `extra` key는 기존 `LogRecord` attribute와 충돌시키지 않는다.
- 작은 scalar와 안정적인 identifier를 우선한다.
- `extra` field가 실제 출력되는지는 formatter/handler configuration에 달려 있음을 고려한다.
- 데이터 안전성은 [Evidence](evidence.md#data-safety)를 따른다.

## Exceptions

현재 `except` block에서 traceback과 함께 failure를 기록해야 할 때 `Logger.exception()`을 우선한다.

```python
try:
    run_operation()
except OperationError:
    _LOGGER.exception("operation 실행 실패")
    raise
```

- 같은 exception을 단순히 다시 올리는 모든 layer에서 반복 logging하지 않는다.
- expected rejection이나 domain result를 무조건 exception log로 만들지 않는다.
- lower layer의 context가 충분하면 상위 layer는 새로운 의미를 추가할 때만 log한다.

## Use Advanced APIs Only When Needed

- 반복 context가 실제 중복을 만들 때만 `LoggerAdapter`를 고려한다.
- 기존 logging helper가 caller location을 가리고 실제 위치가 필요할 때만 `stacklevel`을 사용한다.
- `warning()`을 사용하고 deprecated `warn()`은 사용하지 않는다.
- arbitrary numeric level이나 새 logging abstraction을 만들지 않는다.

## Final Check

- logger가 기존 module hierarchy와 일치하는가?
- configuration을 module이 불필요하게 소유하지 않는가?
- event 의미는 `logging.md`를 따르는가?
- structured context가 작고 안정적인가?
- 같은 failure의 traceback을 중복 기록하지 않는가?
- wrapper, adapter, handler가 실제 필요 이상으로 늘어나지 않았는가?

## References

- Python 3.13 `logging` API: <https://docs.python.org/3.13/library/logging.html>
- Python 3.13 Logging HOWTO: <https://docs.python.org/3.13/howto/logging.html>
- Python 3.13 Logging Cookbook: <https://docs.python.org/3.13/howto/logging-cookbook.html>
