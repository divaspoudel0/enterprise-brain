from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.user import User
from app.services.ontology_service import OntologyService

router = APIRouter()


class EntityRequest(BaseModel):
    label: str
    entity_id: str
    properties: dict = {}


class RelationshipRequest(BaseModel):
    from_label: str
    from_id: str
    to_label: str
    to_id: str
    rel_type: str
    properties: dict = {}


class CypherRequest(BaseModel):
    cypher: str
    params: dict = {}


@router.get("/stats")
async def get_graph_stats(current_user: User = Depends(get_current_user)):
    return await OntologyService.get_graph_stats()


@router.post("/entities")
async def upsert_entity(payload: EntityRequest, current_user: User = Depends(get_current_user)):
    await OntologyService.upsert_entity(payload.label, payload.entity_id, payload.properties)
    return {"status": "ok", "label": payload.label, "id": payload.entity_id}


@router.post("/relationships")
async def create_relationship(payload: RelationshipRequest, current_user: User = Depends(get_current_user)):
    await OntologyService.create_relationship(
        payload.from_label, payload.from_id,
        payload.to_label, payload.to_id,
        payload.rel_type, payload.properties
    )
    return {"status": "ok"}


@router.get("/entities/{entity_id}/neighborhood")
async def get_neighborhood(entity_id: str, depth: int = 2, current_user: User = Depends(get_current_user)):
    return await OntologyService.get_entity_neighborhood(entity_id, depth)


@router.post("/query")
async def run_cypher(payload: CypherRequest, current_user: User = Depends(get_current_user)):
    if any(kw in payload.cypher.upper() for kw in ["DROP", "DELETE", "DETACH"]):
        raise HTTPException(status_code=400, detail="Destructive queries not allowed")
    results = await OntologyService.query(payload.cypher, payload.params)
    return {"results": results, "count": len(results)}
