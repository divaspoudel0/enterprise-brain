import json
import structlog
import numpy as np
from app.agents.state import AgentState
from app.services.ml_service import MLService

log = structlog.get_logger()


async def analytics_agent(state: AgentState) -> AgentState:
    log.info("analytics_agent.start")
    docs = state.get("search_results", [])

    numeric_values = []
    for doc in docs:
        raw = doc.get("data", "{}")
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            data = {}
        for v in data.values():
            try:
                numeric_values.append(float(v))
            except (ValueError, TypeError):
                pass

    anomalies = []
    summary = {}
    if len(numeric_values) >= 10:
        arr = np.array(numeric_values)
        summary = {
            "count": len(arr),
            "mean": round(float(arr.mean()), 4),
            "std": round(float(arr.std()), 4),
            "min": round(float(arr.min()), 4),
            "max": round(float(arr.max()), 4),
            "p25": round(float(np.percentile(arr, 25)), 4),
            "p75": round(float(np.percentile(arr, 75)), 4),
        }
        anomalies = MLService.detect_anomalies(numeric_values)

    return {
        **state,
        "analytics_results": {"summary": summary, "anomalies": anomalies, "doc_count": len(docs)},
        "agent_trace": [{"agent": "analytics", "records_analyzed": len(numeric_values), "anomalies_found": len(anomalies)}],
    }
