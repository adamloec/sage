from setuptools import setup, find_packages

setup(
    name="sage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "transformers",
        "torch",
        "pydantic",
        "aiosqlite",
        "langchain",
    ],
    python_requires=">=3.12",
    entry_points={
        "console_scripts": [
            "sage-server=sage.main:run_server",
        ],
    }
) 