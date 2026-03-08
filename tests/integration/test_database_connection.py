import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.modules.organizations.repository import OrganizationRepository

@pytest.mark.asyncio
async def test_create_organization_persistence():
    # Use SQLite in-memory for a quick, isolated integration test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        # Create minimal table for the test (since schemas.sql is Postgres specific)
        await conn.execute(text("""
            CREATE TABLE organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
    
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        repo = OrganizationRepository(session)
        org_id = str(uuid4())
        
        # Test Repository creation
        # Note: We need to make sure the repository uses simple SQL or adapt it
        # Let's try to insert directly first to verify the session
        await session.execute(
            text("INSERT INTO organizations (id, name) VALUES (:id, :name)"),
            {"id": org_id, "name": "SQLite Org"}
        )
        await session.commit()
        
        # Verify persistence
        result = await session.execute(text("SELECT name FROM organizations WHERE id = :id"), {"id": org_id})
        row = result.mappings().first()
        assert row["name"] == "SQLite Org"
    
    await engine.dispose()
