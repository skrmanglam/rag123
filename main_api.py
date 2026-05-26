from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import yaml
import uuid
from pathlib import Path
from dotenv import load_dotenv

from db.sqlite_db import SQLiteDB
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.rag_chain import RAGChain
from core.faq_loader import FAQLoader
from core.faq_cache import FAQCache
from core.document_loader import DocumentLoader
from core.chunker import TextChunker
from core.prompt_builder import PromptBuilder

# load env vars
load_dotenv()


# Load configuration
def load_config():
    with open('config/settings.yaml', 'r') as f:
        return yaml.safe_load(f)


# Initialize components
config = load_config()
db = SQLiteDB(config['database']['path'])
embedder = Embedder(config['embedding']['model_name'])
vector_store = VectorStore(
    host=config['vector_store']['host'],
    port=config['vector_store']['port'],
    collection_name=config['vector_store']['collection_name']
)
retriever = Retriever(embedder, vector_store)
faq_loader = FAQLoader()

# Initialize document processing components
doc_loader = DocumentLoader(config['storage']['upload_dir'])
chunker = TextChunker(
    chunk_size=config['chunking']['chunk_size'],
    chunk_overlap=config['chunking']['chunk_overlap']
)

# Initialize FAQ cache
faq_cache = FAQCache(
    embedder=embedder,
    vector_store=vector_store,
    db=db,
    similarity_threshold=config['faq']['similarity_threshold']
)

# Initialize RAG chain with FAQ cache for fuzzy search support
rag_chain = RAGChain(retriever, config['llm'], faq_cache=faq_cache)

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="API for RAG-based chatbots",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5
    use_fuzzy_faq: Optional[bool] = False


class SystemPromptRequest(BaseModel):
    system_prompt: str


class Source(BaseModel):
    file_name: str
    page: Optional[int]
    chunk_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]


class BotInfo(BaseModel):
    bot_id: str
    bot_name: str
    role: Optional[str]
    tone: Optional[str]
    strictness: Optional[str]
    citation_required: bool
    created_at: str
    is_protected: bool  # True if password_hash exists


class DocumentInfo(BaseModel):
    document_id: str
    file_name: str
    status: str
    created_at: str


class BotCreateRequest(BaseModel):
    bot_name: str
    role: str
    tone: str
    strictness: str
    citation_required: bool = True
    fallback_behavior: str = "say_dont_know"
    behavior_instructions: Optional[str] = None
    password_hash: Optional[str] = None  # SHA-256 hash from client


class PasswordVerifyRequest(BaseModel):
    password_hash: str


# Endpoints
@app.get("/")
def root():
    """Serve the main HTML page."""
    return FileResponse('static/index.html')


@app.get("/bots", response_model=List[BotInfo])
def list_bots():
    """List all bots with protection status."""
    bots = db.list_bots()
    return [
        BotInfo(
            bot_id=bot['bot_id'],
            bot_name=bot['bot_name'],
            role=bot.get('role'),
            tone=bot.get('tone'),
            strictness=bot.get('strictness'),
            citation_required=bool(bot.get('citation_required', True)),
            created_at=bot['created_at'],
            is_protected=bool(bot.get('password_hash'))
        )
        for bot in bots
    ]


