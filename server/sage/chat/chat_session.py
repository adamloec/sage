from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sage.api.dto import ChatMessage, LLMConfig
from sage.llm.llm import SageLLM
from sage.chat.db.db_models import ChatSessionDB, ChatMessageDB

class ChatSession:
    def __init__(self, db_session: ChatSessionDB):
        self.session_id = db_session.id
        self.created_at = db_session.created_at
        self.last_message_at = db_session.last_message_at
        self.message_history: List[ChatMessage] = []
        self.llm_config: Optional[LLMConfig] = None

    async def load_messages(self, db: AsyncSession):
        """Load messages from database"""
        query = select(ChatMessageDB).where(ChatMessageDB.session_id == self.session_id)
        result = await db.execute(query)
        db_messages = result.scalars().all()
        
        self.message_history = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ) for msg in db_messages
        ]

    async def update_session_database(self, user_message: ChatMessage, assistant_message: ChatMessage, db: AsyncSession):
        """Update the database with the new messages"""
        db_user_message = ChatMessageDB(
            session_id=self.session_id,
            role=user_message.role,
            content=user_message.content,
            timestamp=user_message.timestamp
        )
        db.add(db_user_message)

        db_assistant_message = ChatMessageDB(
            session_id=self.session_id,
            role=assistant_message.role,
            content=assistant_message.content,
            timestamp=assistant_message.timestamp
        )
        db.add(db_assistant_message)

        query = select(ChatSessionDB).where(ChatSessionDB.id == self.session_id)
        result = await db.execute(query)
        db_session = result.scalar_one()
        db_session.last_message_at = assistant_message.timestamp
        
        await db.commit()

    async def add_message(self, prompt: str, llm: SageLLM, db: AsyncSession) -> ChatMessage:
        """Process a user message and generate a response"""
        
        # Generate response using the LLM
        message_history = [msg.content for msg in self.message_history]
        response = llm.inference(prompt, message_history)
        
        user_message = ChatMessage(role="user", content=prompt)
        self.message_history.append(user_message)

        assistant_message = ChatMessage(role="assistant", content=response)
        self.message_history.append(assistant_message)
        
        await self.update_session_database(user_message, assistant_message, db)
        
        return assistant_message
    
    async def stream_message(self, prompt: str, llm: SageLLM, db: AsyncSession):
        """Stream a message in a chat session and update database after completion"""
        # Create the user message
        user_message = ChatMessage(role="user", content=prompt)
        self.message_history.append(user_message)
        
        # Stream the response while collecting the full response
        full_response = ""
        message_history = [msg.content for msg in self.message_history]
        
        async for token in llm.stream_inference(prompt, message_history):
            full_response += token
            yield token
        
        # Create the assistant message with the complete response
        assistant_message = ChatMessage(role="assistant", content=full_response)
        self.message_history.append(assistant_message)
        
        # Update the database with both messages
        await self.update_session_database(user_message, assistant_message, db)