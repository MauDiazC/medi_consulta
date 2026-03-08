from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.notes.signing.repository import SigningRepository
from app.core.audit import audit_log

class RetentionPolicyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SigningRepository(db)

    def calculate_retention_period(self, organization_period_years: int = 5) -> datetime:
        """
        Phase 3: Automatic Retention Calculation.
        Enforces NOM-004 floor (5 years) vs Organization settings.
        """
        years = max(5, organization_period_years)
        return datetime.now(timezone.utc) + timedelta(days=365 * years)

    async def apply_legal_hold(self, entity_type: str, entity_id: str, executor_id: str, reason: str):
        """
        Phase 4: Audited Legal Hold Governance.
        """
        await self.repo.update_snapshot_archival(entity_id, status="active", legal_hold=True)
        await audit_log(
            self.db, entity_type, entity_id, "LEGAL_HOLD_PLACED", executor_id,
            metadata={"reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        await self.db.commit()

    async def release_legal_hold(self, entity_type: str, entity_id: str, executor_id: str, reason: str):
        """
        Phase 4: Audited Legal Hold Governance.
        """
        await self.repo.update_snapshot_archival(entity_id, status="active", legal_hold=False)
        await audit_log(
            self.db, entity_type, entity_id, "LEGAL_HOLD_RELEASED", executor_id,
            metadata={"reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        await self.db.commit()
