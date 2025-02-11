from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """Configuration for an LLM model"""
    model_name: str
    model_path: Optional[str] = None
    
    # Core model parameters
    trust_remote_code: Optional[bool] = False
    dtype: Optional[str] = "float16"
    local_files_only: Optional[bool] = True
    use_cache: Optional[bool] = True
    return_dict_in_generate: Optional[bool] = True
    output_attentions: Optional[bool] = False
    output_hidden_states: Optional[bool] = False
    low_cpu_mem_usage: Optional[bool] = True
    
    # Generation parameters
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None
    do_sample: Optional[bool] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None

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

class ChatSessionResponse(ApiResponse):
    """Response model for chat session operations"""
    session_id: str
    created_at: datetime
    last_message_at: Optional[datetime] = None
    llm_config: LLMConfig
    messages: List[ChatMessage] = []

class ChatMessageRequest(ApiRequest):
    """Request model for sending a message in a chat session"""
    content: str

class ChatMessageResponse(ApiResponse):
    """Response model for chat messages"""
    message: ChatMessage
    session_id: str

class ChatSessionSummary(BaseModel):
    session_id: str = Field(..., description="The ID of the chat session")
    created_at: datetime = Field(..., description="When the session was created")
    last_message_at: Optional[datetime] = Field(
        None, description="Timestamp of the last message in the session"
    )