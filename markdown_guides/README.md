# 🤖 Local RAG Chatbot Builder MVP

Build a simple local RAG (Retrieval-Augmented Generation) chatbot from your documents in minutes!

## Features

- 📄 Upload PDF, TXT, and MD documents
- 🤖 Create custom chatbots with configurable behavior
- 💬 Chat interface via Streamlit
- 🔌 REST API for integration
- 🗄️ Local vector storage with Qdrant
- 📊 SQLite for metadata management
- 🎯 Citation support with source tracking
- ❓ FAQ support with dual search modes (Vector & Fuzzy)

## Tech Stack

- **Frontend**: Streamlit
- **Backend API**: FastAPI
- **Vector DB**: Qdrant (local)
- **Document Parsing**: PyMuPDF
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: OpenAI API (configurable)
- **Metadata DB**: SQLite
- **Language**: Python 3.8+

## Project Structure

```
rag_builder/
│
├── app_streamlit.py          # Streamlit UI
├── main_api.py               # FastAPI endpoints
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── core/                     # Core RAG components
│   ├── document_loader.py    # Document loading and text extraction
│   ├── chunker.py            # Text chunking
│   ├── embedder.py           # Embedding generation
│   ├── vector_store.py       # Qdrant vector store interface
│   ├── retriever.py          # Retrieval logic
│   ├── prompt_builder.py     # Prompt construction
│   ├── rag_chain.py          # Main RAG pipeline
│   ├── faq_loader.py         # FAQ CSV file loading
│   ├── faq_cache.py          # FAQ caching and search
│   └── faq_fuzzy_search.py   # Fuzzy search for FAQ (no embeddings)
│
├── db/                       # Database
│   ├── sqlite_db.py          # SQLite interface
│   └── schema.sql            # Database schema
│
├── storage/                  # File storage
│   └── uploaded_files/       # Uploaded documents (created automatically)
│
└── config/                   # Configuration
    └── settings.yaml         # Application settings
```

## Prerequisites

- Python 3.8 or higher
- Docker (for Qdrant)
- OpenAI API key

## Setup Instructions

### 1. Clone or Create Project Directory

```bash
mkdir rag_builder
cd rag_builder
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up OpenAI API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or create a `.env` file:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### 4. Start Qdrant Vector Database

Using Docker:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Or using Docker Compose (create `docker-compose.yml`):

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

Then run:

```bash
docker-compose up -d
```

Verify Qdrant is running:

```bash
curl http://localhost:6333/
```

### 5. Start the FastAPI Server

```bash
python main_api.py
```

Or using uvicorn directly:

```bash
uvicorn main_api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### 6. Start the Streamlit App

In a new terminal:

```bash
streamlit run app_streamlit.py
```

The Streamlit app will open in your browser at `http://localhost:8501`

## Usage Guide

### Creating a Chatbot

1. Open the Streamlit app at `http://localhost:8501`
2. In the sidebar, you'll see "Create New Bot" selected by default
3. Fill in the bot configuration:
   - **Bot Name**: e.g., "HR Assistant"
   - **Bot Role**: Choose from HR, Legal, Policy, or Custom
   - **Tone**: Formal, Friendly, or Concise
   - **Answer Strictness**: 
     - Strict: Only from documents
     - Balanced: Primarily documents
     - Flexible: Documents + general knowledge
   - **Require Citations**: Enable to include source references
   - **Fallback Behavior**: What to do when answer is not found
4. Click "Create Bot"

### Uploading Documents

