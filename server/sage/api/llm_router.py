from fastapi import APIRouter, HTTPException, Request
from sage.api.dto import LLMConfig
from typing import Dict, Optional

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