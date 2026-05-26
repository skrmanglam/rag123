from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue


class VectorStore:
    """Manage vector storage and retrieval using Qdrant."""
    
    def __init__(self, host: str = "localhost", port: int = 6333, 
                 collection_name: str = "rag_documents"):
        """
        Initialize Qdrant client.
        
        Args:
            host: Qdrant server host
            port: Qdrant server port
            collection_name: Name of the collection to use
        """
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
    
    def create_collection(self, embedding_dim: int):
        """
        Create a new collection if it doesn't exist.
        
        Args:
            embedding_dim: Dimension of embedding vectors
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=Distance.COSINE
                )
            )
    
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Add chunks with embeddings to the vector store.
        
        Args:
            chunks: List of chunk dicts with metadata
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=chunk['chunk_id'],
                vector=embedding,
                payload={
                    'chunk_id': chunk['chunk_id'],
                    'bot_id': chunk['bot_id'],
                    'document_id': chunk['document_id'],
                    'file_name': chunk['file_name'],
                    'page_number': chunk.get('page_number'),
                    'section_name': chunk.get('section_name'),
                    'has_table': chunk.get('has_table', False),
                    'text': chunk['text']
                }
            )
            points.append(point)
        
        # Upload in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )
    
    def search(self, query_embedding: List[float], bot_id: str, 
               top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            bot_id: Bot ID to filter by
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with scores
        """
        # Create filter for bot_id
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="bot_id",
                    match=MatchValue(value=bot_id)
                )
            ]
        )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k
        )
        
        # Format results - handle both document chunks and FAQ entries
        formatted_results = []
        for result in results:
            # Check if this is an FAQ entry or document chunk
            if 'question' in result.payload:
                # FAQ entry
                formatted_results.append({
                    'faq_id': result.payload.get('faq_id'),
                    'question_id': result.payload.get('question_id'),
                    'question': result.payload.get('question'),
                    'answer': result.payload.get('answer'),
                    'category': result.payload.get('category'),
                    'score': result.score
                })
            else:
                # Document chunk
                formatted_results.append({
                    'chunk_id': result.payload.get('chunk_id'),
                    'document_id': result.payload.get('document_id'),
                    'file_name': result.payload.get('file_name'),
                    'page_number': result.payload.get('page_number'),
                    'text': result.payload.get('text'),
                    'score': result.score
                })
        
        return formatted_results
    
    def delete_by_bot(self, bot_id: str):
        """
        Delete all chunks for a specific bot.
        
        Args:
            bot_id: Bot ID to delete chunks for
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="bot_id",
                        match=MatchValue(value=bot_id)
                    )
                ]
            )
        )
    
    def collection_exists(self) -> bool:
        """Check if the collection exists."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        return self.collection_name in collection_names
