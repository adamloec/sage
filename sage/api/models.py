from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000

class CodeFile(BaseModel):
    """Code file content and metadata"""
    path: str
    content: str
    language: Optional[str] = None

class ChatMessage(BaseModel):
    """Single message in a chat"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatSessionCreate(BaseModel):
    """Request model for creating a new chat session"""
    model_config: ModelConfig

class ChatSessionResponse(BaseModel):
    """Response model for chat session operations"""
    session_id: str
    created_at: datetime
    last_message_at: Optional[datetime] = None
    model_config: ModelConfig
    messages: List[ChatMessage] = []

class ChatMessageRequest(BaseModel):
    """Request model for sending a message in a chat session"""
    content: str
    files: List[CodeFile] = []

class ChatMessageResponse(BaseModel):
    """Response model for chat messages"""
    message: ChatMessage
    session_id: str

class ChatSummary(BaseModel):
    """Summary of a chat session for display"""
    session_id: str
    created_at: datetime
    first_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    message_count: int