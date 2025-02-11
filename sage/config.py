import os
from pathlib import Path
from dotenv import load_dotenv
from sage.api.dto import LLMConfig  # import the Pydantic model

def load_config():
    """Load environment variables from .env file if it exists"""
    load_dotenv()

    # Get the package directory path
    package_dir = Path(__file__).parent
    default_db_path = f"sqlite+aiosqlite:///{package_dir}/chat/db/session_history.db"
    
    # Database configuration
    os.environ.setdefault('SAGE_DB_PATH', default_db_path)

# Load environment variables
load_config() 

# Set the server mode: can be "standalone" or "production"
# You can also override this via the SAGE_MODE environment variable.
MODE = os.getenv("SAGE_MODE", "production")

# Create the production LLM configuration as an instance of LLMConfig
PRODUCTION_LLM_CONFIG = LLMConfig(
    model_name="prod_model",
    model_path="C:/Users/Adam/dev/projects/sage/sage/llm/hf/generation/Qwen2.5-Coder-1.5B-Instruct",
    trust_remote_code=False,
    dtype="float16",
    local_files_only=True,
    use_cache=True,
    return_dict_in_generate=True,
    output_attentions=False,
    output_hidden_states=False,
    low_cpu_mem_usage=False,

    # Generation parameters
    max_new_tokens=512,
    temperature=0.7,
    do_sample=True,
    top_p=0.9,
    top_k=50,
) 