import streamlit as st
import yaml
import uuid
import os
from pathlib import Path


from db.sqlite_db import SQLiteDB
from core.document_loader import DocumentLoader
from core.chunker import TextChunker
from core.embedder import Embedder
from core.vector_store import VectorStore
from core.retriever import Retriever
from core.rag_chain import RAGChain
from core.faq_loader import FAQLoader
from core.faq_cache import FAQCache




# Load configuration
@st.cache_resource
def load_config():
   with open('config/settings.yaml', 'r') as f:
       return yaml.safe_load(f)




# Initialize components
@st.cache_resource
def init_components():
   config = load_config()
  
   # Initialize database
   db = SQLiteDB(config['database']['path'])
  
   # Initialize document loader
   doc_loader = DocumentLoader(config['storage']['upload_dir'])
  
   # Initialize chunker
   chunker = TextChunker(
       chunk_size=config['chunking']['chunk_size'],
       chunk_overlap=config['chunking']['chunk_overlap']
   )
  
   # Initialize embedder
   embedder = Embedder(config['embedding']['model_name'])
  
   # Initialize vector store
   vector_store = VectorStore(
       host=config['vector_store']['host'],
       port=config['vector_store']['port'],
       collection_name=config['vector_store']['collection_name']
   )
  
   # Create collection if it doesn't exist
   if not vector_store.collection_exists():
       vector_store.create_collection(embedder.get_embedding_dimension())
  
   # Initialize retriever
   retriever = Retriever(embedder, vector_store)
  
   # Initialize FAQ components
   faq_loader = FAQLoader(config['storage']['faq_dir'])
   faq_cache = FAQCache(
       embedder=embedder,
       vector_store=vector_store,
       db=db,
       similarity_threshold=config['faq']['similarity_threshold']
   )
  
   # Initialize RAG chain with FAQ cache for fuzzy search support
   rag_chain = RAGChain(retriever, config['llm'], faq_cache=faq_cache)
  
   return db, doc_loader, chunker, embedder, vector_store, retriever, rag_chain, faq_loader, faq_cache, config




