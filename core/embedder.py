from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np




class Embedder:
   """Generate embeddings using sentence-transformers."""
  
   def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
       """
       Initialize embedder with specified model.
      
       Args:
           model_name: Name of the sentence-transformers model
       """
       self.model_name = model_name
       self.model = SentenceTransformer(model_name)
       self.embedding_dim = self.model.get_sentence_embedding_dimension()
  
   def embed_text(self, text: str) -> List[float]:
       """
       Generate embedding for a single text.
      
       Args:
           text: Text to embed
          
       Returns:
           Embedding vector as list of floats
       """
       embedding = self.model.encode(text, convert_to_numpy=True)
       return embedding.tolist()
  
   def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
       """
       Generate embeddings for multiple texts.
      
       Args:
           texts: List of texts to embed
           batch_size: Batch size for processing
          
       Returns:
           List of embedding vectors
       """
       embeddings = self.model.encode(
           texts,
           batch_size=batch_size,
           convert_to_numpy=True,
           show_progress_bar=True
       )
       return embeddings.tolist()
  
   def get_embedding_dimension(self) -> int:
       """Get the dimension of embeddings produced by this model."""
       return self.embedding_dim
