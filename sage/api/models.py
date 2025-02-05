from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    """Configuration for an LLM model"""
    model_name: str
    model_type: Literal["generation", "embedding"] = "generation"
    model_path: Optional[str] = None # allows user to add model
    
    # Model loading parameters
    trust_remote_code: Optional[bool] = None
    local_files_only: Optional[bool] = None
    use_cache: Optional[bool] = None
    dtype: Optional[str] = "float16"
    
    # Model generation improvement parameters
    return_dict_in_generate: Optional[bool] = None
    output_attentions: Optional[bool] = None
    output_hidden_states: Optional[bool] = None
    low_cpu_mem_usage: Optional[bool] = None
    
    # Generation config
    max_model_len: Optional[int] = None
    max_tokens: Optional[int] = None
    do_sample: Optional[bool] = None

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None


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