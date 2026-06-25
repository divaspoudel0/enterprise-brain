import asyncio
import structlog
from app.tasks.celery_app import celery_app

log = structlog.get_logger()


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.tasks.ingest_file", bind=True, max_retries=3)
def ingest_file(self, source_id: int, object_path: str, file_type: str):
    from app.core.database import AsyncSessionLocal
    from app.models.data_source import DataSource
    from app.services.etl_service import ETLService
    from app.services.storage_service import StorageService
    from sqlalchemy import select

    async def _run_ingest():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(DataSource).where(DataSource.id == source_id))
            source = result.scalar_one_or_none()
            if not source:
                log.error("ingest_file.source_not_found", source_id=source_id)
                return
            file_bytes = StorageService.download_file(object_path.split("/", 1)[-1])
            if file_type == "csv":
                count = await ETLService.ingest_csv(source, file_bytes, db)
            elif file_type in ("xlsx", "xls"):
                count = await ETLService.ingest_excel(source, file_bytes, db)
            elif file_type == "pdf":
                count = await ETLService.ingest_pdf(source, file_bytes, db)
            else:
                count = 0
            log.info("ingest_file.done", source_id=source_id, count=count)
            await db.commit()

    try:
        _run(_run_ingest())
    except Exception as exc:
        log.error("ingest_file.failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.tasks.tasks.scheduled_risk_scan")
def scheduled_risk_scan():
    from app.core.database import AsyncSessionLocal
    from app.services.ml_service import MLService
    from app.services.explainability_service import ExplainabilityService
    from app.models.risk import RiskAlert
    from app.services.governance_service import GovernanceService

    async def _scan():
        async with AsyncSessionLocal() as db:
            scenarios = [
                {"name": "Revenue Decline Risk", "category": "financial", "features": {"revenue_trend": 0.6, "payment_delay_days": 0.3}},
                {"name": "Operational Risk", "category": "operational", "features": {"inventory_turnover": 0.7, "debt_ratio": 0.4}},
            ]
            for s in scenarios:
                risk_score, shap_values = MLService.score_risk(s["features"])
                if risk_score >= 0.4:
                    severity = "critical" if risk_score > 0.8 else "high" if risk_score > 0.6 else "medium"
                    exp = ExplainabilityService.build_risk_explanation(risk_score, shap_values, s["category"])
                    alert = RiskAlert(title=s["name"], description=exp, severity=severity, risk_score=risk_score, risk_category=s["category"], affected_entities={}, evidence={}, shap_values=shap_values)
                    db.add(alert)
                    await db.flush()
                    await GovernanceService.log(db, "risk.detected", "RiskAlert", f"Scheduled scan: {s['name']}", alert.id, actor_type="system")
            await db.commit()
            log.info("scheduled_risk_scan.done")

    _run(_scan())


@celery_app.task(name="app.tasks.tasks.scheduled_forecast_refresh")
def scheduled_forecast_refresh():
    from app.core.database import AsyncSessionLocal
    from app.services.ml_service import MLService
    from app.models.forecast import ForecastResult
    from app.services.governance_service import GovernanceService

    async def _refresh():
        async with AsyncSessionLocal() as db:
            for metric in ["revenue", "customers", "orders"]:
                df = MLService.generate_timeseries(metric, 365)
                result = MLService.forecast_prophet(metric, df, 30)
                record = ForecastResult(
                    metric_name=metric, model_type="prophet", horizon_days=30,
                    forecast_data=result, accuracy_metrics={"rmse": result.get("rmse"), "mape": result.get("mape")},
                    feature_importance={}, rmse=result.get("rmse"), mape=result.get("mape"),
                )
                db.add(record)
                await db.flush()
                await GovernanceService.log(db, "forecast.refreshed", "ForecastResult", f"Auto-refreshed forecast: {metric}", record.id, actor_type="system")
            await db.commit()
            log.info("scheduled_forecast_refresh.done")

    _run(_refresh())
