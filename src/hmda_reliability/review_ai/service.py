"""현재 한국어 단계별 텍스트 검토의 일반 진입점.

모델이 텍스트를 반환하고 코드가 JSON을 취합한다. 과거 version을 선택한
JSON 검토는 review_ai.legacy.review_null_spike에서만 제공한다.
"""

from hmda_reliability.review_ai.staged.service import (
    review_null_spike_staged as review_null_spike,
)

__all__ = ["review_null_spike"]
