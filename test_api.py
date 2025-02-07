import requests
import json
from typing import Dict

BASE_URL = "http://localhost:8000/api"

def initialize_llm(llm_config: Dict) -> None:
    """Initialize the LLM with the given configuration"""
    print("\nInitializing LLM...")
    response = requests.put(
        f"{BASE_URL}/llm",
        json=llm_config
    )
    response.raise_for_status()
    print("LLM initialized successfully")

def create_session() -> str:
    """Create a new chat session and return session_id"""
    print("\nCreating new chat session...")
    response = requests.post(f"{BASE_URL}/sessions")
    response.raise_for_status()
    session_data = response.json()
    print(f"Session created with ID: {session_data['session_id']}")
    return session_data["session_id"]

def send_message(session_id: str, message: str, stream: bool = True):
    """Send a message and get the response"""
    print(f"\nSending message: {message}")
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        params={"stream": stream},
        json={
            "content": message,
        },
        stream=True  # Enable requests streaming
    )
    response.raise_for_status()
    
    if stream:
        print("Response: ", end="", flush=True)
        for line in response.iter_lines():
            if line:
                # Remove "data: " prefix and decode
                line = line.decode('utf-8').removeprefix('data: ')
                if line == '[DONE]':
                    break
                print(line, end="", flush=True)
        print()  # New line after response
        return None
    else:
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
        # Initialize the LLM
        initialize_llm(llm_config)
        
        # Create a new session
        session_id = create_session()
        
        # Test messages
        messages = [
            "Write a cuda kernal that adds two numbers.",
            "Write a python script for the fibonacci sequence.",
            "Write a short poem about coding."
        ]
        
        # Send each message
        for message in messages:
            send_message(session_id, message, stream=True)  # Enable streaming by default
            input("\nPress Enter to send next message...")  # Pause between messages
            
    except requests.exceptions.RequestException as e:
        print(f"\nError occurred: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    main() 