@app.get("/bots/{bot_id}", response_model=BotInfo)
def get_bot(bot_id: str):
    """Get bot information."""
    bot = db.get_bot(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return BotInfo(
        bot_id=bot['bot_id'],
        bot_name=bot['bot_name'],
        role=bot.get('role'),
        tone=bot.get('tone'),
        strictness=bot.get('strictness'),
        citation_required=bool(bot.get('citation_required', True)),
        created_at=bot['created_at'],
        is_protected=bool(bot.get('password_hash'))
    )


@app.get("/bots/{bot_id}/documents", response_model=List[DocumentInfo])
def get_bot_documents(bot_id: str):
    """Get all documents for a bot."""
    bot = db.get_bot(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    documents = db.get_documents_by_bot(bot_id)
    
    return [
        DocumentInfo(
            document_id=doc['document_id'],
            file_name=doc['file_name'],
            status=doc['status'],
            created_at=doc['created_at']
        )
        for doc in documents
    ]


@app.post("/bots", response_model=BotInfo)
def create_bot(request: BotCreateRequest):
    """Create a new bot."""
    # Generate bot_id from bot_name
    bot_id = request.bot_name.lower().replace(' ', '_')
    
    # Check if bot already exists
    existing_bot = db.get_bot(bot_id)
    if existing_bot:
        raise HTTPException(status_code=400, detail="Bot with this name already exists")
    
    # Create bot configuration
    bot_config = {
        'role': request.role,
        'tone': request.tone,
        'strictness': request.strictness,
        'citation_required': request.citation_required,
        'fallback_behavior': request.fallback_behavior
    }
    
    # Build system prompt
    system_prompt = PromptBuilder.build_system_prompt(bot_config)
    
    if request.behavior_instructions:
        system_prompt += f"\n\nAdditional instructions:\n{request.behavior_instructions}"
    
    # Save to database with password hash
    success = db.create_bot(
        bot_id=bot_id,
        bot_name=request.bot_name,
        system_prompt=system_prompt,
        role=request.role,
        tone=request.tone,
        strictness=request.strictness,
        citation_required=request.citation_required,
        fallback_behavior=request.fallback_behavior,
        password_hash=request.password_hash
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create bot")
    
    # Return created bot
    bot = db.get_bot(bot_id)
    return BotInfo(
        bot_id=bot['bot_id'],
        bot_name=bot['bot_name'],
        role=bot.get('role'),
        tone=bot.get('tone'),
        strictness=bot.get('strictness'),
        citation_required=bool(bot.get('citation_required', True)),
        created_at=bot['created_at'],
        is_protected=bool(bot.get('password_hash'))
    )


@app.post("/bots/{bot_id}/documents")
async def upload_documents(bot_id: str, files: List[UploadFile] = File(...)):
    """Upload and process documents for a bot."""
    # Validate bot exists
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ['.pdf', '.txt', '.md']:
                results.append({
                    "file_name": file.filename,
                    "status": "error",
                    "message": "Unsupported file type"
                })
                continue
            
            # Save file
            file_content = await file.read()
            file_path = doc_loader.save_file(file_content, file.filename, bot_id)
            
            # Create document record
            document_id = str(uuid.uuid4())
            db.create_document(
                document_id=document_id,
                bot_id=bot_id,
                file_name=file.filename,
                file_path=file_path,
                file_type=file_ext,
                status='processing'
            )
            
            # Load and process document
            documents = doc_loader.load_document(file_path)
            
            # Chunk documents
            all_chunks = []
            for doc in documents:
                chunks = chunker.chunk_text(doc['text'], 
                doc.get('page_number'))
                for i, chunk in enumerate(chunks):
                    all_chunks.append({
                        'content': chunk['text'], # changed from chunk to chunk['text']
                        'metadata': {
                            'document_id': document_id,
                            'file_name': file.filename,
                            'page': chunk.get('page_number'),# Changed from doc.get to chunk.get
                            'chunk_index': i
                        }
                    })
            
            # Prepare chunks for vector store
            chunks_for_db = []
            texts_to_embed = []

            for chunk in all_chunks:
                chunk_id = str(uuid.uuid4())
                chunks_for_db.append({
                    'chunk_id': chunk_id,
                    'bot_id': bot_id,
                    'document_id': document_id,
                    'file_name': file.filename,
                    'page_number': chunk['metadata'].get('page'),
                    'text': chunk['content']
                })
                texts_to_embed.append(chunk['content'])

                # Generate embeddings in batch
                embeddings = embedder.embed_batch(texts_to_embed)

                # Store in vector database
                vector_store.add_chunks(chunks_for_db, embeddings)
            
            # Update document status
            db.update_document_status(document_id, 'completed')
            
            results.append({
                "file_name": file.filename,
                "status": "success",
                "chunks": len(all_chunks)
            })
            
        except Exception as e:
            # Update document status to failed
            if 'document_id' in locals():
                db.update_document_status(document_id, 'failed')
            
            # Add this line to see the actual error
            print(f"ERROR processing {file.filename}: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()  # This will print the full stack trace

            results.append({
                "file_name": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {"results": results}


@app.post("/chat/{bot_id}", response_model=ChatResponse)
def chat(bot_id: str, request: ChatRequest):
    """
    Chat with a bot.
    
    Args:
        bot_id: Bot ID
        request: Chat request with question
        
    Returns:
        Chat response with answer and sources
    """
    # Get bot configuration
    bot = db.get_bot(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Check if bot has documents
    documents = db.get_documents_by_bot(bot_id)
    if not documents:
        raise HTTPException(
            status_code=400,
            detail="Bot has no documents. Please upload documents first."
        )
    
    # Process query
    try:
        result = rag_chain.query(
            question=request.question,
            bot_id=bot_id,
            bot_config=bot,
            top_k=request.top_k or 5,
            use_fuzzy_faq=request.use_fuzzy_faq or False
        )
        
        return ChatResponse(
            answer=result['answer'],
            sources=[
                Source(
                    file_name=source['file_name'],
                    page=source['page'],
                    chunk_id=source['chunk_id']
                )
                for source in result['sources']
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.delete("/bots/{bot_id}")
def delete_bot(bot_id: str):
    """
    Delete a bot and all associated data.
    
    This will:
    1. Delete from SQLite (cascade deletes documents, chunks, FAQs)
    2. Delete from Qdrant vector store
    3. Delete uploaded files from storage
    4. Delete FAQ files from storage
    """
    # Verify bot exists
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # Delete from vector store
        vector_store.delete_by_bot(bot_id)
        
        # Delete uploaded files
        doc_loader.delete_bot_files(bot_id)
        
        # Delete FAQ files
        faq_loader.delete_bot_faq_files(bot_id)
        
        # Delete from database (cascade deletes related records)
        success = db.delete_bot(bot_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete bot")
        
        return {
            "message": "Bot deleted successfully",
            "bot_id": bot_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting bot: {str(e)}")


@app.post("/bots/{bot_id}/verify-password")
def verify_bot_password(bot_id: str, request: PasswordVerifyRequest):
    """
    Verify password for a protected bot.
    Returns success if password matches or bot is not protected.
    """
    bot = db.get_bot(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # If bot has no password, it's public
    if not bot.get('password_hash'):
        return {"verified": True, "message": "Bot is not protected"}
    
    # Compare hashes
    if request.password_hash == bot['password_hash']:
        return {"verified": True, "message": "Password correct"}
    else:
        return {"verified": False, "message": "Incorrect password"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# FAQ Endpoints
@app.post("/bots/{bot_id}/faq/upload")
async def upload_faq(bot_id: str, file: UploadFile = File(...)):
    """
    Upload FAQ CSV file for a bot.
    
    CSV format: question_id,question,answer
    Optional column: category
    """
    # Validate bot exists
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        file_path = faq_loader.save_file(content, file.filename, bot_id)
        
        # Parse CSV
        faq_entries = faq_loader.parse_csv(file_path)
        
        # Validate entries
        validation = faq_loader.validate_faq_entries(faq_entries)
        
        if not validation['valid']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid FAQ entries: {validation['duplicates']}"
            )
        
        # Add to FAQ cache
        result = faq_cache.add_faq_entries(bot_id, faq_entries)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
        
        return {
            "message": "FAQ uploaded successfully",
            "stats": {
                "total_entries": result['total'],
                "added": result['added'],
                "skipped": result['skipped'],
                "errors": result.get('errors')
            },
            "validation": validation
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading FAQ: {str(e)}")


@app.get("/bots/{bot_id}/faq/stats")
def get_faq_stats(bot_id: str):
    """Get FAQ statistics for a bot."""
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    stats = faq_cache.get_faq_stats(bot_id)
    return stats


@app.get("/bots/{bot_id}/faq")
def list_faq_entries(bot_id: str):
    """List all FAQ entries for a bot."""
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    faqs = db.get_faq_by_bot(bot_id)
    return {
        "bot_id": bot_id,
        "total": len(faqs),
        "faqs": faqs
    }


@app.delete("/bots/{bot_id}/faq")
def delete_faq_entries(bot_id: str):
    """Delete all FAQ entries for a bot."""
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    success = faq_cache.delete_faq_by_bot(bot_id)
    
    if success:
        return {"message": "FAQ entries deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error deleting FAQ entries")


@app.post("/bots/{bot_id}/faq/search")
def search_faq(bot_id: str, request: ChatRequest):
    """
    Search FAQ entries for a question.
    Returns matching FAQs above similarity threshold.
    Supports both vector and fuzzy search methods.
    """
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    try:
        # Choose search method based on use_fuzzy_faq flag
        if request.use_fuzzy_faq:
            results = faq_cache.search_faq_fuzzy(
                query=request.question,
                bot_id=bot_id,
                top_k=request.top_k or 3
            )
            search_type = "fuzzy"
        else:
            results = faq_cache.search_faq(
                query=request.question,
                bot_id=bot_id,
                top_k=request.top_k or 3
            )
            search_type = "vector"
        
        return {
            "query": request.question,
            "threshold": faq_cache.similarity_threshold,
            "matches": len(results),
            "results": results,
            "search_type": search_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching FAQ: {str(e)}")


@app.get("/bots/{bot_id}/system-prompt")
def get_system_prompt(bot_id: str):
    """Get the system prompt for a bot."""
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {
        "bot_id": bot_id,
        "system_prompt": bot.get('system_prompt', '')
    }


@app.put("/bots/{bot_id}/system-prompt")
def update_system_prompt(bot_id: str, request: SystemPromptRequest):
    """Update the system prompt for a bot."""
    bot = db.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if not request.system_prompt.strip():
        raise HTTPException(status_code=400, detail="System prompt cannot be empty")
    
    try:
        # Update in database
        conn = db.get_connection()
        conn.execute(
            "UPDATE bots SET system_prompt = ? WHERE bot_id = ?",
            (request.system_prompt, bot_id)
        )
        conn.commit()
        conn.close()
        
        return {
            "message": "System prompt updated successfully",
            "bot_id": bot_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating system prompt: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)