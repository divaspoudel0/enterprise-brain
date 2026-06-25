from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.data_source import DataSource
from app.schemas.data import DataSourceCreate, DataSourceResponse, QueryRequest, QueryResponse
from app.services.etl_service import ETLService
from app.services.llm_service import LLMService
from app.services.governance_service import GovernanceService

router = APIRouter()


@router.post("/sources", response_model=DataSourceResponse, status_code=201)
async def create_data_source(
    payload: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    source = DataSource(
        name=payload.name,
        source_type=payload.source_type,
        connection_config=payload.connection_config,
        created_by=current_user.id,
    )
    db.add(source)
    await db.flush()
    await GovernanceService.log(db, "data_source.created", "DataSource", f"Created data source: {source.name}", source.id, current_user.id)
    return source


@router.get("/sources", response_model=list[DataSourceResponse])
async def list_data_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DataSource).order_by(DataSource.created_at.desc()))
    return result.scalars().all()


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_data_source(source_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return source


@router.post("/sources/{source_id}/upload")
async def upload_file(
    source_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(DataSource).where(DataSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    content = await file.read()
    filename = file.filename.lower()
    try:
        if filename.endswith(".csv"):
            count = await ETLService.ingest_csv(source, content, db)
        elif filename.endswith((".xlsx", ".xls")):
            count = await ETLService.ingest_excel(source, content, db)
        elif filename.endswith(".pdf"):
            count = await ETLService.ingest_pdf(source, content, db)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    await GovernanceService.log(db, "data.ingested", "DataSource", f"Ingested {count} records from {file.filename}", source_id, current_user.id)
    return {"message": f"Ingested {count} records", "source_id": source_id}


@router.post("/query", response_model=QueryResponse)
async def query_data(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await LLMService.answer_query(payload.query, payload.data_source_ids, payload.include_graph)
    await GovernanceService.log(db, "query.executed", "Query", f"Query: {payload.query[:100]}", actor_id=current_user.id)
    return QueryResponse(**result)
