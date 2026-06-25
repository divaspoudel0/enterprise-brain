from typing import TypedDict, Annotated, Optional, Any
import operator


class AgentState(TypedDict):
    query: str
    messages: Annotated[list[dict], operator.add]
    search_results: list[dict]
    analytics_results: dict
    forecast_results: dict
    risk_results: dict
    recommendation: str
    confidence: float
    evidence: list[dict]
    explanation: dict
    error: Optional[str]
    agent_trace: Annotated[list[dict], operator.add]
