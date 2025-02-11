from datetime import datetime, UTC
from typing import List
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class UserDB(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationship to chat sessions
    sessions: Mapped[List["ChatSessionDB"]] = relationship(
        "ChatSessionDB", back_populates="user", cascade="all, delete-orphan"
    )

class ChatSessionDB(Base):
    __tablename__ = "chat_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    # Now, use a foreign key to reference the user which owns this session
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    last_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    messages: Mapped[List["ChatMessageDB"]] = relationship(
        "ChatMessageDB", back_populates="session", cascade="all, delete-orphan"
    )
    
    # Relationship to the user record
    user: Mapped["UserDB"] = relationship("UserDB", back_populates="sessions")

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    
    session: Mapped[ChatSessionDB] = relationship("ChatSessionDB", back_populates="messages")

class LLMConfigDB(Base):
    __tablename__ = "llm_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String, unique=True)
    model_path: Mapped[str] = mapped_column(String, nullable=True)
    
    # Core model parameters
    trust_remote_code: Mapped[bool] = mapped_column(Boolean, default=False)
    dtype: Mapped[str] = mapped_column(String, default="float16")
    local_files_only: Mapped[bool] = mapped_column(Boolean, default=True)
    use_cache: Mapped[bool] = mapped_column(Boolean, default=True)
    return_dict_in_generate: Mapped[bool] = mapped_column(Boolean, default=True)
    output_attentions: Mapped[bool] = mapped_column(Boolean, default=False)
    output_hidden_states: Mapped[bool] = mapped_column(Boolean, default=False)
    low_cpu_mem_usage: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Generation parameters
    max_new_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)
    do_sample: Mapped[bool] = mapped_column(Boolean, nullable=True)
    top_p: Mapped[float] = mapped_column(Float, nullable=True)
    top_k: Mapped[int] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))