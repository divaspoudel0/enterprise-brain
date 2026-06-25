import structlog
from app.agents.state import AgentState
from app.services.ml_service import MLService

log = structlog.get_logger()


async def forecast_agent(state: AgentState) -> AgentState:
    query = state.get("query", "revenue")
    log.info("forecast_agent.start", query=query)

    metric = query.lower()
    df = MLService.generate_timeseries(metric, n_days=365)
    result = MLService.forecast_prophet(metric, df, horizon_days=30)

    return {
        **state,
        "forecast_results": result,
        "agent_trace": [{"agent": "forecast", "metric": metric, "horizon_days": 30, "rmse": result.get("rmse")}],
    }
