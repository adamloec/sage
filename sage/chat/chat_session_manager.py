from typing import Optional, List, Callable
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sage.chat.chat_session import ChatSession
from sage.db.db_models import ChatSessionDB

class ChatSessionManager:
    
    def __init__(self, get_db: Callable[[], object]):
        self.get_db = get_db
        
    async def load_sessions(self):
        """Optionally preload sessions from the database.
           This method is less useful if you're not caching sessions,
           but can be used if you need to iterate over all sessions.
        """
        async with self.get_db() as db:
            query = select(ChatSessionDB)
            result = await db.execute(query)
            db_sessions = result.scalars().all()
            sessions = []
            for db_session in db_sessions:
                session = ChatSession(db_session)
                await session.load_messages(db)
                sessions.append(session)
            return sessions
            
    async def create_session(self, user_id: str) -> ChatSession:
        """Create a new chat session for a given user_id"""
        async with self.get_db() as db:
            db_session = ChatSessionDB(id=str(uuid.uuid4()), user_id=user_id)
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
            
            session = ChatSession(db_session)
            await session.load_messages(db)
            return session
            
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Retrieve a chat session from the database"""
        async with self.get_db() as db:
            query = select(ChatSessionDB).where(ChatSessionDB.id == session_id)
            result = await db.execute(query)
            db_session = result.scalar_one_or_none()
            if db_session is None:
                return None
            session = ChatSession(db_session)
            await session.load_messages(db)
            return session
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session from the database"""
        async with self.get_db() as db:
            query = select(ChatSessionDB).where(ChatSessionDB.id == session_id)
            result = await db.execute(query)
            db_session = result.scalar_one_or_none()
            if db_session:
                await db.delete(db_session)
                await db.commit()
            
    async def get_sessions_by_user(self, user_id: str) -> List[ChatSession]:
        """Retrieve all chat sessions associated with a user_id."""
        async with self.get_db() as db:
            query = select(ChatSessionDB).where(ChatSessionDB.user_id == user_id)
            result = await db.execute(query)
            db_sessions = result.scalars().all()
            sessions = []
            for db_session in db_sessions:
                session = ChatSession(db_session)
                await session.load_messages(db)
                sessions.append(session)
            return sessions