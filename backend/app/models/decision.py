from datetime import datetime
from sqlalchemy import String, DateTime, Integer, JSON, func, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    decision_type: Mapped[str] = mapped_column(String(100), nullable=False)  # recommendation, forecast, risk, scenario
    status: Mapped[str] = mapped_column(String(50), default="pending_approval")
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanation: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    source_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    agent_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_by_agent: Mapped[str] = mapped_column(String(100), nullable=False)
    requested_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DecisionApproval(Base):
    __tablename__ = "decision_approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), nullable=False)
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # approved, rejected, deferred
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