1. Select your bot from the sidebar
2. Go to the "📄 Upload Documents" tab
3. Click "Browse files" and select PDF, TXT, or MD files
4. Click "Process Documents"
5. Wait for processing to complete (you'll see progress for each file)

### Managing FAQs

1. Select your bot from the sidebar
2. Go to the "❓ FAQ" tab
3. Upload a CSV file with FAQ entries (format: `question_id,question,answer,category`)
4. Click "Process FAQ Entries" to add them to the bot
5. Test FAQ search using either:
   - **Vector Search** - Semantic similarity using embeddings (more accurate)
   - **Fuzzy Search** - Text matching without embeddings (faster, cost-effective)

**FAQ CSV Format Example:**
```csv
question_id,question,answer,category
faq_001,What is the warranty period?,Our products come with a 2-year warranty,warranty
faq_002,How do I return a product?,You can return within 30 days,returns
```

### Chatting with Your Bot

1. Go to the "💬 Chat" tab
2. **Optional**: Toggle "Fuzzy FAQ" to use fuzzy search for FAQ questions (faster, no embeddings)
3. Type your question in the chat input
4. The bot will:
   - First check FAQ entries (if available)
   - Then retrieve relevant chunks from your documents
   - Generate an answer using the LLM
   - Provide source citations
5. View sources by expanding the "📚 Sources" section

### Using the API

#### List All Bots

```bash
curl http://localhost:8000/bots
```

#### Get Bot Information

```bash
curl http://localhost:8000/bots/hr_assistant
```

#### Chat with a Bot

```bash
curl -X POST http://localhost:8000/chat/hr_assistant \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the leave policy?"}'
```

**Using Fuzzy FAQ Search (faster, no embeddings):**

```bash
curl -X POST http://localhost:8000/chat/hr_assistant \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the warranty period?",
    "use_fuzzy_faq": true
  }'
```

Response:

```json
{
  "answer": "According to the employee handbook...",
  "sources": [
    {
      "file_name": "employee_handbook.pdf",
      "page": 15,
      "chunk_id": "abc123..."
    }
  ]
}
```

#### Get Bot Documents

```bash
curl http://localhost:8000/bots/hr_assistant/documents
```

## Configuration

Edit `config/settings.yaml` to customize:

### Chunking Settings

```yaml
chunking:
  chunk_size: 800        # Approximate tokens per chunk
  chunk_overlap: 150     # Overlap between chunks
```

### Embedding Model

```yaml
embedding:
  model_name: "all-MiniLM-L6-v2"  # sentence-transformers model
```

### Retrieval Settings

```yaml
retrieval:
  top_k: 5  # Number of chunks to retrieve
```

### LLM Settings

```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  temperature: 0.1
  max_tokens: 500

### FAQ Settings

```yaml
faq:
  similarity_threshold: 0.90  # Vector search threshold (0-1)
  fuzzy_threshold: 0.4        # Fuzzy search threshold (0-1)
```

## Troubleshooting

### Qdrant Connection Error

**Error**: `Connection refused to localhost:6333`

**Solution**: Make sure Qdrant is running:

```bash
docker ps | grep qdrant
```

If not running, start it:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### OpenAI API Error

**Error**: `OpenAI API key not set`

**Solution**: Set your API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**: Install dependencies:

```bash
pip install -r requirements.txt
```

### Document Processing Fails

**Error**: `Error processing document`

**Solution**: 
- Check file format (PDF, TXT, MD only)
- Ensure file is not corrupted
- Check file permissions

### FAQ Not Matching

**Error**: FAQ search returns no results

**Solution**:
- **For Vector Search**: Lower `similarity_threshold` in `config/settings.yaml`
- **For Fuzzy Search**: Lower `fuzzy_threshold` or improve FAQ question quality
- Try the alternative search method (toggle between Vector/Fuzzy)
- Ensure FAQ CSV is properly formatted

## Example Workflow

Here's a complete example of creating and using a chatbot:

### 1. Start Services

```bash
# Terminal 1: Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 2: Start FastAPI
export OPENAI_API_KEY='your-key'
python main_api.py

# Terminal 3: Start Streamlit
streamlit run app_streamlit.py
```

### 2. Create Bot via Streamlit

1. Open `http://localhost:8501`
2. Create bot named "HR Assistant"
3. Configure as HR assistant with formal tone
4. Enable citations

### 3. Upload Documents

1. Upload `employee_handbook.pdf`
2. Upload `leave_policy.pdf`
3. Click "Process Documents"

### 4. Chat

Ask: "What is the annual leave policy?"

Response: "Employees are entitled to 20 days of annual leave per year... [Source: leave_policy.pdf, page 3]"

### 5. Use API

```bash
curl -X POST http://localhost:8000/chat/hr_assistant \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the annual leave policy?"}'
```

### 6. Use FAQ Feature

Upload FAQ CSV:
```bash
curl -X POST http://localhost:8000/bots/hr_assistant/faq/upload \
  -F "file=@faq.csv"
```

Chat with fuzzy FAQ search:
```bash
curl -X POST http://localhost:8000/chat/hr_assistant \
  -H "Content-Type: application/json" \
  -d '{
    "question": "warranty information",
    "use_fuzzy_faq": true
  }'
```

## Limitations (MVP)

This is an MVP with the following limitations:

- No user authentication
- No multi-tenancy
- Local deployment only
- Single LLM provider (OpenAI)
- Basic chunking strategy
- No reranking
- No conversation history in API

## FAQ Search Modes

The system supports two FAQ search methods:

### Vector Search (Default)
- Uses embeddings for semantic similarity
- More accurate for paraphrased questions
- Requires embedding generation (slower)
- Best for: Complex queries, synonyms, varied phrasings

### Fuzzy Search (New)
- Text-based matching without embeddings
- ~10x faster, no embedding computation
- Cost-effective for high-volume queries
- Best for: Direct keyword matches, cost optimization

**When to use each:**
- Use **Vector Search** for highest accuracy
- Use **Fuzzy Search** for speed and cost savings

See [`FAQ_FUZZY_SEARCH.md`](FAQ_FUZZY_SEARCH.md) for detailed documentation.

## Future Enhancements

Potential improvements for future versions:

- User authentication and authorization
- Multiple LLM providers (Anthropic, local models)
- Advanced chunking strategies
- Reranking for better retrieval
- Conversation history management
- Web scraping for document ingestion
- Batch document processing
- Export/import bot configurations
- Analytics and usage tracking
- Hybrid FAQ search (combining vector + fuzzy)

## License

MIT License

## Support

For issues or questions, please create an issue in the repository.

---

**Built with ❤️ for simple, local RAG applications**