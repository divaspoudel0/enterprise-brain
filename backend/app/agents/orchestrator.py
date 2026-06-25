from langgraph.graph import StateGraph, END, START
from app.agents.state import AgentState
from app.agents.search_agent import search_agent
from app.agents.analytics_agent import analytics_agent
from app.agents.forecast_agent import forecast_agent
from app.agents.risk_agent import risk_agent
from app.agents.recommend_agent import recommend_agent


def _build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("search", search_agent)
    graph.add_node("analytics", analytics_agent)
    graph.add_node("forecast", forecast_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("recommend", recommend_agent)

    graph.add_edge(START, "search")
    graph.add_edge("search", "analytics")

    # Fan-out: analytics feeds both forecast and risk in parallel
    graph.add_edge("analytics", "forecast")
    graph.add_edge("analytics", "risk")

    # Fan-in: recommend waits for BOTH forecast and risk to complete
    graph.add_edge(["forecast", "risk"], "recommend")

    graph.add_edge("recommend", END)
    return graph


_app = _build_graph().compile()


async def run_pipeline(query: str) -> AgentState:
    initial_state: AgentState = {
        "query": query,
        "messages": [],
        "search_results": [],
        "analytics_results": {},
        "forecast_results": {},
        "risk_results": {},
        "recommendation": "",
        "confidence": 0.0,
        "evidence": [],
        "explanation": {},
        "error": None,
        "agent_trace": [],
    }
    result = await _app.ainvoke(initial_state)
    return result
