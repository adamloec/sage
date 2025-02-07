from fastapi import APIRouter, HTTPException, Request
from typing import List
from sage.api.dto import (
    ChatSessionRequest,
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    LLMConfig,
)
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.put("/llm", response_model=LLMConfig)
async def update_llm(request: Request, llm_config: LLMConfig):
    """Update the current llm for all sessions"""
    try:
        request.app.state.llm_manager.set_llm(llm_config)
        return llm_config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update model: {str(e)}"
        )

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(request: Request):
    """Create a new chat session"""
    
    session = await request.app.state.chat_session_manager.create_session()
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        llm_config=request.app.state.llm_manager.get_current_config(),
        messages=session.messages
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(request: Request, session_id: str):
    """Get an existing chat session"""
    session = request.app.state.chat_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        llm_config=request.app.state.llm_manager.get_current_config(),
        messages=session.messages
    )

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    request: Request, 
    session_id: str, 
    msg_request: ChatMessageRequest,
    stream: bool = True
):
    """Send a message in a chat session"""
    session = request.app.state.chat_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if stream:
        return StreamingResponse(
            session.stream_message(
                msg_request.content,
                request.app.state.llm_manager.get_current_llm()
            ),
            media_type='text/event-stream'
        )
    else:
        async with request.app.state.chat_session_manager.get_db() as db:
            response = await session.add_message(
                msg_request.content,
                request.app.state.llm_manager.get_current_llm(),
                db
            )
            return ChatMessageResponse(
                message=response,
                session_id=session_id
            )

# @router.delete("/sessions/{session_id}")
# async def delete_chat_session(request: Request, session_id: str):
#     """Delete a chat session"""
#     session = request.app.state.session_manager.get_session(session_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")
    
#     request.app.state.session_manager.delete_session(session_id)
#     return {"status": "success", "message": "Chat session deleted"}