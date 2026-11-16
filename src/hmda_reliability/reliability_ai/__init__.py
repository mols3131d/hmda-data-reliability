"""신뢰성 AI(reliability_ai) 도메인 공개 API 모듈.

조사(investigation)와 위임 실행(execution) 인터페이스를 제공한다.
"""

from hmda_reliability.reliability_ai import (
    context,
    contracts,
    evidence,
    execution,
    investigation,
    settings,
)
from hmda_reliability.reliability_ai.context import (
    BoundedReviewContext,
    build_bounded_review_context,
)
from hmda_reliability.reliability_ai.contracts import (
    AgenticReviewInput,
    InvestigationInput,
    NullSpikeFacts,
)
from hmda_reliability.reliability_ai.execution import (
    ActionProposal,
    ExecutionReceipt,
    ReportEnvelope,
    TaskEnvelope,
    execute_delegated_task,
)
from hmda_reliability.reliability_ai.investigation import (
    DEFAULT_INVESTIGATION_TOOLS,
    InvestigationFinding,
    InvestigationHypothesis,
    InvestigationResult,
    InvestigationTurnRecord,
    InvestigationUncertainty,
    ToolCallRecord,
    ToolRegistry,
    investigate_incident,
)
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings

__all__ = [
    "ActionProposal",
    "AgenticReviewInput",
    "BoundedReviewContext",
    "DEFAULT_INVESTIGATION_TOOLS",
    "ExecutionReceipt",
    "InvestigationFinding",
    "InvestigationHypothesis",
    "InvestigationInput",
    "InvestigationResult",
    "InvestigationTurnRecord",
    "InvestigationUncertainty",
    "NullSpikeFacts",
    "ReliabilityAISettings",
    "ReportEnvelope",
    "TaskEnvelope",
    "ToolCallRecord",
    "ToolRegistry",
    "build_bounded_review_context",
    "context",
    "contracts",
    "evidence",
    "execute_delegated_task",
    "execution",
    "investigate_incident",
    "investigation",
    "settings",
]
