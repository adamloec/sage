from typing import List, Optional

from sage.api.models import ChatMessage, CodeFile
from sage.llm.llm import LLM
from sage.db.db_models import ChatSessionDB

class ChatSession:
    def __init__(self, db_session: ChatSessionDB):
        self.session_id = db_session.id
        self.created_at = db_session.created_at
        self.messages: List[ChatMessage] = [
            ChatMessage(
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp
            ) for msg in db_session.messages
        ]
    
    async def add_message(self, content: str, model: LLM, files: Optional[List[CodeFile]] = None) -> ChatMessage:
        """Process a user message and generate a response"""
        user_message = ChatMessage(role="user", content=content)
        self.messages.append(user_message)
        
        context = content
        if files:
            context += "\n\nProvided files:\n"
            for file in files:
                context += f"\n{file.path}:\n{file.content}\n"
        
        response = await model.generate(context, self.messages)
        
        # Add assistant message
        assistant_message = ChatMessage(
            role="assistant",
            content=response
        )
        self.messages.append(assistant_message)
        
        # Update last_message_at in database
        db_session = await self.db.get(ChatSessionDB, self.session_id)
        if db_session:
            db_session.last_message_at = assistant_message.timestamp
            await self.db.commit()
        
        return assistant_message