from fastapi import APIRouter, HTTPException, Request
from sage.api.dto import LLMConfig
from typing import Dict, Optional
from sage.chat.db.db_models import LLMConfigDB
from sage.chat.db.database import get_db
from sqlalchemy import select

router = APIRouter()

@router.put("/llm", response_model=LLMConfig)
async def set_llm(request: Request, llm_config: LLMConfig):
    """Update the current llm for all sessions"""
    try:
        # Validate required fields
        if not llm_config.model_name or not llm_config.model_path:
            raise ValueError("model_name and model_path are required fields")
            
        request.app.state.llm_manager.set_llm(llm_config)
        return llm_config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update model: {str(e)}"
        )
    
@router.delete("/llm")
async def remove_llm(request: Request):
    """Delete the current llm for all sessions"""
    try:
        request.app.state.llm_manager.remove_llm()
        return {"message": "LLM removed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove model: {str(e)}"
        )

@router.get("/llm", response_model=Optional[LLMConfig])
async def get_llm(request: Request):
    """Get the current llm configuration"""
    try:
        config = request.app.state.llm_manager.get_current_llm()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model configuration: {str(e)}"
        )

@router.get("/llm/configs")
async def get_llm_configs(request: Request):
    """Get all saved LLM configurations"""
    async with get_db() as session:
        result = await session.execute(select(LLMConfigDB))
        configs = result.scalars().all()
        return configs

@router.post("/llm/configs")
async def create_llm_config(request: Request, config: LLMConfig):
    """Save a new LLM configuration"""
    async with get_db() as session:
        db_config = LLMConfigDB(**config.dict())
        session.add(db_config)
        await session.commit()
        return db_config

@router.delete("/llm/configs/{config_id}")
async def delete_llm_config(request: Request, config_id: int):
    """Delete a saved LLM configuration"""
    async with get_db() as session:
        config = await session.get(LLMConfigDB, config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
        await session.delete(config)
        await session.commit()
        return {"message": "Configuration deleted successfully"}