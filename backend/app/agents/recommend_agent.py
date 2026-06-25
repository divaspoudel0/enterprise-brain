import structlog
from app.agents.state import AgentState
from app.services.llm_service import LLMService
from app.services.explainability_service import ExplainabilityService

log = structlog.get_logger()


async def recommend_agent(state: AgentState) -> AgentState:
    log.info("recommend_agent.start")

    context = {
        "query": state.get("query"),
        "analytics": state.get("analytics_results", {}),
        "forecast": {k: v for k, v in state.get("forecast_results", {}).items() if k in ("rmse", "mape")},
        "risk": state.get("risk_results", {}),
        "search_docs_count": len(state.get("search_results", [])),
    }

    recommendation = await LLMService.generate_recommendation(context, state.get("query", "enterprise analysis"))
    risk = state.get("risk_results", {})
    forecast = state.get("forecast_results", {})
    confidence = 0.7
    if risk.get("risk_score", 0) < 0.5:
        confidence += 0.1
    if forecast.get("mape", 100) < 10:
        confidence += 0.1
    if len(state.get("search_results", [])) >= 5:
        confidence += 0.05
    confidence = min(0.95, confidence)

    shap_values = risk.get("shap_values", {})
    evidence = state.get("search_results", [])[:5]
    explanation = ExplainabilityService.build_explanation(
        recommendation, shap_values, evidence, "multi-agent", confidence
    )

    return {
        **state,
        "recommendation": recommendation,
        "confidence": confidence,
        "evidence": evidence,
        "explanation": explanation,
        "agent_trace": [{"agent": "recommend", "confidence": round(confidence, 3)}],
    }
