import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.main import app
from app.core.config import settings

# Database URL for testing
TEST_DATABASE_URL = settings.DATABASE_URL.replace("mediconsulta", "mediconsulta_test")

@pytest_asyncio.fixture(scope="session")
async def engine():
    # Engine is created once per session
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        
        # Load schema
        with open("db/schemas.sql", "r") as f:
            schema_sql = f.read()
        for statement in schema_sql.split(";"):
            if statement.strip():
                try:
                    await conn.execute(text(statement))
                except Exception:
                    pass
                    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    # Transactional session for EACH test
    async with engine.connect() as connection:
        async with connection.begin() as transaction:
            session_factory = async_sessionmaker(
                bind=connection,
                expire_on_commit=False,
                class_=AsyncSession
            )
            session = session_factory()
            
            yield session
            
            await session.close()
            await transaction.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    from httpx import AsyncClient, ASGITransport
    
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
