import os
from dotenv import load_dotenv

def load_config():
    """Load environment variables from .env file if it exists"""
    load_dotenv()

    # Database configuration
    os.environ.setdefault('SAGE_DB_PATH', 'sqlite+aiosqlite:///server/sage/chat/db/session_history.db')

load_config() 