from typing import List, Dict, Any, Optional
import re


class TextChunker:
   """Simple text chunker with overlap."""
  
   def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
       """
       Initialize chunker.
      
       Args:
           chunk_size: Approximate number of tokens per chunk
           chunk_overlap: Approximate number of tokens to overlap between chunks
       """
       self.chunk_size = chunk_size
       self.chunk_overlap = chunk_overlap
       # Rough approximation: 1 token ≈ 4 characters
       self.char_chunk_size = chunk_size * 4
       self.char_overlap = chunk_overlap * 4
  
   def chunk_text(self, text: str, page_number: Optional[int] = None) -> List[Dict[str, Any]]:
       """
       Chunk text into overlapping segments.
      
       Args:
           text: Text to chunk
           page_number: Optional page number for metadata
          
       Returns:
           List of chunk dicts with text and metadata
       """
       if not text or not text.strip():
           return []
      
       chunks: list[Any] =  []
      
       # Split by sentences first for better boundaries
       sentences: List[str] = self._split_into_sentences(text)
      
       current_chunk: List[str] = []
       current_length = 0
      
       for sentence in sentences:
           sentence_length = len(sentence)
          
           # If adding this sentence exceeds chunk size, save current chunk
           if current_length + sentence_length > self.char_chunk_size and current_chunk:
               chunk_text = ' '.join(current_chunk)
               chunks.append({
                   'text': chunk_text,
                   'page_number': page_number,
                   'char_count': len(chunk_text)
               })
              
               # Keep overlap sentences for next chunk
               overlap_text: str = chunk_text[-self.char_overlap:]
               overlap_sentences: List[str] = self._split_into_sentences(overlap_text)
               current_chunk: List[str] = overlap_sentences
               current_length: int = sum(len(s) for s in current_chunk)
          
           current_chunk.append(sentence)
           current_length += sentence_length
      
       # Add remaining text as final chunk
       if current_chunk:
           chunk_text = ' '.join(current_chunk)
           chunks.append({
               'text': chunk_text,
               'page_number': page_number,
               'char_count': len(chunk_text)
           })
      
       return chunks
  
   def _split_into_sentences(self, text: str) -> List[str]:
       """
       Split text into sentences.
       Simple sentence boundary detection.
       """
       # Split on sentence boundaries
       sentences = re.split(r'(?<=[.!?])\s+', text)
       return [s.strip() for s in sentences if s.strip()]
  
   def chunk_document_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
       """
       Chunk multiple pages from a document.
      
       Args:
           pages: List of page dicts with 'text' and 'page_number'
          
       Returns:
           List of all chunks from all pages
       """
       all_chunks = []
      
       for page in pages:
           text = page.get('text', '')
           page_number = page.get('page_number')
          
           page_chunks: List[Dict[str, Any]] = self.chunk_text(text, page_number)
           all_chunks.extend(page_chunks)
      
       return all_chunks
