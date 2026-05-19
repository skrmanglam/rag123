from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import re




class FAQFuzzySearch:
   """Fuzzy search for FAQ entries without requiring embeddings."""
  
   def __init__(self, similarity_threshold: float = 0.4):
       """
       Initialize fuzzy search.
      
       Args:
           similarity_threshold: Minimum similarity score (0-1) for matches (default: 0.4)
       """
       self.similarity_threshold = similarity_threshold
  
   def _normalize_text(self, text: str) -> str:
       """
       Normalize text for comparison.
      
       Args:
           text: Input text
          
       Returns:
           Normalized text (lowercase, no extra spaces)
       """
       # Convert to lowercase
       text = text.lower()
       # Remove extra whitespace
       text = ' '.join(text.split())
       # Remove punctuation at the end
       text = re.sub(r'[?.!,;]+$', '', text)
       return text
  
   def _calculate_similarity(self, query: str, question: str) -> float:
       """
       Calculate similarity between query and question.
      
       Uses SequenceMatcher for fuzzy string matching.
      
       Args:
           query: User query
           question: FAQ question
          
       Returns:
           Similarity score (0-1)
       """
       # Normalize both texts
       query_norm = self._normalize_text(query)
       question_norm = self._normalize_text(question)
      
       # Calculate base similarity
       base_similarity = SequenceMatcher(None, query_norm, question_norm).ratio()
      
       # Bonus for word overlap
       query_words = set(query_norm.split())
       question_words = set(question_norm.split())
      
       if query_words and question_words:
           word_overlap = len(query_words & question_words) / len(query_words | question_words)
           # Weighted combination: 70% sequence match, 30% word overlap
           final_similarity = (base_similarity * 0.7) + (word_overlap * 0.3)
       else:
           final_similarity = base_similarity
      
       return final_similarity
  
   def _contains_keywords(self, query: str, question: str) -> bool:
       """
       Check if question contains key words from query.
      
       Args:
           query: User query
           question: FAQ question
          
       Returns:
           True if significant keyword overlap exists
       """
       query_norm = self._normalize_text(query)
       question_norm = self._normalize_text(question)
      
       # Extract words (filter out common stop words)
       stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                     'would', 'should', 'could', 'may', 'might', 'can', 'i', 'you',
                     'he', 'she', 'it', 'we', 'they', 'what', 'when', 'where', 'how'}
      
       query_words = [w for w in query_norm.split() if w not in stop_words and len(w) > 2]
       question_words = set(question_norm.split())
      
       if not query_words:
           return False
      
       # Check if at least 50% of query keywords are in question
       matches = sum(1 for word in query_words if word in question_words)
       return matches >= len(query_words) * 0.5
  
   def search(self, query: str, faq_entries: List[Dict[str, Any]],
              top_k: int = 3) -> List[Dict[str, Any]]:
       """
       Search FAQ entries using fuzzy matching.
      
       Args:
           query: User query
           faq_entries: List of FAQ entry dicts with 'question' and 'answer' fields
           top_k: Number of top results to return
          
       Returns:
           List of matching FAQ entries with similarity scores, sorted by score
       """
       if not query or not faq_entries:
           return []
      
       results = []
      
       for entry in faq_entries:
           question = entry.get('question', '')
           if not question:
               continue
          
           # Calculate similarity
           similarity = self._calculate_similarity(query, question)
          
           # Boost score if keywords match
           if self._contains_keywords(query, question):
               similarity = min(1.0, similarity * 1.1)  # 10% boost, capped at 1.0
          
           # Only include if above threshold
           if similarity >= self.similarity_threshold:
               result = {
                   'question_id': entry.get('question_id'),
                   'question': question,
                   'answer': entry.get('answer'),
                   'category': entry.get('category'),
                   'score': similarity,
                   'search_type': 'fuzzy'
               }
               results.append(result)
      
       # Sort by similarity score (descending)
       results.sort(key=lambda x: x['score'], reverse=True)
      
       # Return top_k results
       return results[:top_k]
  
   def get_best_match(self, query: str, faq_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
       """
       Get the best matching FAQ entry.
      
       Args:
           query: User query
           faq_entries: List of FAQ entry dicts
          
       Returns:
           Best matching FAQ entry or None if no match above threshold
       """
       results = self.search(query, faq_entries, top_k=1)
       return results[0] if results else None
  
   def search_by_category(self, query: str, faq_entries: List[Dict[str, Any]],
                         category: str, top_k: int = 3) -> List[Dict[str, Any]]:
       """
       Search FAQ entries within a specific category.
      
       Args:
           query: User query
           faq_entries: List of FAQ entry dicts
           category: Category to filter by
           top_k: Number of top results to return
          
       Returns:
           List of matching FAQ entries from the specified category
       """
       # Filter by category first
       filtered_entries = [
           entry for entry in faq_entries
           if entry.get('category', '').lower() == category.lower()
       ]
      
       return self.search(query, filtered_entries, top_k)
