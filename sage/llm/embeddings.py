from typing import List

class SageEmbeddings:

    embedding_model_name: str = "stella"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    def embed_query(self, text: str) -> List[float]:
        pass