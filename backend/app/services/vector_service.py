from typing import Optional
import structlog
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)
from sentence_transformers import SentenceTransformer

from app.core.config import settings

log = structlog.get_logger()
_model: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def _get_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)


class VectorService:
    @staticmethod
    async def ensure_collection():
        client = _get_client()
        try:
            collections = await client.get_collections()
            names = [c.name for c in collections.collections]
            if settings.QDRANT_COLLECTION not in names:
                await client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=VectorParams(size=settings.EMBEDDING_DIM, distance=Distance.COSINE),
                )
                log.info("qdrant.collection_created", name=settings.QDRANT_COLLECTION)
        finally:
            await client.close()

    @staticmethod
    def embed(text: str) -> list[float]:
        return _get_model().encode(text).tolist()

    @staticmethod
    async def upsert(doc_id: str, text: str, metadata: dict):
        client = _get_client()
        try:
            vector = VectorService.embed(text)
            await client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[PointStruct(id=abs(hash(doc_id)) % (2**63), vector=vector, payload={**metadata, "text": text})],
            )
        finally:
            await client.close()

    @staticmethod
    async def search(query: str, limit: int = 5, filters: Optional[dict] = None) -> list[dict]:
        client = _get_client()
        try:
            vector = VectorService.embed(query)
            qdrant_filter = None
            if filters:
                conditions = [FieldCondition(key=k, match=MatchValue(value=v)) for k, v in filters.items()]
                qdrant_filter = Filter(must=conditions)
            results = await client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=vector,
                limit=limit,
                query_filter=qdrant_filter,
                with_payload=True,
            )
            return [{"score": r.score, **r.payload} for r in results]
        finally:
            await client.close()
