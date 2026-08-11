# Python Standard Logging

Python 표준 `logging`을 사용할 때의 구현 기준이다. **무엇을 log할지는 [Logging](logging.md)이 소유하고, 이 문서는 Python에서 그것을 어떻게 표현할지만 다룬다.**

Project Pivot의 runtime은 Python 3.13을 기준으로 한다. 표준 library의 logger hierarchy와 application-owned configuration을 우선하고, clarification만을 위해 별도 logging framework를 만들지 않는다.

## Logger

일반 module은 module 이름 기반 logger를 사용한다.

```python
import logging

_LOGGER = logging.getLogger(__name__)
```

Project Pivot의 기존 helper가 적용되는 영역에서는 동일한 hierarchy를 유지하는 `project_pivot.logger.get_logger()`를 재사용한다.

- `Logger`를 직접 생성하지 않는다.
- root logger에 직접 기록하는 module code를 만들지 않는다.
- request, partition, incident 같은 runtime value마다 새 logger name을 만들지 않는다.
- logger name은 package/module hierarchy처럼 안정적인 namespace로 유지한다.

## Configuration Ownership

handler, formatter, destination, global level 같은 configuration은 application/entrypoint가 소유한다.

```python
# entrypoint
logging.basicConfig(level=logging.INFO)
```

일반 library/module code에서는 다음을 피한다.

```python
logging.basicConfig(...)
_LOGGER.addHandler(...)
_LOGGER.setLevel(...)
```

하위 module이 handler와 level을 고정하면 caller와 framework가 verbosity와 destination을 제어하기 어려워진다.

Project Pivot처럼 application package 안에서 동작하는 code에는 `NullHandler`를 기계적으로 추가하지 않는다. 재사용 library로 분리되어 application logging configuration과 독립되어야 할 때만 Python library guidance에 따라 검토한다.

## Message Formatting

변수를 message에 넣을 때는 logging의 argument formatting을 우선한다.

```python
_LOGGER.info("dbt build 완료: return_code=%s", result.return_code)
```

다음처럼 호출 전에 문자열을 만들 필요는 없다.

```python
_LOGGER.info(f"dbt build 완료: return_code={result.return_code}")
```

logging argument 방식은 record가 실제 emit될 때 formatting할 수 있고, message template을 더 안정적으로 유지하기 쉽다.

단, Project Pivot에서 비교·검색해야 하는 값은 message 문자열에만 숨기지 말고 기존 structured context convention과 함께 사용한다.

## Structured Context

Python `logging`의 `extra`는 사용자 field를 `LogRecord`에 추가한다.

```python
_LOGGER.info(
    "HMDA 원천 적재 완료",
    extra={
        "table_name": table_name,
        "source_count": len(paths),
        "row_count": row_count,
    },
)
```

- field는 작은 scalar 또는 안정적인 identifier를 우선한다.
- `LogRecord`의 기존 attribute 이름과 충돌하는 key를 사용하지 않는다.
- `extra`가 실제 출력에 보이는지는 formatter/handler configuration에 달려 있음을 고려한다.
- 전체 model dump나 mutable object를 그대로 넣지 않는다.

반복되는 context를 여러 호출에 전달해야 하고 실제 중복이 커질 때만 `logging.LoggerAdapter`를 고려한다. Python 3.13의 `LoggerAdapter`는 `merge_extra`를 지원하지만, 단순 호출 몇 개를 위해 adapter나 wrapper를 추가하지 않는다.

## Exceptions

현재 `except` block에서 traceback과 함께 failure를 소유해 기록해야 할 때 `Logger.exception()`을 사용한다.

```python
try:
    run_operation()
except OperationError:
    _LOGGER.exception("operation 실행 실패")
    raise
```

- `exception()`은 exception handler 안에서 사용한다.
- exception을 단순히 다시 올리는 모든 layer에서 반복 logging하지 않는다.
- lower layer가 exception context를 충분히 제공한다면 상위 layer는 새로운 의미를 추가하는 경우에만 log한다.
- traceback이 필요하지 않은 expected rejection이나 domain result를 무조건 exception log로 만들지 않는다.

`exc_info=True`가 필요한 특수한 경우가 아니면 `exception()`이 의도를 더 직접 표현한다.

## Level Methods

정해진 level에서는 해당 method를 사용한다.

```python
_LOGGER.debug(...)
_LOGGER.info(...)
_LOGGER.warning(...)
_LOGGER.error(...)
_LOGGER.critical(...)
```

- deprecated `warn()` 대신 `warning()`을 사용한다.
- arbitrary numeric level과 `logger.log()`는 기존 protocol이 요구하지 않는 한 만들지 않는다.
- `CRITICAL`은 일반 operation 실패를 강조하기 위한 level이 아니다.

level 의미 자체는 [Logging](logging.md)의 기준을 따른다.

## Helpers And Caller Location

logging helper가 caller를 대신해 실제 log call을 수행하면 기록된 filename/function/line이 helper를 가리킬 수 있다.

그러한 helper가 이미 필요하고 caller location을 보존해야 할 때 `stacklevel`을 사용한다.

```python
def log_rejection(message: str) -> None:
    _LOGGER.warning(message, stacklevel=2)
```

하지만 `stacklevel`을 쓰기 위해 logging helper를 새로 만들지는 않는다. wrapper는 반복되는 의미나 정책을 실제로 소유할 때만 고려한다.

## Concurrency

Python `logging`은 일반 thread 사용을 위한 내부 locking을 제공한다. clarification 목적만으로 별도 lock을 둘 필요는 없다.

고비용 handler I/O가 실제 execution을 방해하는 문제가 확인되면 `QueueHandler` 같은 별도 설계를 검토할 수 있지만, 이는 기본 runtime clarification 범위를 넘어설 수 있으므로 성능 문제와 구분한다.

async signal handler처럼 표준 logging의 locking과 맞지 않는 특수 execution context에서는 logging을 안전하다고 가정하지 않는다.

## Final Check

Python logging 변경 후 확인한다.

- module logger가 기존 hierarchy와 일치하는가?
- configuration을 module이 불필요하게 소유하지 않는가?
- event 의미는 `logging.md`의 기준을 충족하는가?
- dynamic value가 안정적인 방식으로 전달되는가?
- `extra` field가 작고 충돌하지 않는가?
- exception traceback을 같은 failure에 중복 기록하지 않는가?
- wrapper, adapter, handler가 실제 필요 이상으로 늘어나지 않았는가?

## References

- Python 3.13 `logging` API: https://docs.python.org/3.13/library/logging.html
- Python 3.13 Logging HOWTO: https://docs.python.org/3.13/howto/logging.html
- Python 3.13 Logging Cookbook: https://docs.python.org/3.13/howto/logging-cookbook.html
