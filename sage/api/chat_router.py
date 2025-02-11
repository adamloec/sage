from fastapi import APIRouter, HTTPException, Request, Header
from typing import List, Optional
from sqlalchemy.future import select

from sage.api.dto import (
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionSummary,
)
from fastapi.responses import StreamingResponse
from sage.db.db_models import ChatSessionDB

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: Request,
    x_user_id: Optional[str] = Header(None)
):
    """Create a new chat session for the specified user"""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    session = await request.app.state.chat_session_manager.create_session(user_id=x_user_id)
    
    if hasattr(request.app.state, "llm_manager"):
        current_config = request.app.state.llm_manager.get_current_config()
    else:
        current_config = request.app.state.production_llm_config
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        llm_config=current_config,
        messages=session.message_history
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(request: Request, session_id: str):
    """Get an existing chat session"""
    session = await request.app.state.chat_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if hasattr(request.app.state, "llm_manager"):
        current_config = request.app.state.llm_manager.get_current_config()
    else:
        current_config = request.app.state.production_llm_config
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        llm_config=current_config,
        messages=session.message_history
    )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    request: Request, 
    session_id: str, 
    msg_request: ChatMessageRequest,
    stream: bool = False
):
    """Send a message in a chat session"""
    session = await request.app.state.chat_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Determine which LLM to use
    if hasattr(request.app.state, "llm_manager"):
        llm = request.app.state.llm_manager.get_current_llm()
    else:
        llm = request.app.state.llm

    inference_lock = getattr(request.app.state, "inference_lock", None)

    if stream:
        async def event_generator():
            async with request.app.state.chat_session_manager.get_db() as db:
                if inference_lock:
                    async with inference_lock:
                        async for token in session.stream_message(
                            msg_request.content,
                            llm,
                            db
                        ):
                            yield f"data: {token}\n\n"
                else:
                    async for token in session.stream_message(
                        msg_request.content,
                        llm,
                        db
                    ):
                        yield f"data: {token}\n\n"
                yield "data: [DONE]\n\n"
        return StreamingResponse(
            event_generator(),
            media_type='text/event-stream'
        )
    else:
        async with request.app.state.chat_session_manager.get_db() as db:
            if inference_lock:
                async with inference_lock:
                    response = await session.add_message(
                        msg_request.content,
                        llm,
                        db
                    )
            else:
                response = await session.add_message(
                    msg_request.content,
                    llm,
                    db
                )
        return ChatMessageResponse(
            message=response,
            session_id=session_id
        )

@router.get("/sessions", response_model=List[ChatSessionSummary])
async def list_chat_sessions(
    request: Request,
    x_user_id: Optional[str] = Header(None)
):
    """List all chat sessions for the specified user in descending order by last_message_at."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    async with request.app.state.chat_session_manager.get_db() as db:
        query = (
            select(ChatSessionDB)
            .where(ChatSessionDB.user_id == x_user_id)
            .order_by(ChatSessionDB.last_message_at.desc())
        )
        result = await db.execute(query)
        sessions = result.scalars().all()
    
    summaries = [
        ChatSessionSummary(
            session_id=session.id,
            created_at=session.created_at,
            last_message_at=session.last_message_at,
        )
        for session in sessions
    ]
    return summaries

@router.delete("/sessions/{session_id}")
async def delete_chat_session(request: Request, session_id: str):
    """Delete a chat session"""
    session = await request.app.state.chat_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await request.app.state.chat_session_manager.delete_session(session_id)
    return {"status": "success", "message": "Chat session deleted"}