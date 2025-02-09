import platform
import subprocess
import sys
import re
from setuptools import setup, find_packages

def get_cuda_version_from_nvcc():
    try:
        output = subprocess.check_output(['nvcc', '--version']).decode('utf-8')
        # Example output: "Cuda compilation tools, release 11.8, V11.8.89"
        match = re.search(r'release (\d+\.\d+)', output)
        if match:
            version = match.group(1)
            return ''.join(version.split('.'))  # e.g., '11.8' -> '118'
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

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