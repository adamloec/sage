import requests
import json
from typing import Dict

BASE_URL = "http://localhost:8000/api"

def create_session(llm_config: Dict) -> str:
    """Create a new chat session and return session_id"""
    print("\nCreating new chat session...")
    response = requests.post(
        f"{BASE_URL}/sessions",
        json={"llm_config": llm_config}
    )
    response.raise_for_status()
    session_data = response.json()
    print(f"Session created with ID: {session_data['session_id']}")
    return session_data["session_id"]

def send_message(session_id: str, message: str):
    """Send a message and get the response"""
    print(f"\nSending message: {message}")
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        params={"stream": False},  # Explicitly disable streaming
        json={
            "content": message,
        }
    )
    response.raise_for_status()
    response_data = response.json()
    print("Response:", response_data["message"]["content"])
    return response_data

def main():
    # Extract model name from path
    model_path = "/Users/adam/dev/projects/sage/sage/llm/hf/generation/Qwen2.5-Coder-7B-Instruct"
    model_name = "Qwen2.5-Coder-7B-Instruct"  # Base name of the model
    
    # LLM configuration
    llm_config = {
        "model_name": model_name,  # Required field
        "model_path": model_path,
        "trust_remote_code": False,
        "dtype": "float16",
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95
    }
    
    try:
        # Create a new session
        session_id = create_session(llm_config)
        
        # Test messages
        messages = [
            "Hello! How are you?",
            "What is the capital of France?",
            "Write a short poem about coding."
        ]
        
        # Send each message
        for message in messages:
            send_message(session_id, message)
            input("\nPress Enter to send next message...")  # Pause between messages
            
    except requests.exceptions.RequestException as e:
        print(f"\nError occurred: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main() 