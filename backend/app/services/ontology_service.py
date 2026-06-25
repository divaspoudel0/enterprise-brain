from typing import Optional
import structlog
from neo4j import AsyncGraphDatabase

from app.core.config import settings

log = structlog.get_logger()


class OntologyService:
    @staticmethod
    def _driver():
        return AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    @staticmethod
    async def ensure_schema():
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                constraints = [
                    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                    "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
                    "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
                    "CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE",
                ]
                for c in constraints:
                    await session.run(c)
                log.info("neo4j.schema_initialized")
        except Exception as e:
            log.warning("neo4j.schema_init_failed", error=str(e))
        finally:
            await driver.close()

    @staticmethod
    async def upsert_entity(label: str, entity_id: str, properties: dict):
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                props = {k: v for k, v in properties.items() if v is not None}
                await session.run(
                    f"MERGE (e:{label} {{id: $id}}) SET e += $props",
                    id=entity_id, props=props
                )
        finally:
            await driver.close()

    @staticmethod
    async def create_relationship(
        from_label: str, from_id: str,
        to_label: str, to_id: str,
        rel_type: str, properties: dict = None
    ):
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                await session.run(
                    f"""
                    MATCH (a:{from_label} {{id: $from_id}})
                    MATCH (b:{to_label} {{id: $to_id}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    SET r += $props
                    """,
                    from_id=from_id, to_id=to_id, props=properties or {}
                )
        finally:
            await driver.close()

    @staticmethod
    async def query(cypher: str, params: dict = None) -> list[dict]:
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                result = await session.run(cypher, params or {})
                records = await result.data()
                return records
        finally:
            await driver.close()

    @staticmethod
    async def get_entity_neighborhood(entity_id: str, depth: int = 2) -> dict:
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                result = await session.run(
                    """
                    MATCH path = (e {id: $id})-[*1..$depth]-(related)
                    RETURN e, relationships(path) as rels, nodes(path) as nodes
                    LIMIT 50
                    """,
                    id=entity_id, depth=depth
                )
                data = await result.data()
                return {"entity_id": entity_id, "neighborhood": data}
        finally:
            await driver.close()

    @staticmethod
    async def get_graph_stats() -> dict:
        driver = OntologyService._driver()
        try:
            async with driver.session() as session:
                result = await session.run(
                    """
                    MATCH (n)
                    WITH labels(n)[0] as label, count(n) as count
                    RETURN label, count ORDER BY count DESC
                    """
                )
                node_counts = await result.data()
                rel_result = await session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
                rel_counts = await rel_result.data()
                return {"nodes": node_counts, "relationships": rel_counts}
        finally:
            await driver.close()
