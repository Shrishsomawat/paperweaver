from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from paper2code.agents import PipelineAgents
from paper2code.models import Paper2CodeState


def build_graph(agents: PipelineAgents):
    graph = StateGraph(Paper2CodeState)
    graph.add_node("parser", agents.parser_agent)
    graph.add_node("vision", agents.vision_agent)
    graph.add_node("planner", agents.planner_agent)
    graph.add_node("coder_critic", agents.coder_critic_agent)
    graph.add_node("test_writer", agents.test_agent)

    graph.set_entry_point("parser")
    graph.add_edge("parser", "vision")
    graph.add_edge("vision", "planner")
    graph.add_edge("planner", "coder_critic")
    graph.add_conditional_edges(
        "coder_critic",
        should_retry_or_continue,
        {
            "retry_coding": "coder_critic",
            "next_module": "coder_critic",
            "generate_tests": "test_writer",
        },
    )
    graph.add_edge("test_writer", END)
    return graph.compile()


def should_retry_or_continue(state: Paper2CodeState) -> str:
    if state.get("critic_feedback") and state.get("critic_iterations", 0) < 1:
        return "retry_coding"
    if len(state.get("code_modules", {})) < len(state.get("implementation_plan", [])):
        return "next_module"
    return "generate_tests"
