import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """Load environment variables from .env file if it exists"""
    load_dotenv()

    # Get the package directory path
    package_dir = Path(__file__).parent
    default_db_path = f"sqlite+aiosqlite:///{package_dir}/chat/db/session_history.db"
    
    # Database configuration
    os.environ.setdefault('SAGE_DB_PATH', default_db_path)

load_config() 