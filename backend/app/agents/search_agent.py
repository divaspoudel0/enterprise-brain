import structlog
from app.agents.state import AgentState
from app.services.vector_service import VectorService
from app.services.ontology_service import OntologyService

log = structlog.get_logger()


async def search_agent(state: AgentState) -> AgentState:
    query = state["query"]
    log.info("search_agent.start", query=query)

    docs = await VectorService.search(query, limit=8)
    graph_context = []
    try:
        term = query.split()[0] if query else ""
        graph_context = await OntologyService.query(
            "MATCH (n) WHERE toLower(n.name) CONTAINS toLower($term) RETURN n LIMIT 10",
            {"term": term}
        )
    except Exception as e:
        log.warning("search_agent.graph_query_failed", error=str(e))

    return {
        **state,
        "search_results": docs,
        "agent_trace": [{"agent": "search", "docs_found": len(docs), "graph_nodes": len(graph_context)}],
    }
