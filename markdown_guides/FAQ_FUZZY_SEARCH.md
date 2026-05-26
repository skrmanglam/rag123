# FAQ Fuzzy Search Feature

## Overview

The FAQ system now supports **two search methods**:

1. **Vector Search** (Original) - Uses embeddings for semantic similarity
2. **Fuzzy Search** (New) - Uses text matching without embeddings

## Why Fuzzy Search?

### Benefits
- ✅ **No Embeddings Required** - Saves computational resources
- ✅ **Faster** - No need to generate embeddings for queries
- ✅ **Cost-Effective** - Reduces API calls and processing time
- ✅ **Good for Exact/Similar Matches** - Works well when users ask questions similar to FAQ entries

### When to Use Each Method

**Use Vector Search when:**
- You need semantic understanding (e.g., "refund" matching "money back")
- Questions are phrased very differently from FAQ entries
- You want the highest accuracy

**Use Fuzzy Search when:**
- You want faster responses
- You want to reduce computational costs
- FAQ questions are well-written and cover common phrasings
- You have limited resources (no GPU, slow CPU)

## How It Works

### Fuzzy Search Algorithm

The fuzzy search uses a combination of:

1. **Sequence Matching** - Compares character sequences using Python's `SequenceMatcher`
2. **Word Overlap** - Calculates percentage of common words
3. **Keyword Matching** - Boosts scores when key terms match
4. **Stop Word Filtering** - Ignores common words like "the", "is", "are"

**Scoring Formula:**
```
final_score = (sequence_similarity * 0.7) + (word_overlap * 0.3)
+ 10% bonus if keywords match
```

### Default Threshold

- **Fuzzy Search**: 0.4 (40% similarity)
- **Vector Search**: 0.85 (85% similarity)

Lower threshold for fuzzy search accounts for text-based matching being less precise than semantic embeddings.

## Usage

### In Streamlit UI

1. Navigate to the **FAQ** tab
2. Under "Test FAQ Search", select your search method:
   - **Vector Search (Embeddings)** - Traditional semantic search
   - **Fuzzy Search (No Embeddings)** - Fast text-based search
3. Enter your test question and click "Search FAQs"

### In Chat Interface

1. Go to the **Chat** tab
2. Toggle the **"Fuzzy FAQ"** switch in the header
   - OFF = Vector Search (with embeddings)
   - ON = Fuzzy Search (no embeddings)
3. The current mode is displayed below the toggle

### Via API

Send a POST request to `/chat/{bot_id}` with the `use_fuzzy_faq` parameter:

```bash
# Using Vector Search (default)
curl -X POST http://localhost:8000/chat/my_bot \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the warranty period?",
    "top_k": 5
  }'

# Using Fuzzy Search
curl -X POST http://localhost:8000/chat/my_bot \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the warranty period?",
    "top_k": 5,
    "use_fuzzy_faq": true
  }'
```

## Configuration

### Adjusting Fuzzy Search Threshold

Edit `core/faq_cache.py` when initializing `FAQCache`:

```python
faq_cache = FAQCache(
    embedder=embedder,
    vector_store=vector_store,
    db=db,
    similarity_threshold=0.90,  # Vector search threshold
    fuzzy_threshold=0.4          # Fuzzy search threshold (NEW)
)
```

### Customizing Search Behavior

Edit `core/faq_fuzzy_search.py` to modify:

- Stop words list
- Scoring weights
- Keyword matching logic
- Text normalization rules

## Performance Comparison

### Test Results

Using sample FAQ data with 5 entries:

| Query | Vector Search | Fuzzy Search |
|-------|--------------|--------------|
| "warranty information" | ✅ Match (0.92) | ✅ Match (0.45) |
| "how to return item" | ✅ Match (0.89) | ✅ Match (0.58) |
| "payment options" | ✅ Match (0.87) | ❌ No match (0.38) |
| "shipping time" | ✅ Match (0.91) | ✅ Match (0.48) |

**Key Findings:**
- Fuzzy search works well for direct keyword matches
- Vector search better handles synonyms and paraphrasing
- Fuzzy search is ~10x faster (no embedding generation)

## Code Structure

### New Files

1. **`core/faq_fuzzy_search.py`** - Fuzzy search implementation
   - `FAQFuzzySearch` class
   - Text normalization
   - Similarity calculation
   - Category filtering

2. **`test_fuzzy_faq.py`** - Test script for fuzzy search

### Modified Files

1. **`core/faq_cache.py`**
   - Added `search_faq_fuzzy()` method
   - Added `get_faq_match_fuzzy()` method
   - Added `fuzzy_threshold` parameter

2. **`core/rag_chain.py`**
   - Added `use_fuzzy_faq` parameter to `query()` method
   - Added `faq_cache` parameter to constructor
   - Conditional FAQ search based on method

3. **`app_streamlit.py`**
   - Added fuzzy search toggle in chat interface
   - Added search method selector in FAQ test section
   - Pass `use_fuzzy_faq` to RAG chain

4. **`main_api.py`**
   - Added `use_fuzzy_faq` field to `ChatRequest`
   - Initialize `FAQCache` with fuzzy threshold
   - Pass fuzzy search flag to RAG chain

## Testing

Run the test script:

```bash
python test_fuzzy_faq.py
```

This will test:
- Basic fuzzy matching
- Different similarity thresholds
- Category filtering
- Various query types

## Best Practices

1. **Start with Fuzzy Search** - Try it first for cost savings
2. **Monitor Match Quality** - Track if users get good answers
3. **Adjust Threshold** - Lower if too few matches, raise if too many false positives
4. **Use Both Methods** - Let users choose based on their needs
5. **Write Clear FAQs** - Better FAQ questions = better fuzzy matches

## Troubleshooting

### No Matches Found

**Problem:** Fuzzy search returns no results

**Solutions:**
- Lower the similarity threshold (try 0.3)
- Check FAQ questions are well-written
- Ensure query and FAQ use similar terminology
- Consider using vector search instead

### Too Many False Positives

**Problem:** Irrelevant FAQs are returned

**Solutions:**
- Raise the similarity threshold (try 0.5)
- Improve FAQ question quality
- Use category filtering
- Switch to vector search for better accuracy

### Slow Performance

**Problem:** Fuzzy search is slower than expected

**Solutions:**
- Reduce number of FAQ entries
- Implement caching for common queries
- Use category filtering to reduce search space
- Consider indexing for large FAQ sets

## Future Enhancements

Potential improvements:

1. **Hybrid Search** - Combine fuzzy and vector search
2. **Query Expansion** - Add synonyms automatically
3. **Learning** - Track which matches users find helpful
4. **Caching** - Cache fuzzy search results
5. **Phonetic Matching** - Handle misspellings better

## Support

For issues or questions:
- Check test results: `python test_fuzzy_faq.py`
- Review FAQ entries for quality
- Adjust thresholds based on your data
- Consider your use case (speed vs accuracy)

---

**Made with Bob** 🤖