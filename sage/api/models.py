from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    model_name: str
    model_type: Literal["generation", "embedding"] = "generation"
    model_path: Optional[str] = None
    
    # Core model parameters
    trust_remote_code: Optional[bool] = None
    dtype: Optional[str] = "float16"
    
    # Generation parameters
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None

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

# Base request/response types
class ApiRequest(BaseModel):
    """Base class for API requests"""
    pass

class ApiResponse(BaseModel):
    """Base class for API responses"""
    pass

# Chat session models
class ChatSessionRequest(ApiRequest):
    """Request model for creating a new chat session"""
    model_config: ModelConfig

class ChatSessionResponse(ApiResponse):
    """Response model for chat session operations"""
    session_id: str
    created_at: datetime
    last_message_at: Optional[datetime] = None
    model_config: ModelConfig
    messages: List[ChatMessage] = []

class ChatMessageRequest(ApiRequest):
    """Request model for sending a message in a chat session"""
    content: str
    files: List[CodeFile] = []

class ChatMessageResponse(ApiResponse):
    """Response model for chat messages"""
    message: ChatMessage
    session_id: str

class ChatSummary(ApiResponse):
    """Summary of a chat session for display"""
    session_id: str
    created_at: datetime
    first_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    message_count: int