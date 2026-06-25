from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api import auth, data_ingestion, ontology, analytics, forecast, risk, decisions, audit, health
from app.core.config import settings
from app.core.database import engine, Base
from app.services.ontology_service import OntologyService
from app.services.vector_service import VectorService

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("enterprise_brain.startup", env=settings.APP_ENV)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await VectorService.ensure_collection()
    await OntologyService.ensure_schema()
    yield
    log.info("enterprise_brain.shutdown")
    await engine.dispose()


app = FastAPI(
    title="Enterprise Brain API",
    description="Ontology-Driven Decision Intelligence Platform with Explainable AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(data_ingestion.router, prefix="/api/v1/data", tags=["Data Ingestion"])
app.include_router(ontology.router, prefix="/api/v1/ontology", tags=["Ontology"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(forecast.router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk"])
app.include_router(decisions.router, prefix="/api/v1/decisions", tags=["Decisions"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
