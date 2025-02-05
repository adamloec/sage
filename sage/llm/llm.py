from typing import List

from sage.api.models import ChatMessage, ModelConfig

class LLM:
    def __init__(self, config: ModelConfig):
        self.config = config
        # Initialize model here based on config
        self._model = None  # This would be the actual model instance


    # def load(self) -> None:
    #     """Load the model"""
    #     if self.config.model_type == "generation":
    #         self._model = AutoModelForCausalLM.from_pretrained(self.config.model_path)
    #     elif self.config.model_type == "embedding":
    #         self._model = sentence_transformers.SentenceTransformer(self.config.model_path)

    def unload(self) -> None:
        """Cleanup model resources"""

        if self._model is not None:
            # Implement actual model cleanup
            self._model = None
    
    def inference(self, prompt: str, history: List[ChatMessage]) -> str:
        """Generate a response given the prompt and chat history"""
        # Here you'd implement the actual model inference
        return "Model response would go here"
    
    def generate_embeddings(self, texts: List[str]) -> List[float]:
        """Generate embeddings for a list of texts"""
        if self.config.model_type == "embedding":
            return []
        else:
            raise ValueError("Model type is not supported for embedding generation")