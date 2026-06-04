"""Lắp StateGraph — docs/agent-workflow §3.

Pattern: router rõ ràng + branch node + guardrail + respond.
(KHÔNG dùng ReAct tự do, để kiểm soát được 4 failure paths + guardrail.)
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent import nodes
from agent.state import AgentState


def build_graph(checkpointer=None):
    """Dựng & compile graph. Truyền checkpointer để có memory + interrupt/resume.

    - Demo/test: MemorySaver (default trong runner).
    - Production: PostgresSaver trỏ Supabase (xem docs §3).
    """
    g = StateGraph(AgentState)

    g.add_node("router", nodes.router)
    g.add_node("analyze", nodes.analyze)
    g.add_node("muscle_gap", nodes.muscle_gap)
    g.add_node("build_plan", nodes.build_plan)
    g.add_node("create_routine", nodes.create_routine)
    g.add_node("knowledge", nodes.knowledge)
    g.add_node("clarify", nodes.clarify)
    g.add_node("general", nodes.general)
    g.add_node("guardrail", nodes.guardrail)
    g.add_node("respond", nodes.respond)

    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        nodes.route_intent,
        ["analyze", "muscle_gap", "build_plan", "create_routine", "knowledge", "clarify", "general"],
    )

    # Các branch "khuyên" đi qua guardrail; còn lại thẳng tới respond.
    for n in ("analyze", "muscle_gap", "build_plan"):
        g.add_edge(n, "guardrail")
    g.add_edge("guardrail", "respond")
    for n in ("create_routine", "knowledge", "clarify", "general"):
        g.add_edge(n, "respond")
    g.add_edge("respond", END)

    return g.compile(checkpointer=checkpointer)
