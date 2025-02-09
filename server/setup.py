import platform
from setuptools import setup, find_packages 

def get_torch_requirements():
    system = platform.system().lower()
    
    print(f"\nDetecting system configuration for PyTorch installation...")
    
    # macOS - use default PyPI package for MPS support
    if system == "darwin":
        print("macOS detected: Installing PyTorch with MPS support")
        return ["torch", "torchvision", "torchaudio"]
    
    # For Windows and Linux, we'll need to install torch separately
    print("Windows/Linux detected: PyTorch will need to be installed separately with CUDA support")
    return []  # Return empty list to skip torch installation in setup.py

setup(
    name="sage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        *get_torch_requirements(),
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "transformers",
        "pydantic",
        "aiosqlite",
        "python-dotenv",
        "greenlet",
        "click",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "sage=sage.cli:cli",
        ],
    }
) 