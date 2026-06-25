import structlog
import numpy as np
from app.agents.state import AgentState
from app.services.ml_service import MLService
from app.services.explainability_service import ExplainabilityService

log = structlog.get_logger()


async def risk_agent(state: AgentState) -> AgentState:
    log.info("risk_agent.start")
    analytics = state.get("analytics_results", {})
    summary = analytics.get("summary", {})
    anomalies = analytics.get("anomalies", [])

    features = {
        "revenue_trend": summary.get("mean", 0) / max(summary.get("max", 1), 1),
        "payment_delay_days": min(1.0, len(anomalies) * 0.1),
        "order_volume_change": abs(summary.get("std", 0)) / max(summary.get("mean", 1), 1),
        "customer_churn_rate": min(1.0, len(anomalies) * 0.05),
        "inventory_turnover": 1 - (summary.get("p25", 0) / max(summary.get("p75", 1), 1)),
        "debt_ratio": summary.get("std", 0) / max(summary.get("mean", 1), 1),
    }

    risk_score, shap_values = MLService.score_risk(features)
    explanation = ExplainabilityService.build_risk_explanation(risk_score, shap_values, "operational")

    return {
        **state,
        "risk_results": {
            "risk_score": round(risk_score, 4),
            "severity": "critical" if risk_score > 0.8 else "high" if risk_score > 0.6 else "medium" if risk_score > 0.4 else "low",
            "shap_values": shap_values,
            "anomaly_count": len(anomalies),
            "explanation": explanation,
        },
        "agent_trace": [{"agent": "risk", "risk_score": round(risk_score, 4), "anomalies": len(anomalies)}],
    }