def main():
   st.set_page_config(
       page_title="RAG Chatbot Builder",
       page_icon="🤖",
       layout="wide"
   )
  
   st.title("🤖 Local RAG Chatbot Builder")
   st.markdown("Build a chatbot from your documents in minutes!")
  
   # Initialize components
   db, doc_loader, chunker, embedder, vector_store, retriever, rag_chain, faq_loader, faq_cache, config = init_components()
  
   # Sidebar for bot creation and selection
   with st.sidebar:
       st.header("Bot Management")
      
       # List existing bots
       bots = db.list_bots()
      
       if bots:
           bot_names = [bot['bot_name'] for bot in bots]
           selected_bot_name = st.selectbox("Select Bot", ["Create New Bot"] + bot_names)
          
           if selected_bot_name != "Create New Bot":
               selected_bot = next(bot for bot in bots if bot['bot_name'] == selected_bot_name)
               st.session_state['current_bot'] = selected_bot
              
               # Chat Sessions Section
               st.markdown("---")
               st.subheader("💬 Chat Sessions")
              
               # Initialize sessions in session state
               if 'chat_sessions' not in st.session_state:
                   st.session_state['chat_sessions'] = {}
               if 'current_session_id' not in st.session_state:
                   st.session_state['current_session_id'] = 'default'
              
               bot_id = selected_bot['bot_id']
              
               # Get or create sessions for this bot
               if bot_id not in st.session_state['chat_sessions']:
                   st.session_state['chat_sessions'][bot_id] = {
                       'default': {
                           'name': 'New Chat',
                           'messages': [],
                           'created_at': None
                       }
                   }
              
               # New Chat button
               if st.button("➕ New Chat", use_container_width=True):
                   session_id = str(uuid.uuid4())[:8]
                   st.session_state['chat_sessions'][bot_id][session_id] = {
                       'name': 'New Chat',
                       'messages': [],
                       'created_at': None
                   }
                   st.session_state['current_session_id'] = session_id
                   st.session_state['chat_history'] = []
                   st.rerun()
              
               # Display sessions in a scrollable container
               sessions = st.session_state['chat_sessions'][bot_id]
              
               # Create a container for sessions
               with st.container():
                   for session_id, session_data in sessions.items():
                       col1, col2 = st.columns([4, 1])
                      
                       with col1:
                           # Session button
                           is_current = session_id == st.session_state.get('current_session_id', 'default')
                           button_label = f"{'▶ ' if is_current else ''}{session_data['name']}"
                          
                           if st.button(button_label, key=f"session_{session_id}", use_container_width=True):
                               st.session_state['current_session_id'] = session_id
                               st.session_state['chat_history'] = session_data['messages']
                               st.rerun()
                      
                       with col2:
                           # Delete button (don't allow deleting if it's the only session)
                           if len(sessions) > 1 and st.button("🗑️", key=f"del_{session_id}"):
                               del st.session_state['chat_sessions'][bot_id][session_id]
                               if session_id == st.session_state.get('current_session_id'):
                                   # Switch to first available session
                                   st.session_state['current_session_id'] = list(sessions.keys())[0]
                                   st.session_state['chat_history'] = sessions[list(sessions.keys())[0]]['messages']
                               st.rerun()
           else:
               st.session_state['current_bot'] = None
       else:
           st.info("No bots created yet. Create your first bot below!")
           st.session_state['current_bot'] = None
  
   # Main content area
   if st.session_state.get('current_bot') is None:
       # Bot creation form
       st.header("Create New Bot")
      
       with st.form("bot_creation_form"):
           bot_name = st.text_input("Bot Name", placeholder="e.g., HR Assistant")
          
           col1, col2 = st.columns(2)
          
           with col1:
               role = st.selectbox(
                   "Bot Role",
                   ["hr_assistant", "legal_assistant", "policy_assistant", "custom"]
               )
              
               tone = st.selectbox(
                   "Tone",
                   ["formal", "friendly", "concise"]
               )
          
           with col2:
               strictness = st.selectbox(
                   "Answer Strictness",
                   ["strict", "balanced", "flexible"],
                   help="Strict: Only from documents | Balanced: Primarily documents | Flexible: Documents + general knowledge"
               )
              
               citation_required = st.checkbox("Require Citations", value=True)
          
           fallback_behavior = st.selectbox(
               "Fallback Behavior",
               ["say_dont_know", "ask_rephrase", "escalate"],
               help="What to do when answer is not found"
           )
          
           behavior_instructions = st.text_area(
               "Additional Behavior Instructions (Optional)",
               placeholder="e.g., Always be polite and professional...",
               height=100
           )
          
           submitted = st.form_submit_button("Create Bot")
          
           if submitted and bot_name:
               bot_id = bot_name.lower().replace(' ', '_')
              
               # Create bot configuration
               bot_config = {
                   'role': role,
                   'tone': tone,
                   'strictness': strictness,
                   'citation_required': citation_required,
                   'fallback_behavior': fallback_behavior
               }
              
               # Build system prompt
               from core.prompt_builder import PromptBuilder
               system_prompt = PromptBuilder.build_system_prompt(bot_config)
              
               if behavior_instructions:
                   system_prompt += f"\n\nAdditional instructions:\n{behavior_instructions}"
              
               # Save to database
               success = db.create_bot(
                   bot_id=bot_id,
                   bot_name=bot_name,
                   system_prompt=system_prompt,
                   role=role,
                   tone=tone,
                   strictness=strictness,
                   citation_required=citation_required,
                   fallback_behavior=fallback_behavior
               )
              
               if success:
                   st.success(f"Bot '{bot_name}' created successfully!")
                   st.rerun()
               else:
                   st.error("Bot with this name already exists!")
  
   else:
       # Bot is selected - show document upload and chat interface
       bot = st.session_state['current_bot']
       bot_id = bot['bot_id']
       bot_name = bot['bot_name']
      
       st.header(f"Bot: {bot_name}")
      
       # Create tabs for different sections
       tab1, tab2, tab3, tab4 = st.tabs(["📄 Upload Documents", "💬 Chat", "⚙️ Configuration", "❓ FAQ"])
      
       with tab1:
           st.subheader("Upload Documents")
          
           uploaded_files = st.file_uploader(
               "Upload PDF, TXT, or MD files",
               type=['pdf', 'txt', 'md'],
               accept_multiple_files=True
           )
          
           if st.button("Process Documents", disabled=not uploaded_files):
               with st.spinner("Processing documents..."):
                   for uploaded_file in uploaded_files:
                       try:
                           # Save file
                           file_content = uploaded_file.read()
                           file_path = doc_loader.save_file(
                               file_content,
                               uploaded_file.name,
                               bot_id
                           )
                          
                           # Create document record
                           document_id = str(uuid.uuid4())
                           file_type = Path(uploaded_file.name).suffix.lower()
                          
                           db.create_document(
                               document_id=document_id,
                               bot_id=bot_id,
                               file_name=uploaded_file.name,
                               file_path=file_path,
                               file_type=file_type
                           )
                          
                           # Extract text
                           pages = doc_loader.load_document(file_path)
                          
                           # Chunk text
                           chunks = chunker.chunk_document_pages(pages)
                          
                           # Generate embeddings
                           chunk_texts = [chunk['text'] for chunk in chunks]
                           embeddings = embedder.embed_batch(chunk_texts)
                          
                           # Prepare chunks for storage
                           chunks_with_metadata = []
                           for chunk, embedding in zip(chunks, embeddings):
                               chunk_id = str(uuid.uuid4())
                              
                               # Save to database
                               db.create_chunk(
                                   chunk_id=chunk_id,
                                   bot_id=bot_id,
                                   document_id=document_id,
                                   file_name=uploaded_file.name,
                                   chunk_text=chunk['text'],
                                   page_number=chunk.get('page_number')
                               )
                              
                               chunks_with_metadata.append({
                                   'chunk_id': chunk_id,
                                   'bot_id': bot_id,
                                   'document_id': document_id,
                                   'file_name': uploaded_file.name,
                                   'text': chunk['text'],
                                   'page_number': chunk.get('page_number')
                               })
                          
                           # Add to vector store
                           vector_store.add_chunks(chunks_with_metadata, embeddings)
                          
                           # Update document status
                           db.update_document_status(document_id, 'processed')
                          
                           st.success(f"✅ Processed: {uploaded_file.name}")
                          
                       except Exception as e:
                           st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                  
                   st.success("All documents processed!")
          
           # Show uploaded documents
           st.subheader("Uploaded Documents")
           documents = db.get_documents_by_bot(bot_id)
          
           if documents:
               for doc in documents:
                   status_icon = "✅" if doc['status'] == 'processed' else "⏳"
                   st.text(f"{status_icon} {doc['file_name']} - {doc['status']}")
           else:
               st.info("No documents uploaded yet.")
      
       with tab2:
           # Header with clear chat button and FAQ search option
           col1, col2, col3 = st.columns([2, 1, 1])
           with col1:
               st.subheader("Chat with Your Bot")
           with col2:
               # FAQ search method toggle
               if 'use_fuzzy_faq' not in st.session_state:
                   st.session_state['use_fuzzy_faq'] = False
              
               use_fuzzy = st.toggle(
                   "Fuzzy FAQ",
                   value=st.session_state.get('use_fuzzy_faq', False),
                   help="Use fuzzy search for FAQ (no embeddings, faster)"
               )
               st.session_state['use_fuzzy_faq'] = use_fuzzy
           with col3:
               if st.button("🗑️ Clear Chat", help="Clear conversation history and start fresh"):
                   st.session_state['chat_history'] = []
                   # Also clear from session storage
                   session_id = st.session_state.get('current_session_id', 'default')
                   if bot_id in st.session_state.get('chat_sessions', {}):
                       if session_id in st.session_state['chat_sessions'][bot_id]:
                           st.session_state['chat_sessions'][bot_id][session_id]['messages'] = []
                           st.session_state['chat_sessions'][bot_id][session_id]['name'] = 'New Chat'
                   st.success("Chat cleared!")
                   st.rerun()
          
           # Show FAQ search mode indicator
           if st.session_state.get('use_fuzzy_faq', False):
               st.caption("🔍 FAQ Mode: Fuzzy Search (no embeddings)")
           else:
               st.caption("🔍 FAQ Mode: Vector Search (with embeddings)")
          
           # Check if documents are uploaded
           documents = db.get_documents_by_bot(bot_id)
          
           if not documents:
               st.warning("Please upload and process documents first!")
           else:
               # Initialize chat history
               if 'chat_history' not in st.session_state:
                   st.session_state['chat_history'] = []
              
               # Show chat stats
               if st.session_state['chat_history']:
                   st.caption(f"💬 {len(st.session_state['chat_history'])} messages in conversation")
              
               # Create a container with fixed height for chat history
               chat_container = st.container()
              
               with chat_container:
                   # Display chat history in a scrollable container
                   for message in st.session_state['chat_history']:
                       with st.chat_message(message['role']):
                           st.markdown(message['content'])
                           if message['role'] == 'assistant' and 'sources' in message:
                               with st.expander("📚 Sources"):
                                   for source in message['sources']:
                                       if source['page']:
                                           st.text(f"• {source['file_name']}, page {source['page']}")
                                       else:
                                           st.text(f"• {source['file_name']}")
              
               # Chat input at the bottom
               if question := st.chat_input("Ask a question..."):
                   # Check for greetings
                   greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
                   is_greeting = question.lower().strip() in greetings or any(question.lower().strip().startswith(g) for g in greetings)
                  
                   # Add user message to chat
                   st.session_state['chat_history'].append({
                       'role': 'user',
                       'content': question
                   })
                  
                   # Get bot response
                   if is_greeting:
                       # Handle greetings with bot introduction
                       role_name = bot.get('role', 'assistant').replace('_', ' ').title()
                       bot_name = bot.get('bot_name', 'Assistant')
                      
                       greeting_response = f"Hello! I'm {bot_name}, your {role_name}. "
                       greeting_response += f"I can help you find information from the uploaded documents. "
                       greeting_response += f"Feel free to ask me any questions about the documents!"
                      
                       st.session_state['chat_history'].append({
                           'role': 'assistant',
                           'content': greeting_response,
                           'sources': []
                       })
                   else:
                       # Normal RAG query with conversation history
                       with st.spinner("Thinking..."):
                           result = rag_chain.query(
                               question=question,
                               bot_id=bot_id,
                               bot_config=bot,
                               chat_history=st.session_state['chat_history'][:-1],  # Exclude current question
                               top_k=config['retrieval']['top_k'],
                               use_fuzzy_faq=st.session_state.get('use_fuzzy_faq', False)
                           )
                          
                           # Add assistant message to chat
                           st.session_state['chat_history'].append({
                               'role': 'assistant',
                               'content': result['answer'],
                               'sources': result['sources']
                           })
                  
                   # Save to session storage and update session name
                   session_id = st.session_state.get('current_session_id', 'default')
                   if bot_id in st.session_state.get('chat_sessions', {}):
                       if session_id in st.session_state['chat_sessions'][bot_id]:
                           # Save messages
                           st.session_state['chat_sessions'][bot_id][session_id]['messages'] = st.session_state['chat_history']
                          
                           # Auto-generate session name from first user message
                           if st.session_state['chat_sessions'][bot_id][session_id]['name'] == 'New Chat':
                               first_message = st.session_state['chat_history'][0]['content']
                               # Use first 30 chars as name
                               session_name = first_message[:30] + ('...' if len(first_message) > 30 else '')
                               st.session_state['chat_sessions'][bot_id][session_id]['name'] = session_name
                  
                   # Rerun to update the display
                   st.rerun()
      
       with tab3:
           st.subheader("Bot Configuration")
          
           col1, col2 = st.columns([2, 1])
          
           with col1:
               st.json({
                   'bot_id': bot['bot_id'],
                   'bot_name': bot['bot_name'],
                   'role': bot['role'],
                   'tone': bot['tone'],
                   'strictness': bot['strictness'],
                   'citation_required': bool(bot['citation_required']),
                   'fallback_behavior': bot['fallback_behavior']
               })
          
           with col2:
               if st.button("🔄 Refresh Bot Config", help="Reload bot configuration from database"):
                   st.session_state['current_bot'] = db.get_bot(bot_id)
                   st.success("Configuration refreshed!")
                   st.rerun()
          
           st.subheader("System Prompt")
           st.info("💡 Edit the system prompt below and click 'Update' to apply changes. No restart needed!")
          
           # Editable system prompt
           new_system_prompt = st.text_area(
               "System Prompt",
               value=bot['system_prompt'],
               height=300,
               help="Edit the system prompt to change how the bot behaves"
           )
          
           if st.button("💾 Update System Prompt"):
               if new_system_prompt.strip():
                   # Update in database
                   conn = db.get_connection()
                   conn.execute(
                       "UPDATE bots SET system_prompt = ? WHERE bot_id = ?",
                       (new_system_prompt, bot_id)
                   )
                   conn.commit()
                   conn.close()
                  
                   # Update session state
                   st.session_state['current_bot']['system_prompt'] = new_system_prompt
                  
                   st.success("✅ System prompt updated! Changes will apply to new conversations immediately.")
                   st.info("💡 Tip: The updated prompt is used right away - no restart needed!")
               else:
                   st.error("System prompt cannot be empty!")
          
           st.subheader("API Endpoint")
           st.code(f"POST http://localhost:8000/chat/{bot_id}", language="bash")
          
           st.subheader("Example API Call")
           st.code(f"""curl -X POST http://localhost:8000/chat/{bot_id} \\
 -H "Content-Type: application/json" \\
 -d '{{"question": "What is the leave policy?"}}'""", language="bash")
      
       with tab4:
           st.subheader("FAQ Management")
          
           # FAQ Upload Section
           st.markdown("### Upload FAQ CSV")
           st.markdown("Upload a CSV file with columns: `question_id`, `question`, `answer`, `category` (optional)")
          
           uploaded_faq = st.file_uploader(
               "Upload FAQ CSV file",
               type=['csv'],
               key="faq_uploader"
           )
          
           if uploaded_faq:
               try:
                   # Save file
                   file_content = uploaded_faq.read()
                   file_path = faq_loader.save_file(
                       file_content,
                       uploaded_faq.name,
                       bot_id
                   )
                  
                   # Parse CSV
                   faq_entries = faq_loader.parse_csv(file_path)
                  
                   # Validate entries
                   validation = faq_loader.validate_faq_entries(faq_entries)
                  
                   # Show validation results
                   col1, col2, col3 = st.columns(3)
                   with col1:
                       st.metric("Total Entries", validation['total_entries'])
                   with col2:
                       st.metric("Unique IDs", validation['unique_question_ids'])
                   with col3:
                       status = "✅ Valid" if validation['valid'] else "❌ Invalid"
                       st.metric("Status", status)
                  
                   # Show warnings if any
                   if validation['warnings']:
                       with st.expander("⚠️ Warnings", expanded=False):
                           for warning in validation['warnings']:
                               st.warning(warning)
                  
                   # Show duplicates if any
                   if validation['duplicates']:
                       with st.expander("❌ Duplicates Found", expanded=True):
                           for dup in validation['duplicates']:
                               st.error(dup)
                  
                   # Process button
                   if validation['valid']:
                       if st.button("Process FAQ Entries", type="primary"):
                           with st.spinner("Processing FAQ entries..."):
                               # Add to vector store
                               result = faq_cache.add_faq_entries(bot_id, faq_entries)
                              
                               if result['success']:
                                   st.success(f"✅ Added {result['added']} FAQ entries!")
                                   if result['skipped'] > 0:
                                       st.warning(f"⚠️ Skipped {result['skipped']} entries (duplicates)")
                                   if result.get('errors'):
                                       with st.expander("Errors"):
                                           for error in result['errors']:
                                               st.error(error)
                               else:
                                   st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                   else:
                       st.error("Cannot process FAQ file with duplicates. Please fix and re-upload.")
                      
               except Exception as e:
                   st.error(f"Error processing FAQ file: {str(e)}")
          
           # FAQ Stats Section
           st.markdown("---")
           st.markdown("### FAQ Statistics")
          
           stats = faq_cache.get_faq_stats(bot_id)
          
           if 'error' not in stats and stats.get('total_faqs', 0) > 0:
               col1, col2 = st.columns(2)
               with col1:
                   st.metric("Total FAQs", stats['total_faqs'])
               with col2:
                   st.metric("Similarity Threshold", f"{stats['similarity_threshold']:.2f}")
              
               if stats.get('categories'):
                   st.markdown("**Categories:**")
                   for category, count in stats['categories'].items():
                       st.text(f"• {category}: {count}")
           else:
               st.info("No FAQ entries uploaded yet.")
          
           # FAQ Search Test Section
           st.markdown("---")
           st.markdown("### Test FAQ Search")
          
           # Search method selection
           search_method = st.radio(
               "Search Method",
               ["Vector Search (Embeddings)", "Fuzzy Search (No Embeddings)"],
               help="Vector search uses embeddings (more accurate but requires computation). Fuzzy search uses text matching (faster, no embeddings needed)."
           )
          
           if search_method == "Vector Search (Embeddings)":
               st.markdown("🔍 **Vector Search** - Uses embeddings for semantic similarity")
           else:
               st.markdown("🔍 **Fuzzy Search** - Uses text matching without embeddings (cost-effective)")
          
           test_query = st.text_input(
               "Enter a test question",
               placeholder="e.g., What are your business hours?",
               key="faq_test_query"
           )
          
           col1, col2 = st.columns([1, 3])
           with col1:
               top_k = st.number_input("Results", min_value=1, max_value=10, value=3)
          
           if st.button("Search FAQs", type="secondary"):
               if test_query:
                   with st.spinner("Searching..."):
                       # Choose search method
                       if search_method == "Vector Search (Embeddings)":
                           results = faq_cache.search_faq(test_query, bot_id, top_k=top_k)
                           search_type = "vector"
                       else:
                           results = faq_cache.search_faq_fuzzy(test_query, bot_id, top_k=top_k)
                           search_type = "fuzzy"
                      
                       if results:
                           st.success(f"Found {len(results)} matching FAQ(s) using {search_type} search")
                          
                           for i, result in enumerate(results, 1):
                               score_label = "Similarity Score" if search_type == "vector" else "Match Score"
                               with st.expander(f"Match {i} - {score_label}: {result['score']:.3f}", expanded=(i==1)):
                                   st.markdown(f"**Question ID:** {result['question_id']}")
                                   st.markdown(f"**Question:** {result['question']}")
                                   st.markdown(f"**Answer:** {result['answer']}")
                                   if result.get('category'):
                                       st.markdown(f"**Category:** {result['category']}")
                                   st.markdown(f"**{score_label}:** {result['score']:.3f}")
                                   st.caption(f"Search Type: {result.get('search_type', search_type)}")
                       else:
                           st.warning(f"No matching FAQs found using {search_type} search.")
               else:
                   st.warning("Please enter a test question.")




if __name__ == "__main__":
   main()
