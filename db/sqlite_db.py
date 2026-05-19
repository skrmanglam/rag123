import sqlite3
import os
from typing import List, Dict, Optional
from pathlib import Path




class SQLiteDB:
   """Simple SQLite database manager for RAG Builder."""
  
   def __init__(self, db_path: str = "db/rag_builder.db"):
       self.db_path = db_path
       self._ensure_db_exists()
  
   def _ensure_db_exists(self):
       """Create database and tables if they don't exist."""
       os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
      
       # Read schema file
       schema_path = Path(__file__).parent / "schema.sql"
       with open(schema_path, 'r') as f:
           schema = f.read()
      
       # Execute schema
       conn = sqlite3.connect(self.db_path)
       conn.executescript(schema)
       conn.commit()
       conn.close()
  
   def get_connection(self):
       """Get a database connection."""
       conn = sqlite3.connect(self.db_path)
       conn.row_factory = sqlite3.Row
       return conn
  
   # Bot operations
   def create_bot(self, bot_id: str, bot_name: str, system_prompt: str,
                  role: Optional[str] = None, tone: Optional[str] = None,
                  strictness: Optional[str] = None, citation_required: bool = True,
                  fallback_behavior: Optional[str] = None) -> bool:
       """Create a new bot configuration."""
       conn = self.get_connection()
       try:
           conn.execute("""
               INSERT INTO bots (bot_id, bot_name, role, tone, strictness,
                                citation_required, fallback_behavior, system_prompt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           """, (bot_id, bot_name, role, tone, strictness,
                 1 if citation_required else 0, fallback_behavior, system_prompt))
           conn.commit()
           return True
       except sqlite3.IntegrityError:
           return False
       finally:
           conn.close()
  
   def get_bot(self, bot_id: str) -> Optional[Dict]:
       """Get bot configuration by ID."""
       conn = self.get_connection()
       cursor = conn.execute("SELECT * FROM bots WHERE bot_id = ?", (bot_id,))
       row = cursor.fetchone()
       conn.close()
      
       if row:
           return dict(row)
       return None
  
   def list_bots(self) -> List[Dict]:
       """List all bots."""
       conn = self.get_connection()
       cursor = conn.execute("SELECT * FROM bots ORDER BY created_at DESC")
       rows = cursor.fetchall()
       conn.close()
      
       return [dict(row) for row in rows]
  
   # Document operations
   def create_document(self, document_id: str, bot_id: str, file_name: str,
                      file_path: str, file_type: str) -> bool:
       """Create a new document record."""
       conn = self.get_connection()
       try:
           conn.execute("""
               INSERT INTO documents (document_id, bot_id, file_name, file_path, file_type)
               VALUES (?, ?, ?, ?, ?)
           """, (document_id, bot_id, file_name, file_path, file_type))
           conn.commit()
           return True
       except sqlite3.IntegrityError:
           return False
       finally:
           conn.close()
  
   def update_document_status(self, document_id: str, status: str) -> bool:
       """Update document processing status."""
       conn = self.get_connection()
       conn.execute("UPDATE documents SET status = ? WHERE document_id = ?",
                   (status, document_id))
       conn.commit()
       conn.close()
       return True
  
   def get_documents_by_bot(self, bot_id: str) -> List[Dict]:
       """Get all documents for a bot."""
       conn = self.get_connection()
       cursor = conn.execute(
           "SELECT * FROM documents WHERE bot_id = ? ORDER BY created_at DESC",
           (bot_id,)
       )
       rows = cursor.fetchall()
       conn.close()
      
       return [dict(row) for row in rows]
  
   # Chunk operations
   def create_chunk(self, chunk_id: str, bot_id: str, document_id: str,
                   file_name: str, chunk_text: str, page_number: Optional[int] = None,
                   section_name: Optional[str] = None, has_table: bool = False) -> bool:
       """Create a new chunk record."""
       conn = self.get_connection()
       try:
           conn.execute("""
               INSERT INTO chunks (chunk_id, bot_id, document_id, file_name,
                                  page_number, section_name, has_table, chunk_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           """, (chunk_id, bot_id, document_id, file_name, page_number,
                 section_name, 1 if has_table else 0, chunk_text))
           conn.commit()
           return True
       except sqlite3.IntegrityError:
           return False
       finally:
           conn.close()
  
   def get_chunks_by_document(self, document_id: str) -> List[Dict]:
       """Get all chunks for a document."""
       conn = self.get_connection()
       cursor = conn.execute(
           "SELECT * FROM chunks WHERE document_id = ? ORDER BY page_number",
           (document_id,)
       )
       rows = cursor.fetchall()
       conn.close()
      
       return [dict(row) for row in rows]
  
   def get_chunk(self, chunk_id: str) -> Optional[Dict]:
       """Get a specific chunk by ID."""
       conn = self.get_connection()
       cursor = conn.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
       row = cursor.fetchone()
       conn.close()
      
       if row:
           return dict(row)
       return None
  
   # FAQ operations
   def create_faq_entry(self, faq_id: str, bot_id: str, question_id: str,
                       question: str, answer: str, category: Optional[str] = None) -> bool:
       """Create a new FAQ entry."""
       conn = self.get_connection()
       try:
           conn.execute("""
               INSERT INTO faq_entries (faq_id, bot_id, question_id, question, answer, category)
               VALUES (?, ?, ?, ?, ?, ?)
           """, (faq_id, bot_id, question_id, question, answer, category))
           conn.commit()
           return True
       except sqlite3.IntegrityError:
           return False
       finally:
           conn.close()
  
   def get_faq_by_bot(self, bot_id: str) -> List[Dict]:
       """Get all FAQ entries for a bot."""
       conn = self.get_connection()
       cursor = conn.execute(
           "SELECT * FROM faq_entries WHERE bot_id = ? ORDER BY created_at DESC",
           (bot_id,)
       )
       rows = cursor.fetchall()
       conn.close()
      
       return [dict(row) for row in rows]
  
   def get_faq_entry(self, faq_id: str) -> Optional[Dict]:
       """Get a specific FAQ entry by ID."""
       conn = self.get_connection()
       cursor = conn.execute("SELECT * FROM faq_entries WHERE faq_id = ?", (faq_id,))
       row = cursor.fetchone()
       conn.close()
      
       if row:
           return dict(row)
       return None
  
   def delete_faq_by_bot(self, bot_id: str) -> bool:
       """Delete all FAQ entries for a bot."""
       conn = self.get_connection()
       conn.execute("DELETE FROM faq_entries WHERE bot_id = ?", (bot_id,))
       conn.commit()
       conn.close()
       return True
  
   def delete_faq_entry(self, faq_id: str) -> bool:
       """Delete a specific FAQ entry."""
       conn = self.get_connection()
       conn.execute("DELETE FROM faq_entries WHERE faq_id = ?", (faq_id,))
       conn.commit()
       conn.close()
       return True
