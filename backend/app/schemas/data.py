from typing import Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    connection_config: dict = {}


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    status: str
    last_ingested_at: Optional[datetime] = None
    record_count: int
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryRequest(BaseModel):
    query: str
    data_source_ids: Optional[list[int]] = None
    include_graph: bool = True


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    confidence: float
    graph_context: Optional[Union[list, dict]] = None
    agent_trace: list[dict] = []
