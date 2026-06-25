from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.decision import Decision, DecisionApproval
from app.schemas.decision import DecisionResponse, ApprovalRequest, ApprovalResponse, ScenarioRequest, ScenarioResponse
from app.agents.orchestrator import run_pipeline
from app.services.governance_service import GovernanceService

router = APIRouter()


@router.post("/analyze")
async def analyze_query(
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await run_pipeline(query)
    decision = Decision(
        title=f"Analysis: {query[:100]}",
        description=query,
        decision_type="recommendation",
        recommendation=result.get("recommendation", ""),
        confidence_score=result.get("confidence", 0.0),
        evidence={"sources": result.get("evidence", [])},
        explanation=result.get("explanation", {}),
        source_data={"analytics": result.get("analytics_results", {}), "forecast": result.get("forecast_results", {}), "risk": result.get("risk_results", {})},
        agent_trace={"steps": result.get("agent_trace", [])},
        created_by_agent="orchestrator",
        requested_by=current_user.id,
    )
    db.add(decision)
    await db.flush()
    await GovernanceService.log(db, "decision.created", "Decision", f"Decision created: {decision.title[:80]}", decision.id, current_user.id)
    return {
        "decision_id": decision.id,
        "recommendation": result.get("recommendation"),
        "confidence": result.get("confidence"),
        "explanation": result.get("explanation"),
        "risk_summary": result.get("risk_results"),
        "agent_trace": result.get("agent_trace"),
    }


@router.get("/", response_model=list[DecisionResponse])
async def list_decisions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Decision).order_by(Decision.created_at.desc()).limit(50))
    return result.scalars().all()


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(decision_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Decision).where(Decision.id == decision_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.post("/{decision_id}/approve", response_model=ApprovalResponse)
async def approve_decision(
    decision_id: int,
    payload: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Decision).where(Decision.id == decision_id))
    decision = result.scalar_one_or_none()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    approval = DecisionApproval(
        decision_id=decision_id,
        approved_by=current_user.id,
        action=payload.action,
        notes=payload.notes,
    )
    db.add(approval)
    decision.status = payload.action
    decision.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    await GovernanceService.log(
        db, f"decision.{payload.action}", "Decision",
        f"Decision {payload.action}: {decision.title[:80]}", decision_id, current_user.id,
        metadata={"notes": payload.notes}
    )
    return approval


@router.post("/scenario/simulate", response_model=ScenarioResponse)
async def simulate_scenario(
    payload: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.services.ml_service import MLService
    import numpy as np
    risk_score, shap_vals = MLService.score_risk(payload.parameters)
    base_forecast = MLService.generate_timeseries("revenue", 30)
    last_val = float(base_forecast["y"].iloc[-1])
    impact_factor = 1 + (0.1 * (1 - risk_score))
    simulated_outcomes = {
        "expected_revenue": round(last_val * impact_factor, 2),
        "revenue_impact": round((impact_factor - 1) * 100, 2),
        "risk_score": round(risk_score, 4),
        "shap_values": shap_vals,
    }
    recommendations = [
        f"Proceed with '{payload.scenario_name}' if risk score < 0.5 (current: {risk_score:.2f}).",
        "Monitor revenue_trend and payment_delay_days closely.",
        "Review with finance team before execution.",
    ]
    await GovernanceService.log(db, "scenario.simulated", "Scenario", f"Simulated: {payload.scenario_name}", actor_id=current_user.id)
    return ScenarioResponse(
        scenario_name=payload.scenario_name,
        description=payload.description,
        simulated_outcomes=simulated_outcomes,
        risk_delta=round(risk_score - 0.3, 4),
        confidence=round(1 - risk_score, 4),
        recommendations=recommendations,
    )
