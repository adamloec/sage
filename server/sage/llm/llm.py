from typing import Optional, List, Any, Dict, Callable, Iterator
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
import gc
from threading import Thread

from sage.api.dto import LLMConfig, ChatMessage

class SageLLM:

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config

        self._llm: Optional[AutoModelForCausalLM] = None
        self._tokenizer: Optional[AutoTokenizer] = None
        self._device: Optional[torch.device] = None

    def load_llm(self):
        # Determine the best available device
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self._device = torch.device("mps")
        else:
            self._device = torch.device("cpu")

        self._tokenizer = AutoTokenizer.from_pretrained(
            pretrained_model_name_or_path=self.llm_config.model_path,
            trust_remote_code=self.llm_config.trust_remote_code or False,
            local_files_only=True  # Consider adding to LLMConfig if configurable
        )

        self._llm = AutoModelForCausalLM.from_pretrained(
            pretrained_model_name_or_path=self.llm_config.model_path,
            trust_remote_code=self.llm_config.trust_remote_code or False,
            local_files_only=True,  # Consider adding to LLMConfig if configurable
            use_cache=True,  # Consider adding to LLMConfig if configurable
            torch_dtype=getattr(torch, self.llm_config.dtype),  # Convert string to torch dtype
            return_dict_in_generate=True,  # Consider adding to LLMConfig if configurable
            output_attentions=False,  # Consider adding to LLMConfig if configurable
            output_hidden_states=False,  # Consider adding to LLMConfig if configurable
            low_cpu_mem_usage=True,  # Consider adding to LLMConfig if configurable
            device_map="auto",  # Enable automatic device mapping
        ).to(self._device)

    def deload_llm(self):
        try:
            # Clear model and tokenizer
            if self._llm is not None:
                self._llm.cpu()  # Move model to CPU first
                del self._llm
                self._llm = None
            if self._tokenizer is not None:
                del self._tokenizer
                self._tokenizer = None
            
            # Clear device-specific caches
            if self._device is not None:
                device_type = self._device.type
                if device_type == 'cuda':
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()
                elif device_type == 'mps':
                    torch.mps.empty_cache()
                self._device = None

            gc.collect()

        except Exception as e:
            print(f"Warning: Error during model deallocation: {str(e)}")

    def inference(self, prompt: str, message_history: List[ChatMessage]) -> str:

        try:
            # Inference
            encoded_input = self._tokenizer(
                prompt,
                return_tensors="pt",
            ).to(self._device)
            
            with torch.inference_mode():
                generation_config = {
                    "use_cache": self.llm_config.use_cache,
                    "max_new_tokens": self.llm_config.max_new_tokens,
                    "do_sample": self.llm_config.do_sample,
                    "temperature": self.llm_config.temperature,
                    "top_p": self.llm_config.top_p,
                    "top_k": self.llm_config.top_k,
                    "pad_token_id": self._tokenizer.pad_token_id,
                }

                outputs = self._llm.generate(
                    **encoded_input,
                    **generation_config
                )
                
                # Decode the generated text
                generated_text = self._tokenizer.decode(outputs[0][encoded_input.input_ids.shape[1]:], skip_special_tokens=True)

            return generated_text
        
        except Exception as e:
            self.deload_llm()
            raise e
        
    async def stream_inference(self, prompt: str, message_history: List[ChatMessage]):
        try:
            # Inference
            encoded_input = self._tokenizer(
                prompt,
                return_tensors="pt",
            ).to(self._device)

            streamer = TextIteratorStreamer(
                tokenizer=self._tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )

            # Start generation in a separate thread
            generation_kwargs = {
                **encoded_input,
                "use_cache": self.llm_config.use_cache,
                "max_new_tokens": self.llm_config.max_new_tokens,
                "do_sample": self.llm_config.do_sample,
                "temperature": self.llm_config.temperature,
                "top_p": self.llm_config.top_p,
                "top_k": self.llm_config.top_k,
                "pad_token_id": self._tokenizer.pad_token_id,
                "streamer": streamer,
            }

            thread = Thread(target=self._llm.generate, kwargs=generation_kwargs)
            thread.start()

            # Yield tokens as they become available
            for new_text in streamer:
                yield new_text

        except Exception as e:
            self.deload_llm()
            raise e
