from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from sage.llm.llm_manager import LLMManager
from sage.chat.chat_session_manager import ChatSessionManager
from sage.api.chat_router import router as chat_router
from sage.db.database import init_db, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers as app state

    # Initialize database
    await init_db()
    
    # Get database session
    db: AsyncSession = next(get_db())

    app.state.llm_manager = LLMManager()
    app.state.chat_session_manager = ChatSessionManager(db)

    yield
    
    # Cleanup on shutdown
    app.state.llm_manager.unload_model()
    app.state.chat_session_manager.clear_sessions()


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(chat_router, prefix="/api")