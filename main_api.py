from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import yaml


from db.sqlite_db import SQLiteDB
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.rag_chain import RAGChain
from core.faq_loader import FAQLoader
from core.faq_cache import FAQCache




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




# Request/Response models
class ChatRequest(BaseModel):
   question: str
   top_k: Optional[int] = 5
   use_fuzzy_faq: Optional[bool] = False




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




class DocumentInfo(BaseModel):
   document_id: str
   file_name: str
   status: str
   created_at: str




# Endpoints
@app.get("/")
def root():
   """Root endpoint."""
   return {
       "message": "RAG Chatbot API",
       "version": "1.0.0",
       "endpoints": {
           "chat": "POST /chat/{bot_id}",
           "bots": "GET /bots",
           "bot_info": "GET /bots/{bot_id}",
           "bot_documents": "GET /bots/{bot_id}/documents"
       }
   }




@app.get("/bots", response_model=List[BotInfo])
def list_bots():
   """List all bots."""
   bots = db.list_bots()
   return [
       BotInfo(
           bot_id=bot['bot_id'],
           bot_name=bot['bot_name'],
           role=bot.get('role'),
           tone=bot.get('tone'),
           strictness=bot.get('strictness'),
           citation_required=bool(bot.get('citation_required', True)),
           created_at=bot['created_at']
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
       created_at=bot['created_at']
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
   """
   bot = db.get_bot(bot_id)
   if not bot:
       raise HTTPException(status_code=404, detail="Bot not found")
  
   try:
       results = faq_cache.search_faq(
           query=request.question,
           bot_id=bot_id,
           top_k=request.top_k or 3
       )
      
       return {
           "query": request.question,
           "threshold": faq_cache.similarity_threshold,
           "matches": len(results),
           "results": results
       }
   except Exception as e:
       raise HTTPException(status_code=500, detail=f"Error searching FAQ: {str(e)}")




if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)
