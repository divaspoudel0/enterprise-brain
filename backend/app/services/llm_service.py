from typing import Optional
import structlog
import anthropic

from app.core.config import settings
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService

log = structlog.get_logger()


class LLMService:
    @staticmethod
    def _client() -> anthropic.AsyncAnthropic:
        return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    @staticmethod
    async def answer_query(query: str, data_source_ids: Optional[list[int]] = None, include_graph: bool = True) -> dict:
        filters = {"source_id": data_source_ids[0]} if data_source_ids and len(data_source_ids) == 1 else None
        docs = await VectorService.search(query, limit=8, filters=filters)

        graph_context: list[dict] = []
        if include_graph:
            try:
                term = query.split()[0] if query else ""
                graph_context = await OntologyService.query(
                    "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($term) RETURN n LIMIT 5",
                    {"term": term}
                )
            except Exception:
                graph_context = []

        context_text = "\n\n".join(
            f"[Source: {d.get('source_name', 'unknown')}]\n{d.get('text', '')}"
            for d in docs
        )
        system_prompt = (
            "You are Enterprise Brain, an AI decision intelligence assistant. "
            "Answer questions about enterprise data accurately and concisely. "
            "Always cite your evidence sources. If the context is insufficient, say so. "
            "Format your response with: Answer, Key Evidence, Confidence Assessment."
        )
        user_prompt = f"Question: {query}\n\nContext from enterprise data:\n{context_text}"

        try:
            client = LLMService._client()
            message = await client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            answer = message.content[0].text
            confidence = min(0.95, 0.5 + len(docs) * 0.05 + (0.1 if graph_context else 0))
        except Exception as e:
            log.error("llm.query_failed", error=str(e))
            answer = (
                f"I found {len(docs)} relevant data points for your query about '{query}'. "
                f"Based on the available evidence, please review the source documents for detailed analysis."
            )
            confidence = 0.4

        return {
            "answer": answer,
            "sources": docs[:5],
            "confidence": round(confidence, 3),
            "graph_context": graph_context,
            "agent_trace": [
                {"step": "vector_search", "results": len(docs)},
                {"step": "graph_query", "results": len(graph_context)},
                {"step": "llm_inference", "model": settings.LLM_MODEL},
            ],
        }

    @staticmethod
    async def generate_recommendation(context: dict, task: str) -> str:
        system_prompt = (
            "You are an enterprise decision intelligence engine. "
            "Generate a clear, actionable recommendation based on the provided context. "
            "Include: recommended action, rationale, expected impact, and risk level."
        )
        user_prompt = f"Task: {task}\n\nContext: {str(context)[:2000]}"
        try:
            client = LLMService._client()
            message = await client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return message.content[0].text
        except Exception as e:
            log.error("llm.recommendation_failed", error=str(e))
            return (
                f"Recommendation based on {task}: Review current data trends and consult "
                f"with domain experts before proceeding. Risk indicators suggest cautious approach."
            )
