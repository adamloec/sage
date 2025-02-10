from contextlib import asynccontextmanager
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .db_models import Base

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

@asynccontextmanager
async def get_db():
    """Provide a transactional scope around a series of operations."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()