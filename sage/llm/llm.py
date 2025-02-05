from typing import Optional, List, Any, Dict, Callable
from langchain_core.language_models.llms import LLM

from sage.api.models import ModelConfig

class SageLLM(LLM):

    model_config: Optional[ModelConfig] = None

    _model: Optional[AutoModelForCausalLM] = None
    _tokenizer: Optional[AutoTokenizer] = None

    def _load_model(self):
        self._tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=self.model_config["model_path"],
            trust_remote_code=self.model_config.get("trust_remote_code", False),
            local_files_only=self.model_config.get("local_files_only", True)
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=self.model_config["model_path"],
            trust_remote_code=self.model_config.get("trust_remote_code", False),
            local_files_only=self.model_config.get("local_files_only", True),
            use_cache=self.model_config.get("use_cache", True),
            torch_dtype=self.model_config.get("dtype", torch.float16),
            return_dict_in_generate=self.model_config.get("return_dict_in_generate"),
            output_attentions=self.model_config.get("output_attentions"),
            output_hidden_states=self.model_config.get("output_hidden_states"),
            low_cpu_mem_usage=self.model_config.get("low_cpu_mem_usage"),
            device_map=f"cuda:",
        )

    def _deload_model(self):
        del self._model
        del self._tokenizer


    def _call(self, 
              prompt: str, 
              stop: Optional[List[str]] = None, 
              run_manager: Optional[Callable] = None, 
              **kwargs: Any) -> str:

        # Load generation model
        self._load_model()

        # Inference
        encoded_input = self.tokenizer(
                prompt,
                return_tensors="pt",
            )
        
        with torch.inference_mode():
            generation_config = {
                "use_cache": self.model_config.get("use_cache", True),


                "max_new_tokens": self.model_config.get("max_new_tokens", 512),
                "do_sample": self.model_config.get("do_sample", True),
                "temperature": self.model_config.get("temperature", 0.01),
                "top_p": self.model_config.get("top_p", 0.1),

                "top_k":self.model_config.get("top_k", 20),


                "pad_token_id": self.tokenizer.pad_token_id,
            }

            output = self.model.generate(
                **encoded_input,
                **generation_config
            )

        # deload
        self._deload_model()

        


    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_config": self.model_config}
