from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsRequest, AnalyticsResponse, KPIResponse
from app.services.ml_service import MLService
from app.services.vector_service import VectorService

router = APIRouter()

_KPI_METRICS = [
    {"name": "Revenue", "unit": "USD", "seed": "revenue"},
    {"name": "Active Customers", "unit": "count", "seed": "customers"},
    {"name": "Order Volume", "unit": "count", "seed": "orders"},
    {"name": "Inventory Turnover", "unit": "ratio", "seed": "inventory"},
]


@router.get("/kpis", response_model=list[KPIResponse])
async def get_kpis(current_user: User = Depends(get_current_user)):
    import numpy as np
    kpis = []
    for m in _KPI_METRICS:
        df = MLService.generate_timeseries(m["seed"], n_days=60)
        current = float(df["y"].iloc[-1])
        previous = float(df["y"].iloc[-31])
        change_pct = round((current - previous) / max(abs(previous), 1) * 100, 2)
        kpis.append(KPIResponse(
            name=m["name"],
            value=round(current, 2),
            unit=m["unit"],
            change_pct=change_pct,
            trend="up" if change_pct > 0 else "down" if change_pct < 0 else "stable",
            period="Last 30 days",
        ))
    return kpis


@router.post("/query", response_model=AnalyticsResponse)
async def run_analytics(
    payload: AnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    df = MLService.generate_timeseries(payload.metric, n_days=90)
    data = [{"date": str(row.ds.date()), "value": round(row.y, 2)} for _, row in df.iterrows()]
    anomalies = MLService.detect_anomalies(df["y"].tolist())
    anomaly_details = [{"date": data[a["index"]]["date"], "value": a["value"], "score": a["anomaly_score"]} for a in anomalies if a["index"] < len(data)]
    summary = {
        "mean": round(float(df["y"].mean()), 2),
        "max": round(float(df["y"].max()), 2),
        "min": round(float(df["y"].min()), 2),
        "std": round(float(df["y"].std()), 2),
    }
    insights = [
        f"Average {payload.metric}: {summary['mean']:,.2f}",
        f"Range: {summary['min']:,.2f} – {summary['max']:,.2f}",
        f"Detected {len(anomaly_details)} anomalies in the period.",
    ]
    return AnalyticsResponse(metric=payload.metric, data=data, summary=summary, insights=insights, anomalies=anomaly_details)
