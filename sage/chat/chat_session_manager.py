from typing import Optional, List, Callable, AsyncGenerator
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sage.chat.chat_session import ChatSession
from sage.api.dto import ChatMessage
from sage.chat.db.db_models import ChatSessionDB, ChatMessageDB

class ChatSessionManager:
    
    def __init__(self, get_db: Callable[[], AsyncGenerator[AsyncSession, None]]):
        self.get_db = get_db
        self.sessions: dict[str, ChatSession] = {}
        
    async def load_sessions(self):
        """Load all sessions from database"""
        async with self.get_db() as db:
            query = select(ChatSessionDB)
            result = await db.execute(query)
            db_sessions = result.scalars().all()
            
            for db_session in db_sessions:
                session = ChatSession(db_session)
                await session.load_messages(db)
                self.sessions[db_session.id] = session
    
    async def create_session(self) -> ChatSession:
        """Create a new chat session"""
        async with self.get_db() as db:
            # Create DB record
            db_session = ChatSessionDB(id=str(uuid.uuid4()))
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
            
            # Create memory session
            session = ChatSession(db_session)
            await session.load_messages(db)
            self.sessions[session.session_id] = session
            return session
    
    async def save_message(self, session_id: str, message: ChatMessage):
        """Save a message to the database"""
        async with self.get_db() as db:
            db_message = ChatMessageDB(
                session_id=session_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
            )
            db.add(db_message)
            await db.commit()
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session from memory and database"""
        if session_id in self.sessions:
            async with self.get_db() as db:
                # Delete from database
                query = select(ChatSessionDB).where(ChatSessionDB.id == session_id)
                result = await db.execute(query)
                db_session = result.scalar_one_or_none()
                if db_session:
                    await db.delete(db_session)
                    await db.commit()
                
                # Delete from memory
                del self.sessions[session_id]
            
    async def clear_sessions(self) -> None:
        """Clear sessions from memory (database sessions persist)"""
        self.sessions.clear()