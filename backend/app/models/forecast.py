from datetime import datetime
from sqlalchemy import String, DateTime, Integer, JSON, func, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(100), nullable=False)  # prophet, xgboost
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    accuracy_metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    feature_importance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
