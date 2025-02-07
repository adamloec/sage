from fastapi import APIRouter, HTTPException, Request
from sage.api.dto import LLMConfig

router = APIRouter()

@router.put("/llm", response_model=LLMConfig)
async def update_llm(request: Request, llm_config: LLMConfig):
    """Update the current llm for all sessions"""
    try:
        request.app.state.llm_manager.set_llm(llm_config)
        return llm_config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update model: {str(e)}"
        )