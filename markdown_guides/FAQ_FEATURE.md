# FAQ Pre-Cache Feature Documentation

## Overview

The FAQ pre-cache feature provides a fast-path lookup mechanism for frequently asked questions. When a user asks a question, the system first searches the FAQ cache using semantic similarity. If a match is found above the configured threshold (default: 0.80), the cached answer is returned after being personalized by the LLM. If no match is found, the system falls back to the regular RAG pipeline that searches through uploaded documents.

## Architecture

```
User Question
     ↓
1. Embed Question (384-dim vector)
     ↓
2. Search FAQ Collection in Qdrant
     ↓
3. Check Similarity Score
     ↓
   Score ≥ 0.80?  ──YES──→ Return FAQ Answer (via LLM personalization)
     ↓ NO
4. Fall back to Document RAG Pipeline
```

## Key Components

### 1. **FAQ Loader** (`core/faq_loader.py`)
- Parses CSV files with FAQ entries
- Validates format and data integrity
- Supports both comma (`,`) and pipe (`|`) delimiters

### 2. **FAQ Cache** (`core/faq_cache.py`)
- Manages FAQ storage in SQLite + Qdrant
- Performs semantic search on questions
- Filters results by similarity threshold
- Handles FAQ CRUD operations

### 3. **RAG Chain Integration** (`core/rag_chain.py`)
- Checks FAQ cache before document search
- Personalizes FAQ answers through LLM
- Combines multiple FAQ matches when relevant
- Falls back to document search if no FAQ match

### 4. **Database Schema** (`db/schema.sql`)
- `faq_entries` table stores FAQ metadata
- Indexed by `bot_id` and `question_id`
- Supports categories for organization

## CSV Format

### Required Columns
```csv
question_id,question,answer
faq_001,What is the warranty period?,Our products come with a 2-year warranty.
faq_002,How do I return a product?,You can return within 30 days.
```

### Optional Columns
```csv
question_id,question,answer,category
faq_001,What is the warranty period?,Our products come with a 2-year warranty.,warranty
faq_002,How do I return a product?,You can return within 30 days.,returns
```

### Format Rules
- **Delimiter**: Comma (`,`) or pipe (`|`)
- **Headers**: First row must contain column names
- **Encoding**: UTF-8
- **question_id**: Unique identifier (e.g., faq_001, faq_002)
- **question**: The FAQ question text
- **answer**: The cached answer text
- **category**: Optional grouping (e.g., warranty, shipping, returns)

## API Endpoints

### 1. Upload FAQ CSV
```http
POST /bots/{bot_id}/faq/upload
Content-Type: multipart/form-data

file: sample_faq.csv
```

**Response:**
```json
{
  "message": "FAQ uploaded successfully",
  "stats": {
    "total_entries": 10,
    "added": 10,
    "skipped": 0,
    "errors": null
  },
  "validation": {
    "valid": true,
    "total_entries": 10,
    "unique_question_ids": 10,
    "duplicates": [],
    "warnings": []
  }
}
```

### 2. Get FAQ Statistics
```http
GET /bots/{bot_id}/faq/stats
```

**Response:**
```json
{
  "total_faqs": 10,
  "categories": {
    "warranty": 1,
    "returns": 2,
    "shipping": 3,
    "payment": 1,
    "orders": 1,
    "pricing": 1,
    "support": 1
  },
  "similarity_threshold": 0.80
}
```

### 3. List All FAQ Entries
```http
GET /bots/{bot_id}/faq
```

**Response:**
```json
{
  "bot_id": "customer_support_bot",
  "total": 10,
  "faqs": [
    {
      "faq_id": "uuid-here",
      "bot_id": "customer_support_bot",
      "question_id": "faq_001",
      "question": "What is the warranty period?",
      "answer": "Our products come with a 2-year warranty.",
      "category": "warranty",
      "created_at": "2026-04-27 10:00:00"
    }
  ]
}
```

### 4. Search FAQ (Test Matching)
```http
POST /bots/{bot_id}/faq/search
Content-Type: application/json

{
  "question": "How long is the warranty?",
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "How long is the warranty?",
  "threshold": 0.80,
  "matches": 1,
  "results": [
    {
      "question_id": "faq_001",
      "question": "What is the warranty period?",
      "answer": "Our products come with a 2-year warranty.",
      "score": 0.94
    }
  ]
}
```

### 5. Delete All FAQ Entries
```http
DELETE /bots/{bot_id}/faq
```

**Response:**
```json
{
  "message": "FAQ entries deleted successfully"
}
```

### 6. Chat with FAQ Cache
```http
POST /chat/{bot_id}
Content-Type: application/json

{
  "question": "How long is the warranty?",
  "top_k": 5
}
```

**Response (FAQ Match):**
```json
{
  "answer": "Our products come with a comprehensive 2-year warranty that covers all manufacturing defects...",
  "sources": [
    {
      "file_name": "FAQ",
      "page": null,
      "chunk_id": "faq_001"
    }
  ],
  "faq_matched": true
}
```

