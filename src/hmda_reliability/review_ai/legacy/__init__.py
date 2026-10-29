"""v1~v3 JSON 검토의 명시적 비교·과거 실행 재현 API.

일반 검토는 review_ai.review_null_spike를 사용한다. 여기의 호출자는
PromptIdentity를 명시하며 기존 AgenticReviewResult 계약을 사용한다.
"""

from hmda_reliability.review_ai.contracts import PromptIdentity
from hmda_reliability.review_ai.legacy.service import review_null_spike

__all__ = ["PromptIdentity", "review_null_spike"]
