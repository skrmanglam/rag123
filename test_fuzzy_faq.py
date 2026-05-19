#!/usr/bin/env python3
"""
Test script for FAQ fuzzy search functionality.
"""


from core.faq_fuzzy_search import FAQFuzzySearch




def test_fuzzy_search():
   """Test fuzzy search with sample FAQ data."""
  
   # Sample FAQ entries
   faq_entries = [
       {
           'question_id': 'faq_001',
           'question': 'What is the warranty period?',
           'answer': 'Our products come with a standard 2-year warranty.',
           'category': 'warranty'
       },
       {
           'question_id': 'faq_002',
           'question': 'How do I return a product?',
           'answer': 'You can return any product within 30 days of purchase.',
           'category': 'returns'
       },
       {
           'question_id': 'faq_003',
           'question': 'What payment methods do you accept?',
           'answer': 'We accept all major credit cards, PayPal, and bank transfers.',
           'category': 'payment'
       },
       {
           'question_id': 'faq_004',
           'question': 'How long does shipping take?',
           'answer': 'Standard shipping takes 5-7 business days.',
           'category': 'shipping'
       },
       {
           'question_id': 'faq_005',
           'question': 'Do you ship internationally?',
           'answer': 'Yes, we ship to over 100 countries worldwide.',
           'category': 'shipping'
       }
   ]
  
   # Initialize fuzzy search with default threshold (0.4)
   fuzzy_search = FAQFuzzySearch(similarity_threshold=0.4)
  
   print("=" * 80)
   print("FAQ FUZZY SEARCH TEST")
   print("=" * 80)
   print()
  
   # Test queries
   test_queries = [
       "warranty information",
       "how to return item",
       "payment options",
       "shipping time",
       "international delivery",
       "refund policy",  # Should not match well
       "what are the accepted payment methods"
   ]
  
   for query in test_queries:
       print(f"\nQuery: '{query}'")
       print("-" * 80)
      
       results = fuzzy_search.search(query, faq_entries, top_k=3)
      
       if results:
           print(f"Found {len(results)} match(es):\n")
           for i, result in enumerate(results, 1):
               print(f"  {i}. Question: {result['question']}")
               print(f"     Score: {result['score']:.3f}")
               print(f"     Category: {result['category']}")
               print(f"     Answer: {result['answer'][:60]}...")
               print()
       else:
           print("  No matches found above threshold (0.4)")
      
       print()
  
   # Test with different thresholds
   print("\n" + "=" * 80)
   print("TESTING DIFFERENT THRESHOLDS")
   print("=" * 80)
  
   query = "warranty info"
   thresholds = [0.4, 0.5, 0.6, 0.7, 0.8]
  
   for threshold in thresholds:
       fuzzy_search_test = FAQFuzzySearch(similarity_threshold=threshold)
       results = fuzzy_search_test.search(query, faq_entries, top_k=3)
       print(f"\nThreshold {threshold}: Found {len(results)} match(es)")
       if results:
           for result in results:
               print(f"  - {result['question']} (score: {result['score']:.3f})")
  
   # Test category filtering
   print("\n" + "=" * 80)
   print("TESTING CATEGORY FILTERING")
   print("=" * 80)
  
   query = "shipping"
   results = fuzzy_search.search_by_category(query, faq_entries, "shipping", top_k=3)
   print(f"\nQuery: '{query}' in category 'shipping'")
   print(f"Found {len(results)} match(es):\n")
   for result in results:
       print(f"  - {result['question']} (score: {result['score']:.3f})")
  
   print("\n" + "=" * 80)
   print("TEST COMPLETED")
   print("=" * 80)




if __name__ == "__main__":
   test_fuzzy_search()
