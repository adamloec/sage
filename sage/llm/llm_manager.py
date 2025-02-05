from typing import Any, Optional, Literal

from sage.api.models import ModelConfig
from sage.llm.llm import SageLLM
from sage.llm.embeddings import SageEmbeddings

class LLMManager:
    def __init__(self):
        self._current_model: Optional[SageLLM] = None
        self._current_config: Optional[ModelConfig] = None
        self._current_embeddings: Optional[SageEmbeddings] = None

    def set_llm(self, config: ModelConfig) -> SageLLM:
        if self._current_config != config:

            self._current_model = SageLLM(config)
            self._current_config = config

        return self._current_model
        
    def set_embeddings(self) -> SageEmbeddings:
        if self._current_embeddings is None:
            self._current_embeddings = SageEmbeddings()
            
        return self._current_embeddings

    def get_current_llm(self) -> Optional[SageLLM]:
        return self._current_model

    def get_current_embeddings(self) -> Optional[SageEmbeddings]:
        return self._current_embeddings

    def get_current_config(self) -> Optional[ModelConfig]:
        return self._current_model.config if self._current_model else None