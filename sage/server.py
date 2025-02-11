from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import signal
import sys

from sage.chat.chat_session_manager import ChatSessionManager
from sage.chat.db.database import init_db, get_db_cm
from sage.api.chat_router import router as chat_router
from sage.api.user_router import router as user_router

import sage.config as config

shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize managers as app state

    # Initialize database
    await init_db()
    
    if config.MODE == "production":
        # In production mode: load a single LLM (with static config) and a global inference lock
        from sage.llm.llm import SageLLM  # Use the same SageLLM class
        app.state.llm = SageLLM(llm_config=config.PRODUCTION_LLM_CONFIG)
        app.state.llm.load_llm()  # Permanently load the model
        
        # Store production llm config if you want to expose it in chat responses
        app.state.production_llm_config = config.PRODUCTION_LLM_CONFIG
        
        # Create a lock to ensure only one inference runs at a time
        app.state.inference_lock = asyncio.Lock()
        
        # Use the context-manager based DB helper:
        app.state.chat_session_manager = ChatSessionManager(get_db_cm)
    else:
        # Standalone mode: full feature set including LLM management
        from sage.llm.llm_manager import LLMManager
        app.state.llm_manager = LLMManager()
        app.state.chat_session_manager = ChatSessionManager(get_db_cm)

    yield
    
    # Cleanup on shutdown
    if config.MODE == "production":
        try:
            app.state.llm.deload_llm()
        except Exception as e:
            print(f"Error cleaning up production LLM: {e}")
        await app.state.chat_session_manager.clear_sessions()
    else:
        from sage.llm.llm_manager import LLMManager
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
    
    try:
        # Clean up resources if they exist
        if hasattr(app.state, 'llm_manager') and app.state.llm_manager is not None:
            try:
                await app.state.llm_manager.remove_llm()
            except Exception as e:
                print(f"Error cleaning up LLM manager: {e}")
                
        if hasattr(app.state, 'chat_session_manager') and app.state.chat_session_manager is not None:
            try:
                await app.state.chat_session_manager.clear_sessions()
            except Exception as e:
                print(f"Error cleaning up chat sessions: {e}")
                
        shutdown_event.set()
        return {"message": "Server shutdown initiated"}
    except Exception as e:
        print(f"Error during shutdown: {e}")
        return {"message": f"Shutdown initiated with errors: {str(e)}"}

# Include the chat router always
app.include_router(chat_router, prefix="/api/chat")

# In standalone mode, include the LLM management router.
if config.MODE != "production":
    from sage.api.llm_router import router as llm_router
    app.include_router(llm_router, prefix="/api")

# Include the user router
app.include_router(user_router, prefix="/api/user")

def run(host, port, reload):
    print(f"Starting Sage server on {host}:{port}")
    
    uvicorn_config = uvicorn.Config(
        "sage.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                }
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",
                }
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
        }
    )
    
    server = uvicorn.Server(uvicorn_config)
    
    async def watch_shutdown():
        await shutdown_event.wait()
        print("Shutdown event received, stopping server...")
        server.should_exit = True
        try:
            await server.shutdown()
        except Exception as e:
            print(f"Error during server shutdown: {e}")
    
    def signal_handler(signum, frame):
        print(f"Received signal {signum}")
        loop = asyncio.get_event_loop()
        loop.create_task(shutdown())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
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
        try:
            loop.close()
        except Exception as e:
            print(f"Error closing event loop: {e}")