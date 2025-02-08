from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class ChatSessionDB(Base):
    __tablename__ = "chat_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    messages: Mapped[List["ChatMessageDB"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    session: Mapped[ChatSessionDB] = relationship(back_populates="messages")

class LLMConfigDB(Base):
    __tablename__ = "llm_configs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String, unique=True)
    model_path: Mapped[str] = mapped_column(String)
    context_window: Mapped[int] = mapped_column(Integer, default=4096)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    trust_remote_code: Mapped[bool] = mapped_column(Boolean, default=False)
    dtype: Mapped[str] = mapped_column(String, default="float16")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    do_sample: Mapped[bool] = mapped_column(Boolean, default=True)
    top_p: Mapped[float] = mapped_column(Float, default=0.95)
    top_k: Mapped[int] = mapped_column(Integer, default=40)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)