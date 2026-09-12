"""Provider 중립적 AI 런타임 경계 패키지.

`runtime_ai` 패키지 루트는 외부 capability 호출자가 런타임을 구성할 때
사용하는 명시적 설정 계약인 `RuntimeAISettings`만 공개(export)한다.
OpenAI 호환 어댑터, 전송 프로토콜, 메시지 계약 및 예외 계층은
도메인 내부 모듈(`provider`, `contracts`, `settings`)에 유지된다.
"""

from hmda_reliability.runtime_ai.settings import RuntimeAISettings

__all__ = ["RuntimeAISettings"]
