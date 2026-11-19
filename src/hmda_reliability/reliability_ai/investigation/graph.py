"""사고와 적재 조사가 공유하는 제한된 모델·조회 상태 전이."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langsmith import tracing_context

from hmda_reliability.runtime_ai.contracts import ProviderResponse, ToolCall


@dataclass(frozen=True)
class GraphStop:
    status: str
    failure_code: str | None = None
    payload: dict[str, Any] | None = None


@dataclass
class _Run:
    """민감한 원문과 도메인 연결은 조사별로 격리하고 그래프 상태에는 위치만 둔다."""

    assess: Callable[[int], GraphStop | None]
    model: Callable[[int], ProviderResponse | GraphStop]
    retain: Callable[[int, ProviderResponse], ProviderResponse | GraphStop | None]
    read: Callable[[int, ToolCall], GraphStop | None]
    max_turns: int
    max_tool_calls: int
    response: ProviderResponse | None = None
    stop: GraphStop | None = None


type _Route = Literal["model", "retain", "read", "assess", "finish"]


@dataclass
class _State:
    turn: int
    index: int
    calls: int
    route: _Route


def _assess(state: _State, runtime: Runtime[_Run]) -> dict[str, Any]:
    run = runtime.context
    turn = state.turn + 1
    run.stop = run.assess(turn)
    if run.stop is None and turn >= run.max_turns:
        run.stop = GraphStop("budget_exhausted", "max_turns_exceeded")
    return {"turn": turn, "route": "finish" if run.stop else "model"}


def _model(state: _State, runtime: Runtime[_Run]) -> dict[str, Any]:
    run = runtime.context
    response = run.model(state.turn)
    if isinstance(response, GraphStop):
        run.stop = response
        return {"route": "finish"}
    run.response = response
    return {"route": "retain"}


def _retain(state: _State, runtime: Runtime[_Run]) -> dict[str, Any]:
    run = runtime.context
    assert run.response is not None
    retained = run.retain(state.turn, run.response)
    if isinstance(retained, ProviderResponse):
        run.response = retained
    else:
        run.stop = retained
    if run.stop is None and not run.response.tool_calls:
        raise ValueError("retained response must contain a terminal decision or calls")
    return {"index": 0, "route": "finish" if run.stop else "read"}


def _read(state: _State, runtime: Runtime[_Run]) -> dict[str, Any]:
    run = runtime.context
    assert run.response is not None
    if state.calls >= run.max_tool_calls:
        run.stop = GraphStop("budget_exhausted", "tool_call_budget_exhausted")
        return {"route": "finish"}
    index = state.index
    batch = run.response.tool_calls
    run.stop = run.read(state.turn, batch[index])
    if run.stop is not None:
        return {"route": "finish"}
    return {
        "index": index + 1,
        "calls": state.calls + 1,
        "route": "read" if index + 1 < len(batch) else "assess",
    }


def _route(state: _State) -> _Route:
    return state.route


def _build_graph() -> CompiledStateGraph[_State, _Run, _State, _State]:
    graph = StateGraph(_State, context_schema=_Run)
    graph.add_edge(START, "assess")
    for name, node, destinations in (
        ("assess", _assess, ["model", "finish"]),
        ("model", _model, ["retain", "finish"]),
        ("retain", _retain, ["read", "finish"]),
        ("read", _read, ["read", "assess", "finish"]),
    ):
        graph.add_node(name, node)
        graph.add_conditional_edges(
            name,
            _route,
            {dest: END if dest == "finish" else dest for dest in destinations},
        )
    return graph.compile()


_GRAPH = _build_graph()


def run_investigation_graph[Result](
    *,
    assess: Callable[[int], GraphStop | None],
    model: Callable[[int], ProviderResponse | GraphStop],
    retain: Callable[[int, ProviderResponse], ProviderResponse | GraphStop | None],
    read: Callable[[int, ToolCall], GraphStop | None],
    finish: Callable[[GraphStop], Result],
    max_turns: int,
    max_tool_calls: int,
) -> Result:
    """영속화된 모델 응답에서 허용된 횟수만큼 순서대로 읽고 종료 결정을 게시한다."""
    run = _Run(assess, model, retain, read, max_turns, max_tool_calls)
    # 원격 관측은 도메인의 명시적 투영만 보내야 한다. 상속된 LangSmith 추적은 끈다.
    with tracing_context(enabled=False):
        _GRAPH.invoke(
            _State(turn=-1, index=0, calls=0, route="assess"),
            context=run,
            config={"recursion_limit": 3 * max_turns + max_tool_calls + 4},
        )
    assert run.stop is not None
    return finish(run.stop)
