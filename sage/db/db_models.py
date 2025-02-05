from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON
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
    files: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    session: Mapped[ChatSessionDB] = relationship(back_populates="messages")