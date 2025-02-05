

class VectorStore:
    def __init__(self, embedding_size: int, persist_directory: Optional[str] = None):
        settings = Settings(persist_directory=persist_directory) if persist_directory else Settings()
        self.client = chromadb.Client(settings)
        self.collection = self.client.create_collection(
            name=f"collection_{uuid.uuid4().hex}",
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_size = embedding_size

    async def add_documents(self, texts: List[str], embeddings: List[List[float]]):
        """Add documents and their embeddings to the store"""
        # Convert document indices to strings for Chroma
        ids = [str(i) for i in range(len(texts))]
        
        # Add documents and embeddings to Chroma
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            ids=ids
        )

    async def similarity_search(self, query_embedding: List[float], k: int = 4) -> List[str]:
        """Find most similar documents using cosine similarity"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        return results['documents'][0]  # Return only the documents