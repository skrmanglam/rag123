from typing import List, Dict, Any
from core.embedder import Embedder
from core.vector_store import VectorStore


class Retriever:
    """Retrieve relevant chunks for a query."""
    
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        """
        Initialize retriever.
        
        Args:
            embedder: Embedder instance for query embedding
            vector_store: VectorStore instance for searching
        """
        self.embedder = embedder
        self.vector_store = vector_store
    
    def retrieve(self, query: str, bot_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            query: User query
            bot_id: Bot ID to filter by
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        # Embed the query
        query_embedding = self.embedder.embed_text(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            bot_id=bot_id,
            top_k=top_k
        )
        
        return results
    
    def search_faq_collection(self, query: str, bot_id: str, top_k: int = 3,
                             similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
        """
        Search FAQ collection with high similarity threshold.
        
        Args:
            query: User query
            bot_id: Bot ID to filter by
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (default 0.85)
            
        Returns:
            List of FAQ entries above threshold, empty list if none found
        """
        # Embed the query
        query_embedding = self.embedder.embed_text(query)
        
        # Temporarily switch to FAQ collection
        original_collection = self.vector_store.collection_name
        self.vector_store.collection_name = "faq_questions"
        
        try:
            # Check if FAQ collection exists
            if not self.vector_store.collection_exists():
                return []
            
            # Search FAQ collection
            results = self.vector_store.search(
                query_embedding=query_embedding,
                bot_id=bot_id,
                top_k=top_k
            )
            
            # Filter by similarity threshold
            filtered_results = [
                r for r in results
                if r.get('score', 0) >= similarity_threshold and 'question' in r
            ]
            
            return filtered_results
            
        finally:
            # Restore original collection
            self.vector_store.collection_name = original_collection
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into context string.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant information found in the documents."
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            file_name = chunk['file_name']
            page_number = chunk.get('page_number')
            text = chunk['text']
            
            # Format source reference
            if page_number:
                source = f"{file_name}, page {page_number}"
            else:
                source = file_name
            
            context_parts.append(f"[Source {i}: {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def get_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract source information from chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            List of source dicts
        """
        sources = []
        seen = set()
        
        for chunk in chunks:
            file_name = chunk['file_name']
            page_number = chunk.get('page_number')
            chunk_id = chunk['chunk_id']
            
            # Create unique key to avoid duplicates
            key = (file_name, page_number)
            if key not in seen:
                sources.append({
                    'file_name': file_name,
                    'page': page_number,
                    'chunk_id': chunk_id
                })
                seen.add(key)
        
        return sources