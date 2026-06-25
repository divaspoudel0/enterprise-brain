from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.forecast import ForecastResult
from app.schemas.analytics import ForecastRequest, ForecastResponse
from app.services.ml_service import MLService
from app.services.governance_service import GovernanceService
from sqlalchemy import select

router = APIRouter()


@router.post("/run", response_model=ForecastResponse)
async def run_forecast(
    payload: ForecastRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    df = MLService.generate_timeseries(payload.metric, n_days=365)
    result = MLService.forecast_prophet(payload.metric, df, payload.horizon_days)

    explanation = (
        f"Prophet model forecasts {payload.metric} for the next {payload.horizon_days} days. "
        f"RMSE: {result.get('rmse', 'N/A')}, MAPE: {result.get('mape', 'N/A')}%. "
        f"The model accounts for weekly and yearly seasonality."
    )

    record = ForecastResult(
        metric_name=payload.metric,
        model_type=payload.model_type,
        horizon_days=payload.horizon_days,
        forecast_data=result,
        accuracy_metrics={"rmse": result.get("rmse"), "mape": result.get("mape")},
        feature_importance={},
        rmse=result.get("rmse"),
        mape=result.get("mape"),
        created_by=current_user.id,
    )
    db.add(record)
    await db.flush()
    await GovernanceService.log(db, "forecast.created", "ForecastResult", f"Forecast: {payload.metric}", record.id, current_user.id)

    return ForecastResponse(
        id=record.id,
        metric_name=payload.metric,
        model_type=payload.model_type,
        horizon_days=payload.horizon_days,
        forecast_data=result,
        accuracy_metrics={"rmse": result.get("rmse"), "mape": result.get("mape")},
        feature_importance={},
        explanation=explanation,
        created_at=record.created_at,
    )


@router.get("/history", response_model=list[ForecastResponse])
async def get_forecast_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ForecastResult).order_by(ForecastResult.created_at.desc()).limit(20))
    records = result.scalars().all()
    return [
        ForecastResponse(
            id=r.id,
            metric_name=r.metric_name,
            model_type=r.model_type,
            horizon_days=r.horizon_days,
            forecast_data=r.forecast_data,
            accuracy_metrics=r.accuracy_metrics,
            feature_importance=r.feature_importance,
            explanation=f"Historical forecast for {r.metric_name}",
            created_at=r.created_at,
        )
        for r in records
    ]
