from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from sage.llm.llm_manager import LLMManager
from sage.chat.chat_session_manager import ChatSessionManager
from sage.chat.db.database import init_db, get_db
from sage.api.chat_router import router as chat_router
from sage.api.llm_router import router as llm_router

import sage.config as config

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers as app state

    # Initialize database
    await init_db()
    
    app.state.llm_manager = LLMManager()
    app.state.chat_session_manager = ChatSessionManager(get_db)

    yield
    
    # Cleanup on shutdown
    app.state.llm_manager.remove_llm()
    app.state.chat_session_manager.clear_sessions()


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(llm_router, prefix="/api")

def run():
    uvicorn.run(
        "sage.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    run()