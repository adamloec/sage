from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import signal
import sys

from sage.llm.llm_manager import LLMManager
from sage.chat.chat_session_manager import ChatSessionManager
from sage.chat.db.database import init_db, get_db
from sage.api.chat_router import router as chat_router
from sage.api.llm_router import router as llm_router

import sage.config as config

shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers as app state

    # Initialize database
    await init_db()
    
    app.state.llm_manager = LLMManager()
    app.state.chat_session_manager = ChatSessionManager(get_db)

    yield
    
    # Cleanup on shutdown
    await app.state.llm_manager.remove_llm()
    await app.state.chat_session_manager.clear_sessions()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/shutdown")
async def shutdown():
    """Gracefully shutdown the server"""
    print("Shutdown requested - initiating graceful shutdown")
    
    # Cleanup resources
    await app.state.llm_manager.remove_llm()
    await app.state.chat_session_manager.clear_sessions()
    
    # Set shutdown event
    shutdown_event.set()
    
    return {"message": "Server shutting down"}

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(llm_router, prefix="/api")

def run(host, port, reload):
    print(f"Starting Sage server on {host}:{port}")
    
    config = uvicorn.Config(
        "sage.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    # Handle shutdown signal
    async def watch_shutdown():
        await shutdown_event.wait()
        server.should_exit = True
        await server.shutdown()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"Received signal {signum}")
        asyncio.create_task(shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Run the server with shutdown watcher
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(
                server.serve(),
                watch_shutdown()
            )
        )
    except Exception as e:
        print(f"Server failed to start: {e}")
        raise
    finally:
        print("Server shutdown complete")