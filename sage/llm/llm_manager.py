from typing import Any, Optional

from sage.api.models import ModelConfig
from sage.llm.llm import LLM

class LLMManager:
    def __init__(self):
        self._current_model: Optional[LLM] = None
        
    def load_model(self, config: ModelConfig) -> LLM:
        """Load a new model, unloading any existing one"""
        if (self._current_model is not None and 
            self._current_model.config.dict() == config.dict()):
            return self._current_model
            
        self.unload_current_model()
        self._current_model = LLM(config)
        return self._current_model

    async def get_current_model(self) -> Optional[LLM]:
        """Get the currently loaded model"""
        if not self._current_model:
            raise Exception("No model currently loaded")
        return self._current_model

    def get_current_config(self) -> Optional[ModelConfig]:
        """Get the current model's configuration"""
        return self._current_model.config if self._current_model else None

    def unload_current_model(self) -> None:
        """Unload the current model and free resources"""
        if self._current_model:
            self._current_model.unload()
            self._current_model = None