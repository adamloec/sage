from typing import Optional
from langchain_core.language_models.llms import LLM

from sage.api.models import ModelConfig

class SageLLM(LLM):

    model_config: Optional[ModelConfig] = None
