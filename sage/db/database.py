from pathlib import Path
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sage.db.db_models import Base

# Get database path from environment or use default
package_dir = Path(__file__).parent
default_db_path = f"sqlite+aiosqlite:///{package_dir}/session_history.db"
DB_PATH = os.environ.get('SAGE_DB_PATH', default_db_path)

# Ensure the database directory exists
db_url = DB_PATH.replace('sqlite+aiosqlite:///', '')
os.makedirs(os.path.dirname(db_url), exist_ok=True)

engine = create_async_engine(
    DB_PATH,
    echo=False,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for FastAPI (async generator)."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

class DBContextManager:
    def __init__(self, async_gen):
        self.async_gen = async_gen
        self._session = None

    async def __aenter__(self):
        # Get the next item from the async generator
        self._session = await self.async_gen.__anext__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, tb):
        await self.async_gen.aclose()

def get_db_cm():
    return DBContextManager(get_db())