from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.audit import AuditLog

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    event_type: str
    entity_type: str
    entity_id: Optional[int] = None
    actor_id: Optional[int] = None
    actor_type: str
    description: str
    metadata: dict
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    event_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if event_type:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(log_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(AuditLog))
    logs = result.scalars().all()
    event_counts = {}
    for log in logs:
        event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1
    return {
        "total_events": len(logs),
        "event_breakdown": event_counts,
        "decisions_approved": event_counts.get("decision.approved", 0),
        "decisions_rejected": event_counts.get("decision.rejected", 0),
        "risks_detected": event_counts.get("risk.detected", 0),
        "queries_executed": event_counts.get("query.executed", 0),
    }
