"""Run with: docker compose exec backend python scripts/seed.py"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.data_source import DataSource


async def seed_postgres():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "admin@enterprise.com"))
        if result.scalar_one_or_none():
            print("PostgreSQL: already seeded.")
            return

        admin = User(
            email="admin@enterprise.com",
            full_name="System Admin",
            hashed_password=hash_password("Admin@1234"),
            role="admin",
        )
        analyst = User(
            email="analyst@enterprise.com",
            full_name="Data Analyst",
            hashed_password=hash_password("Analyst@1234"),
            role="analyst",
        )
        db.add_all([admin, analyst])
        await db.flush()

        sources = [
            DataSource(
                name="Sales Database",
                source_type="postgresql",
                connection_config={"host": "localhost", "db": "sales"},
                status="active",
                record_count=5000,
                created_by=admin.id,
            ),
            DataSource(
                name="Customer Reports Q1",
                source_type="csv",
                connection_config={},
                status="active",
                record_count=1200,
                created_by=analyst.id,
            ),
            DataSource(
                name="Financial Statements 2024",
                source_type="excel",
                connection_config={},
                status="active",
                record_count=850,
                created_by=admin.id,
            ),
        ]
        db.add_all(sources)
        await db.commit()
        print("PostgreSQL seeded: admin@enterprise.com / Admin@1234, analyst@enterprise.com / Analyst@1234")


async def seed_neo4j():
    from app.services.ontology_service import OntologyService

    await OntologyService.ensure_schema()

    entities = [
        # Customers
        ("Customer", "CUST-001", {"name": "Acme Corp", "industry": "Manufacturing", "revenue": 5200000, "country": "USA"}),
        ("Customer", "CUST-002", {"name": "TechNova Ltd", "industry": "Technology", "revenue": 12000000, "country": "UK"}),
        ("Customer", "CUST-003", {"name": "GreenLeaf Inc", "industry": "Agriculture", "revenue": 3100000, "country": "India"}),
        ("Customer", "CUST-004", {"name": "OceanFreight Co", "industry": "Logistics", "revenue": 7800000, "country": "Singapore"}),
        # Products
        ("Product", "PROD-001", {"name": "Enterprise Suite", "category": "Software", "price": 49999, "unit": "license"}),
        ("Product", "PROD-002", {"name": "Analytics Platform", "category": "Software", "price": 29999, "unit": "license"}),
        ("Product", "PROD-003", {"name": "Data Warehouse", "category": "Infrastructure", "price": 99999, "unit": "instance"}),
        ("Product", "PROD-004", {"name": "Support Pack", "category": "Services", "price": 9999, "unit": "year"}),
        # Suppliers
        ("Supplier", "SUPP-001", {"name": "CloudBase Systems", "category": "Cloud Infrastructure", "reliability_score": 0.94}),
        ("Supplier", "SUPP-002", {"name": "DataCore Analytics", "category": "Data Processing", "reliability_score": 0.87}),
        # Assets
        ("Asset", "ASSET-001", {"name": "Primary Data Center", "type": "Infrastructure", "value": 2000000, "location": "Frankfurt"}),
        ("Asset", "ASSET-002", {"name": "ML Compute Cluster", "type": "Computing", "value": 500000, "location": "Cloud"}),
        # Risk Factors
        ("RiskFactor", "RISK-001", {"name": "Geopolitical Instability", "category": "External", "impact_level": "high"}),
        ("RiskFactor", "RISK-002", {"name": "Supply Chain Disruption", "category": "Operational", "impact_level": "medium"}),
    ]

    for label, eid, props in entities:
        await OntologyService.upsert_entity(label, eid, props)

    relationships = [
        # Customer → Product (PURCHASED)
        ("Customer", "CUST-001", "Product", "PROD-001", "PURCHASED", {"date": "2024-01-15", "amount": 49999}),
        ("Customer", "CUST-001", "Product", "PROD-004", "PURCHASED", {"date": "2024-01-15", "amount": 9999}),
        ("Customer", "CUST-002", "Product", "PROD-001", "PURCHASED", {"date": "2024-02-01", "amount": 49999}),
        ("Customer", "CUST-002", "Product", "PROD-002", "PURCHASED", {"date": "2024-03-10", "amount": 29999}),
        ("Customer", "CUST-002", "Product", "PROD-003", "PURCHASED", {"date": "2024-03-10", "amount": 99999}),
        ("Customer", "CUST-003", "Product", "PROD-002", "PURCHASED", {"date": "2024-04-05", "amount": 29999}),
        ("Customer", "CUST-004", "Product", "PROD-004", "PURCHASED", {"date": "2024-04-20", "amount": 9999}),
        # Supplier → Asset (PROVIDES)
        ("Supplier", "SUPP-001", "Asset", "ASSET-001", "PROVIDES", {"contract": "annual", "sla": "99.9%"}),
        ("Supplier", "SUPP-001", "Asset", "ASSET-002", "PROVIDES", {"contract": "monthly"}),
        ("Supplier", "SUPP-002", "Asset", "ASSET-002", "PROVIDES", {"contract": "quarterly"}),
        # RiskFactor → Customer (AFFECTS)
        ("RiskFactor", "RISK-001", "Customer", "CUST-004", "AFFECTS", {"severity": "high"}),
        ("RiskFactor", "RISK-002", "Supplier", "SUPP-002", "AFFECTS", {"severity": "medium"}),
    ]

    for fl, fid, tl, tid, rel, props in relationships:
        await OntologyService.create_relationship(fl, fid, tl, tid, rel, props)

    print(f"Neo4j seeded: {len(entities)} entities, {len(relationships)} relationships")


async def main():
    await seed_postgres()
    try:
        await seed_neo4j()
    except Exception as e:
        print(f"Neo4j seed warning (may already be seeded or not ready): {e}")


asyncio.run(main())
