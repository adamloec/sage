from typing import Optional, List, Callable
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sage.chat.chat_session import ChatSession
from sage.api.dto import ChatMessage
from sage.chat.db.db_models import ChatSessionDB

class ChatSessionManager:
    
    def __init__(self, get_db: Callable[[], object]):
        # get_db is expected to be a function returning an async context manager.
        self.get_db = get_db
        self.sessions: dict[str, ChatSession] = {}
        
    async def load_sessions(self):
        """Load all sessions from the database"""
        async with self.get_db() as db:
            query = select(ChatSessionDB)
            result = await db.execute(query)
            db_sessions = result.scalars().all()
            for db_session in db_sessions:
                session = ChatSession(db_session)
                await session.load_messages(db)
                self.sessions[db_session.id] = session
            
    async def create_session(self, user_id: str) -> ChatSession:
        """Create a new chat session for a given user_id"""
        async with self.get_db() as db:
            db_session = ChatSessionDB(id=str(uuid.uuid4()), user_id=user_id)
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
            
            session = ChatSession(db_session)
            await session.load_messages(db)
            self.sessions[session.session_id] = session
            return session
            
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session from memory and database"""
        if session_id in self.sessions:
            async with self.get_db() as db:
                query = select(ChatSessionDB).where(ChatSessionDB.id == session_id)
                result = await db.execute(query)
                db_session = result.scalar_one_or_none()
                if db_session:
                    await db.delete(db_session)
                    await db.commit()
                del self.sessions[session_id]
            
    async def clear_sessions(self) -> None:
        """Clear sessions from memory (database sessions persist)"""
        self.sessions.clear()
    
    async def get_sessions_by_user(self, user_id: str) -> List[ChatSession]:
        """Retrieve all chat sessions associated with a user_id."""
        async with self.get_db() as db:
            query = select(ChatSessionDB).where(ChatSessionDB.user_id == user_id)
            result = await db.execute(query)
            db_sessions = result.scalars().all()
            sessions = []
            for db_session in db_sessions:
                if db_session.id in self.sessions:
                    sessions.append(self.sessions[db_session.id])
                else:
                    session = ChatSession(db_session)
                    await session.load_messages(db)
                    self.sessions[db_session.id] = session
                    sessions.append(session)
            return sessions