"""
Test script to debug bot selection issue
Run this to see what error occurs when initializing components
"""


import yaml
from db.sqlite_db import SQLiteDB
from core.document_loader import DocumentLoader
from core.chunker import TextChunker
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.rag_chain import RAGChain
from core.faq_loader import FAQLoader


def load_config():
   with open('config/settings.yaml', 'r') as f:
       return yaml.safe_load(f)


def test_init():
   print("Loading config...")
   config = load_config()
  
   print("Initializing database...")
   db = SQLiteDB(config['database']['path'])
  
   print("Initializing document loader...")
   doc_loader = DocumentLoader(config['storage']['upload_dir'])
  
   print("Initializing FAQ loader...")
   faq_loader = FAQLoader(config['storage'].get('faq_dir', 'storage/faq_files'))
  
   print("Initializing chunker...")
   chunker = TextChunker(
       chunk_size=config['chunking']['chunk_size'],
       chunk_overlap=config['chunking']['chunk_overlap']
   )
  
   print("Initializing embedder...")
   embedder = Embedder(config['embedding']['model_name'])
  
   print("Initializing vector store...")
   vector_store = VectorStore(
       host=config['vector_store']['host'],
       port=config['vector_store']['port'],
       collection_name=config['vector_store']['collection_name']
   )
  
   print("Creating document collection if needed...")
   try:
       if not vector_store.collection_exists():
           vector_store.create_collection(embedder.get_embedding_dimension())
           print("  ✓ Document collection created")
       else:
           print("  ✓ Document collection exists")
   except Exception as e:
       print(f"  ✗ Error with document collection: {e}")
  
   print("Creating FAQ collection if needed...")
   try:
       faq_vector_store = VectorStore(
           host=config['vector_store']['host'],
           port=config['vector_store']['port'],
           collection_name="faq_questions"
       )
       if not faq_vector_store.collection_exists():
           faq_vector_store.create_collection(embedder.get_embedding_dimension())
           print("  ✓ FAQ collection created")
       else:
           print("  ✓ FAQ collection exists")
   except Exception as e:
       print(f"  ✗ Error with FAQ collection: {e}")
  
   print("Initializing retriever...")
   retriever = Retriever(embedder, vector_store)
  
   print("Initializing RAG chain...")
   rag_chain = RAGChain(retriever, config['llm'])
  
   print("\n✅ All components initialized successfully!")
  
   # Test bot selection
   print("\nTesting bot selection...")
   bots = db.list_bots()
   print(f"Found {len(bots)} bots")
  
   if bots:
       print("\nBots:")
       for bot in bots:
           print(f"  - {bot['bot_name']} (ID: {bot['bot_id']})")
  
   return True


if __name__ == "__main__":
   try:
       test_init()
   except Exception as e:
       print(f"\n❌ ERROR: {e}")
       import traceback
       traceback.print_exc()