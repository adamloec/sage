from fastapi import APIRouter, HTTPException, Request
from typing import List
from sage.api.models import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ModelConfig,
    ChatSummary
)

router = APIRouter()

@router.get("/sessions/summary", response_model=List[ChatSummary])
async def get_chat_summaries(request: Request):
    """Get summaries of all chat sessions"""
    summaries = []
    for session in request.app.state.session_manager.sessions.values():
        # Find first user message if any exist
        first_message = next(
            (msg.content for msg in session.messages if msg.role == "user"),
            None
        )
        
        # Get last message timestamp if messages exist
        last_message_at = session.messages[-1].timestamp if session.messages else None
        
        summaries.append(ChatSummary(
            session_id=session.session_id,
            created_at=session.created_at,
            first_message=first_message,
            last_message_at=last_message_at,
            message_count=len(session.messages)
        ))
    
    summaries.sort(key=lambda x: x.last_message_at, reverse=True)
    return summaries

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(request: Request, create_request: ChatSessionCreate):
    """Create a new chat session"""
    if request.app.state.llm_manager.get_current_llm() is None:
        request.app.state.llm_manager.load_model(create_request.model_config)
    

    session = request.app.state.session_manager.create_session()
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        model_config=request.app.state.llm_manager.get_current_config(),
        messages=session.messages

    )

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(request: Request, session_id: str):
    """Get an existing chat session"""
    session = request.app.state.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ChatSessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        model_config=request.app.state.llm_manager.get_current_config(),
        messages=session.messages
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    request: Request, 
    session_id: str, 
    msg_request: ChatMessageRequest,
    qa_mode: bool = False
):
    """Send a message in a chat session"""
    session = request.app.state.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    response = await session.add_message(
        msg_request.content,
        request.app.state.llm_manager,
        msg_request.files,
        qa_mode=qa_mode
    )

    return ChatMessageResponse(
        message=response,
        session_id=session_id
    )

@router.put("/model", response_model=ModelConfig)
async def update_model(request: Request, model_config: ModelConfig):
    """Update the current model for all sessions"""
    try:
        request.app.state.llm_manager.load_model(model_config)
        return model_config
    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to update model: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(request: Request, session_id: str):
    """Delete a chat session"""
    session = request.app.state.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    request.app.state.session_manager.delete_session(session_id)
    return {"status": "success", "message": "Chat session deleted"}

@router.post("/window-close")
async def handle_window_close(request: Request):
    """Handle VS Code extension window closing"""
    request.app.state.llm_manager.unload_all()
    return {"status": "success", "message": "Window closed, model unloaded"}