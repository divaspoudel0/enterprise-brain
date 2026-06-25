from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.risk import RiskAlert
from app.schemas.analytics import RiskSummary, RiskAlertResponse
from app.services.ml_service import MLService
from app.services.explainability_service import ExplainabilityService
from app.services.governance_service import GovernanceService

router = APIRouter()


@router.get("/alerts", response_model=list[RiskAlertResponse])
async def list_risk_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RiskAlert).order_by(RiskAlert.created_at.desc()).limit(50))
    return result.scalars().all()


@router.get("/summary", response_model=RiskSummary)
async def get_risk_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RiskAlert))
    alerts = result.scalars().all()
    severities = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    open_count = 0
    for a in alerts:
        severities[a.severity] = severities.get(a.severity, 0) + 1
        if a.status == "open":
            open_count += 1
    top_risks = [
        {"id": a.id, "title": a.title, "severity": a.severity, "risk_score": a.risk_score}
        for a in sorted(alerts, key=lambda x: x.risk_score, reverse=True)[:5]
    ]
    return RiskSummary(
        total_alerts=len(alerts),
        critical=severities["critical"],
        high=severities["high"],
        medium=severities["medium"],
        low=severities["low"],
        open_alerts=open_count,
        top_risks=top_risks,
    )


@router.post("/scan")
async def scan_risks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scenarios = [
        {"name": "Revenue Decline Risk", "category": "financial", "features": {"revenue_trend": 0.7, "payment_delay_days": 0.3}},
        {"name": "Customer Churn Risk", "category": "customer", "features": {"customer_churn_rate": 0.6, "order_volume_change": 0.4}},
        {"name": "Inventory Shortage Risk", "category": "operational", "features": {"inventory_turnover": 0.8, "debt_ratio": 0.2}},
    ]
    created = []
    for s in scenarios:
        risk_score, shap_values = MLService.score_risk(s["features"])
        if risk_score < 0.3:
            continue
        severity = "critical" if risk_score > 0.8 else "high" if risk_score > 0.6 else "medium"
        explanation = ExplainabilityService.build_risk_explanation(risk_score, shap_values, s["category"])
        alert = RiskAlert(
            title=s["name"],
            description=explanation,
            severity=severity,
            risk_score=risk_score,
            risk_category=s["category"],
            affected_entities={},
            evidence={"features": s["features"]},
            shap_values=shap_values,
        )
        db.add(alert)
        await db.flush()
        await GovernanceService.log(db, "risk.detected", "RiskAlert", f"Risk detected: {s['name']}", alert.id, actor_type="agent")
        created.append({"id": alert.id, "title": s["name"], "severity": severity, "risk_score": round(risk_score, 4)})
    return {"scanned": len(scenarios), "alerts_created": len(created), "alerts": created}


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RiskAlert).where(RiskAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.now(timezone.utc)
    await GovernanceService.log(db, "risk.acknowledged", "RiskAlert", f"Alert acknowledged: {alert.title}", alert_id, current_user.id)
    return {"status": "acknowledged", "alert_id": alert_id}
