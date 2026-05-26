from typing import List, Dict, Any, Optional
import uuid
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.faq_fuzzy_search import FAQFuzzySearch
from db.sqlite_db import SQLiteDB


class FAQCache:
    """Manage FAQ cache with vector search, fuzzy search, and database storage."""
    
    def __init__(self, embedder: Embedder, vector_store: VectorStore,
                 db: SQLiteDB, similarity_threshold: float = 0.90,
                 fuzzy_threshold: float = 0.6):
        """
        Initialize FAQ cache.
        
        Args:
            embedder: Embedder instance for question embedding
            vector_store: VectorStore instance for FAQ search
            db: SQLiteDB instance for FAQ metadata
            similarity_threshold: Minimum similarity score for vector search (default: 0.90)
            fuzzy_threshold: Minimum similarity score for fuzzy search (default: 0.6)
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.db = db
        self.similarity_threshold = similarity_threshold
        self.faq_collection_name = "faq_questions"
        self.fuzzy_search = FAQFuzzySearch(similarity_threshold=fuzzy_threshold)
    
    def initialize_faq_collection(self):
        """Create FAQ collection in vector store if it doesn't exist."""
        # Temporarily switch collection name
        original_collection = self.vector_store.collection_name
        self.vector_store.collection_name = self.faq_collection_name
        
        try:
            if not self.vector_store.collection_exists():
                embedding_dim = self.embedder.get_embedding_dimension()
                self.vector_store.create_collection(embedding_dim)
        finally:
            # Restore original collection name
            self.vector_store.collection_name = original_collection
    
    def add_faq_entries(self, bot_id: str, faq_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add FAQ entries to cache (database + vector store).
        
        Args:
            bot_id: Bot ID
            faq_entries: List of FAQ entry dicts with question_id, question, answer
            
        Returns:
            Result dict with success status and stats
        """
        if not faq_entries:
            return {'success': False, 'error': 'No FAQ entries provided'}
        
        try:
            # Initialize FAQ collection
            self.initialize_faq_collection()
            
            # Extract questions for embedding
            questions = [entry['question'] for entry in faq_entries]
            
            # Generate embeddings for all questions
            embeddings = self.embedder.embed_batch(questions)
            
            # Prepare data for storage
            added_count = 0
            skipped_count = 0
            errors = []
            
            for entry, embedding in zip(faq_entries, embeddings):
                try:
                    faq_id = str(uuid.uuid4())
                    
                    # Store in database
                    success = self.db.create_faq_entry(
                        faq_id=faq_id,
                        bot_id=bot_id,
                        question_id=entry['question_id'],
                        question=entry['question'],
                        answer=entry['answer'],
                        category=entry.get('category')
                    )
                    
                    if success:
                        # Store in vector store
                        self._add_faq_to_vector_store(
                            faq_id=faq_id,
                            bot_id=bot_id,
                            question_id=entry['question_id'],
                            question=entry['question'],
                            answer=entry['answer'],
                            category=entry.get('category'),
                            embedding=embedding
                        )
                        added_count += 1
                    else:
                        skipped_count += 1
                        errors.append(f"Duplicate question_id: {entry['question_id']}")
                        
                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Error adding {entry['question_id']}: {str(e)}")
            
            return {
                'success': True,
                'added': added_count,
                'skipped': skipped_count,
                'total': len(faq_entries),
                'errors': errors if errors else None
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _add_faq_to_vector_store(self, faq_id: str, bot_id: str, question_id: str,
                                   question: str, answer: str, category: Optional[str],
                                   embedding: List[float]):
        """Add single FAQ entry to vector store."""
        # Temporarily switch collection
        original_collection = self.vector_store.collection_name
        self.vector_store.collection_name = self.faq_collection_name
        
        try:
            from qdrant_client.models import PointStruct
            
            point = PointStruct(
                id=faq_id,
                vector=embedding,
                payload={
                    'faq_id': faq_id,
                    'bot_id': bot_id,
                    'question_id': question_id,
                    'question': question,
                    'answer': answer,
                    'category': category
                }
            )
            
            self.vector_store.client.upsert(
                collection_name=self.faq_collection_name,
                points=[point]
            )
        finally:
            self.vector_store.collection_name = original_collection
    
    def search_faq(self, query: str, bot_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for matching FAQ entries.
        
        Args:
            query: User query
            bot_id: Bot ID to filter by
            top_k: Number of results to return
            
        Returns:
            List of matching FAQ entries with scores
        """
        try:
            # Check if FAQ collection exists
            if not self.vector_store.collection_exists():
                return []
            
            # Embed the query
            query_embedding = self.embedder.embed_text(query)
            
            # Search in FAQ collection
            original_collection = self.vector_store.collection_name
            self.vector_store.collection_name = self.faq_collection_name
            
            try:
                # Check if FAQ collection exists
                collections = self.vector_store.client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if self.faq_collection_name not in collection_names:
                    # FAQ collection doesn't exist yet
                    return []
                
                results = self.vector_store.search(
                    query_embedding=query_embedding,
                    bot_id=bot_id,
                    top_k=top_k
                )
            finally:
                self.vector_store.collection_name = original_collection
            
            # Filter by similarity threshold and ensure these are FAQ entries
            filtered_results = []
            for r in results:
                # Verify this is an FAQ entry (has 'question' field)
                if 'question' in r and r.get('score', 0) >= self.similarity_threshold:
                    filtered_results.append(r)
            
            return filtered_results
            
        except Exception as e:
            print(f"Error searching FAQ: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_faq_match(self, query: str, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get FAQ match if similarity is above threshold.
        
        Args:
            query: User query
            bot_id: Bot ID
            
        Returns:
            FAQ match dict or None if no match above threshold
        """
        results = self.search_faq(query, bot_id, top_k=3)
        
        if results:
            # Return all matches above threshold
            return {
                'matched': True,
                'matches': results,
                'primary_answer': results[0]['answer'],  # Highest scoring answer
                'all_answers': [r['answer'] for r in results]
            }
        
        return None
    
    def search_faq_fuzzy(self, query: str, bot_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for matching FAQ entries using fuzzy search (no embeddings required).
        
        Args:
            query: User query
            bot_id: Bot ID to filter by
            top_k: Number of results to return
            
        Returns:
            List of matching FAQ entries with scores
        """
        try:
            # Get all FAQ entries for this bot from database
            faq_entries = self.db.get_faq_by_bot(bot_id)
            
            if not faq_entries:
                return []
            
            # Perform fuzzy search
            results = self.fuzzy_search.search(query, faq_entries, top_k=top_k)
            
            return results
            
        except Exception as e:
            print(f"Error in fuzzy FAQ search: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_faq_match_fuzzy(self, query: str, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        Get FAQ match using fuzzy search if similarity is above threshold.
        
        Args:
            query: User query
            bot_id: Bot ID
            
        Returns:
            FAQ match dict or None if no match above threshold
        """
        results = self.search_faq_fuzzy(query, bot_id, top_k=3)
        
        if results:
            # Return all matches above threshold
            return {
                'matched': True,
                'matches': results,
                'primary_answer': results[0]['answer'],  # Highest scoring answer
                'all_answers': [r['answer'] for r in results],
                'search_type': 'fuzzy'
            }
        
        return None
    
    def delete_faq_by_bot(self, bot_id: str) -> bool:
        """
        Delete all FAQ entries for a bot.
        
        Args:
            bot_id: Bot ID
            
        Returns:
            Success status
        """
        try:
            # Delete from database
            self.db.delete_faq_by_bot(bot_id)
            
            # Delete from vector store
            original_collection = self.vector_store.collection_name
            self.vector_store.collection_name = self.faq_collection_name
            
            try:
                self.vector_store.delete_by_bot(bot_id)
            finally:
                self.vector_store.collection_name = original_collection
            
            return True
        except Exception as e:
            print(f"Error deleting FAQ entries: {str(e)}")
            return False
    
    def get_faq_stats(self, bot_id: str) -> Dict[str, Any]:
        """
        Get FAQ statistics for a bot.
        
        Args:
            bot_id: Bot ID
            
        Returns:
            Stats dict with counts and categories
        """
        try:
            faqs = self.db.get_faq_by_bot(bot_id)
            
            categories = {}
            for faq in faqs:
                category = faq.get('category') or 'uncategorized'
                categories[category] = categories.get(category, 0) + 1
            
            return {
                'total_faqs': len(faqs),
                'categories': categories,
                'similarity_threshold': self.similarity_threshold
            }
        except Exception as e:
            return {'error': str(e)}