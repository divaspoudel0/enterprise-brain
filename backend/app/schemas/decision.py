from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class DecisionResponse(BaseModel):
    id: int
    title: str
    description: str
    decision_type: str
    status: str
    recommendation: str
    confidence_score: float
    evidence: dict
    explanation: dict
    source_data: dict
    created_by_agent: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    action: str  # approved, rejected, deferred
    notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    decision_id: int
    action: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioRequest(BaseModel):
    scenario_name: str
    parameters: dict
    description: str


class ScenarioResponse(BaseModel):
    scenario_name: str
    description: str
    simulated_outcomes: dict
    risk_delta: float
    confidence: float
    recommendations: list[str]
