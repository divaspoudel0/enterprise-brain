from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class AnalyticsRequest(BaseModel):
    metric: str
    dimensions: list[str] = []
    filters: dict = {}
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class KPIResponse(BaseModel):
    name: str
    value: float
    unit: str
    change_pct: float
    trend: str  # up, down, stable
    period: str


class AnalyticsResponse(BaseModel):
    metric: str
    data: list[dict]
    summary: dict
    insights: list[str]
    anomalies: list[dict]


class ForecastRequest(BaseModel):
    metric: str
    horizon_days: int = 30
    model_type: str = "prophet"
    include_explanation: bool = True


class ForecastResponse(BaseModel):
    id: int
    metric_name: str
    model_type: str
    horizon_days: int
    forecast_data: dict
    accuracy_metrics: dict
    feature_importance: dict
    explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskSummary(BaseModel):
    total_alerts: int
    critical: int
    high: int
    medium: int
    low: int
    open_alerts: int
    top_risks: list[dict]


class RiskAlertResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    risk_score: float
    risk_category: str
    status: str
    affected_entities: dict
    evidence: dict
    shap_values: dict
    created_at: datetime

    model_config = {"from_attributes": True}
