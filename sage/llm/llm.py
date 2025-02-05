from typing import List

from sage.api.models import ChatMessage, ModelConfig

class LLM:
    def __init__(self, config: ModelConfig):
        self.config = config
        # Initialize model here based on config
        self._model = None  # This would be the actual model instance

    async def generate(self, prompt: str, history: List[ChatMessage]) -> str:
        """Generate a response given the prompt and chat history"""
        # Here you'd implement the actual model inference
        return "Model response would go here"
        
    def unload(self) -> None:
        """Cleanup model resources"""
        if self._model is not None:
            # Implement actual model cleanup
            self._model = None