**Response (No FAQ Match - Document Search):**
```json
{
  "answer": "Based on the documentation...",
  "sources": [
    {
      "file_name": "product_manual.pdf",
      "page": 5,
      "chunk_id": "chunk_123"
    }
  ],
  "faq_matched": false
}
```

## Configuration

Edit `config/settings.yaml`:

```yaml
# FAQ Cache settings
faq:
  similarity_threshold: 0.80  # Minimum similarity score for FAQ match (0.0-1.0)
  # Higher threshold = stricter matching (more precise)
  # Lower threshold = looser matching (more results)
  # Recommended: 0.75-0.85 for good balance

# Storage settings
storage:
  upload_dir: "storage/uploaded_files"
  faq_dir: "storage/faq_files"
```

### Threshold Guidelines

| Threshold | Behavior | Use Case |
|-----------|----------|----------|
| 0.90-1.0 | Very strict | Exact question matches only |
| 0.85-0.89 | Strict | High confidence matches |
| 0.80-0.84 | Moderate (recommended) | Balanced precision/recall |
| 0.75-0.79 | Lenient | More matches, less precise |
| < 0.75 | Very lenient | Not recommended |

## Usage Example

### Step 1: Prepare FAQ CSV

Create `my_faqs.csv`:
```csv
question_id,question,answer,category
faq_001,What is the warranty period?,Our products come with a 2-year warranty.,warranty
faq_002,How do I return a product?,You can return within 30 days.,returns
```

### Step 2: Upload FAQ

```bash
curl -X POST "http://localhost:8000/bots/my_bot/faq/upload" \
  -F "file=@my_faqs.csv"
```

### Step 3: Test FAQ Search

```bash
curl -X POST "http://localhost:8000/bots/my_bot/faq/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "How long is the warranty?"}'
```

### Step 4: Chat with FAQ Cache

```bash
curl -X POST "http://localhost:8000/chat/my_bot" \
  -H "Content-Type: application/json" \
  -d '{"question": "How long is the warranty?"}'
```

## How It Works

### Query Flow

1. **User asks**: "How long is the warranty?"

2. **FAQ Cache Check**:
   - Question is embedded into 384-dim vector
   - Semantic search in `faq_questions` Qdrant collection
   - Finds: "What is the warranty period?" (score: 0.94)
   - Score ≥ 0.80 threshold → FAQ match!

3. **LLM Personalization**:
   - System prompt: Bot configuration
   - User prompt: "Based on FAQ: [answer], respond to: [question]"
   - LLM generates natural, personalized response

4. **Response**:
   - Answer: Personalized version of FAQ answer
   - Sources: `[{file_name: "FAQ", chunk_id: "faq_001"}]`
   - `faq_matched: true`

### If No FAQ Match

1. Score < 0.80 threshold
2. Falls back to regular RAG pipeline
3. Searches document chunks in Qdrant
4. Returns document-based answer

## Benefits

✅ **Fast Response**: FAQ lookup is faster than document search  
✅ **Consistent Answers**: Pre-approved answers for common questions  
✅ **Personalized**: LLM adapts FAQ answers to user's phrasing  
✅ **Fallback**: Seamlessly falls back to document search  
✅ **Easy Management**: Simple CSV upload/update  
✅ **Semantic Matching**: Handles question variations  

## Best Practices

1. **Question Variety**: Include common phrasings in FAQ questions
2. **Clear Answers**: Keep answers concise but complete
3. **Categories**: Use categories for organization
4. **Regular Updates**: Keep FAQ current with product changes
5. **Test Threshold**: Adjust similarity threshold based on your needs
6. **Monitor Matches**: Use `/faq/search` to test question matching

## Troubleshooting

### FAQ Not Matching

**Problem**: Questions not matching despite being similar

**Solutions**:
- Lower similarity threshold (e.g., 0.75)
- Rephrase FAQ question to be more generic
- Add multiple FAQ entries for variations
- Test with `/faq/search` endpoint

### Too Many Matches

**Problem**: Unrelated FAQs matching

**Solutions**:
- Raise similarity threshold (e.g., 0.95)
- Make FAQ questions more specific
- Use categories to organize FAQs

### CSV Upload Errors

**Problem**: CSV file rejected

**Solutions**:
- Check CSV format (headers, delimiters)
- Ensure UTF-8 encoding
- Verify no duplicate question_ids
- Check for empty required fields

## Sample FAQ CSV

See `sample_faq.csv` in the project root for a complete example with 10 FAQ entries covering common customer support topics.

## Technical Details

- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Vector Database**: Qdrant (separate `faq_questions` collection)
- **Metadata Storage**: SQLite (`faq_entries` table)
- **Similarity Metric**: Cosine similarity
- **Default Threshold**: 0.80 (80% similar)
- **LLM Integration**: Answers personalized through configured LLM

---

**Made with Bob** 🤖