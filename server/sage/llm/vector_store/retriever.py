from typing import List, Optional

from sage.llm.llm_manager import LLMManager
from sage.llm.vector_store.vector_store import VectorStore

class Retriever:
    def __init__(self, llm_manager: LLMManager, persist_directory: Optional[str] = None):
        self.llm_manager = llm_manager
        self.persist_directory = persist_directory
        self.vectorstore: Optional[VectorStore] = None

    async def initialize_vectorstore(self, documents: List[str]):
        """Initialize vector store with documents"""
        embeddings_model = await self.llm_manager.get_embeddings()
        
        # Split documents into chunks
        chunks = self._split_documents(documents)
        
        # Get embeddings for all chunks
        embeddings = await embeddings_model.embed_documents(chunks)
        
        # Initialize and populate vector store
        # We assume the first embedding gives us the embedding size
        self.vectorstore = VectorStore(
            embedding_size=len(embeddings[0]),
            persist_directory=self.persist_directory
        )

        await self.vectorstore.add_documents(chunks, embeddings)

    def _split_documents(self, documents: List[str], chunk_size: int = 1000) -> List[str]:
        """Split documents into smaller chunks"""
        chunks = []
        for doc in documents:
            # Implement your own chunking logic here
            # This is a simple example that splits by character count
            for i in range(0, len(doc), chunk_size):
                chunks.append(doc[i:i + chunk_size])
        return chunks

    async def query(self, question: str) -> str:
        """Run retrieval query"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")

        # Get embeddings for the query
        embeddings_model = await self.model_manager.get_embeddings()
        query_embedding = await embeddings_model.embed_query(question)

        # Get relevant documents
        relevant_docs = await self.vectorstore.similarity_search(query_embedding)

        # Generate response using LLM
        llm = await self.llm_manager.get_llm(ModelConfig("your-model", {}))
        llm = await self.model_manager.get_llm(ModelConfig("your-model", {}))
        
        # Create prompt with context
        context = "\n".join(relevant_docs)
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        
        return await llm.generate(prompt)