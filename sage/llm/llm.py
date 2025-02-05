from typing import Optional, List, Any, Dict, Callable
from langchain_core.language_models.llms import LLM

from sage.api.models import ModelConfig

class SageLLM(LLM):

    model_config: Optional[ModelConfig] = None

    def _call(self, 
              prompt: str, 
              stop: Optional[List[str]] = None, 
              run_manager: Optional[Callable] = None, 
              **kwargs: Any) -> str:
        pass

    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_config": self.model_config}
