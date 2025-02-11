import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sage.chat.db.database import get_db
from sage.api.dto import BaseModel, Field

class UserResponse(BaseModel):
    id: str
    created_at: datetime

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_or_get_user(
    x_user_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Automatically check for a user when the frontend connects.
    If a user ID is provided in the x-user-id header and the user exists, return it.
    Otherwise, create a new user record (using the provided ID or generating a new one).
    """
    from sage.chat.db.db_models import UserDB  # Import here to avoid circular dependencies if needed

    if x_user_id:
        # Try to retrieve an existing user with the provided ID
        query = select(UserDB).where(UserDB.id == x_user_id)
        result = await db.execute(query)
        user_obj = result.scalar_one_or_none()
        if user_obj:
            return UserResponse(id=user_obj.id, created_at=user_obj.created_at)
        else:
            # Create a new user using the provided ID (if not found)
            user_obj = UserDB(id=x_user_id)
    else:
        # No user ID provided -- generate a new one
        user_obj = UserDB(id=str(uuid.uuid4()))

    db.add(user_obj)
    try:
        await db.commit()
        await db.refresh(user_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating user")
    return UserResponse(id=user_obj.id, created_at=user_obj.created_at) 