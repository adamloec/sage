from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sage.chat.chat_session import ChatSession
from sage.api.models import ChatMessage, CodeFile
from sage.db.db_models import ChatSessionDB, ChatMessageDB

class ChatSessionManager:
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sessions: dict[str, ChatSession] = {}
        
    async def load_sessions(self):
        """Load all sessions from database"""
        query = select(ChatSessionDB)
        result = await self.db.execute(query)
        db_sessions = result.scalars().all()
        
        for db_session in db_sessions:
            self.sessions[db_session.id] = ChatSession(db_session)
    
    async def create_session(self) -> ChatSession:
        """Create a new chat session"""
        # Create DB record
        db_session = ChatSessionDB(id=str(uuid.uuid4()))
        self.db.add(db_session)
        await self.db.commit()
        await self.db.refresh(db_session)
        
        # Create memory session
        session = ChatSession(db_session)
        self.sessions[session.session_id] = session
        return session
    
    async def save_message(self, session_id: str, message: ChatMessage, files: Optional[List[CodeFile]] = None):
        """Save a message to the database"""
        db_message = ChatMessageDB(
            session_id=session_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            files=[file.model_dump() for file in files] if files else None
        )
        self.db.add(db_message)
        await self.db.commit()
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a chat session from memory and database"""
        if session_id in self.sessions:
            # Delete from database
            query = select(ChatSessionDB).where(ChatSessionDB.id == session_id)
            result = await self.db.execute(query)
            db_session = result.scalar_one_or_none()
            if db_session:
                await self.db.delete(db_session)
                await self.db.commit()
            
            # Delete from memory
            del self.sessions[session_id]
            
    async def clear_sessions(self) -> None:
        """Clear sessions from memory (database sessions persist)"""
        self.sessions.clear()