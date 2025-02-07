from typing import Optional

from sage.api.dto import LLMConfig
from sage.llm.llm import SageLLM
from sage.llm.embeddings import SageEmbeddings

class LLMManager:
    def __init__(self):
        self._current_llm: Optional[SageLLM] = None
        self._current_llm_config: Optional[LLMConfig] = None

    def set_llm(self, llm_config: LLMConfig) -> SageLLM:
        if self._current_llm_config != llm_config:
            self.remove_llm()
            self._current_llm = SageLLM(llm_config=llm_config)
            self._current_llm_config = llm_config

        return self._current_llm

    def remove_llm(self):
        if self._current_llm:
            self._current_llm.deload_llm()
            self._current_llm = None
            self._current_llm_config = None

    def get_current_llm(self) -> Optional[SageLLM]:
        return self._current_llm

    def get_current_config(self) -> Optional[LLMConfig]:
        return self._current_llm_config

