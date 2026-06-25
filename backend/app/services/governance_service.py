from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


class GovernanceService:
    @staticmethod
    async def log(
        db: AsyncSession,
        event_type: str,
        entity_type: str,
        description: str,
        entity_id: int = None,
        actor_id: int = None,
        actor_type: str = "user",
        metadata: dict = None,
        ip_address: str = None,
    ):
        entry = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_type=actor_type,
            description=description,
            extra_data=metadata or {},
            ip_address=ip_address,
        )
        db.add(entry)
        await db.flush()
        return entry
