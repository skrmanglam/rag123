from typing import Dict, Any, List, Optional
import os
import requests
from openai import OpenAI
from core.retriever import Retriever
from core.prompt_builder import PromptBuilder
from core.faq_cache import FAQCache




class RAGChain:
   """Main RAG chain that orchestrates retrieval and generation."""
  
   def __init__(self, retriever: Retriever, llm_config: Dict[str, Any],
                faq_cache: Optional[FAQCache] = None):
       """
       Initialize RAG chain.
      
       Args:
           retriever: Retriever instance
           llm_config: LLM configuration dict
           faq_cache: Optional FAQCache instance for fuzzy search
       """
       self.retriever = retriever
       self.llm_config = llm_config
       self.prompt_builder = PromptBuilder()
       self.provider = llm_config.get('provider', 'ollama')
       self.faq_cache = faq_cache
      
       # Initialize LLM client based on provider
       self.client: Optional[OpenAI] = None
       if self.provider == 'openai':
           api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('openai', {}).get('api_key')
           if not api_key:
               raise ValueError("OPENAI_API_KEY environment variable not set")
           self.client = OpenAI(api_key=api_key)
       elif self.provider == 'openai_compatible':
           base_url = llm_config.get('openai_compatible', {}).get('base_url', 'http://localhost:1234/v1')
           api_key = (
               os.getenv('OPENROUTER_API_KEY')
               or os.getenv('OPENAI_API_KEY')
               or llm_config.get('openai_compatible', {}).get('api_key')
           )
           if not api_key:
               raise ValueError(
                   "Set OPENROUTER_API_KEY (or OPENAI_API_KEY) for openai_compatible provider"
               )
           self.client = OpenAI(base_url=base_url, api_key=api_key)
       elif self.provider == 'ollama':
           self.ollama_base_url = llm_config.get('ollama', {}).get('base_url', 'http://localhost:11434')
       else:
           raise ValueError(f"Unsupported LLM provider: {self.provider}")
  
   def query(self, question: str, bot_id: str, bot_config: Dict[str, Any],
             top_k: int = 5, chat_history: Optional[List[Dict[str, str]]] = None,
             use_fuzzy_faq: bool = False) -> Dict[str, Any]:
       """
       Process a query through the RAG pipeline.
       First checks FAQ collection, then document collection.
      
       Args:
           question: User's question
           bot_id: Bot ID
           bot_config: Bot configuration
           top_k: Number of chunks to retrieve
           chat_history: Optional conversation history for context
           use_fuzzy_faq: If True, use fuzzy search for FAQ instead of vector search
          
       Returns:
           Dict with answer and sources
       """
       # STEP 1: Search FAQ collection first
       if use_fuzzy_faq and self.faq_cache:
           # Use fuzzy search (no embeddings)
           faq_results = self.faq_cache.search_faq_fuzzy(
               query=question,
               bot_id=bot_id,
               top_k=3
           )
       else:
           # Use vector search (with embeddings)
           faq_results = self.retriever.search_faq_collection(
               query=question,
               bot_id=bot_id,
               top_k=3,
               similarity_threshold=0.85
           )
      
       # If FAQ match found, use it
       if faq_results:
           # Format FAQ context
           faq_context = "\n\n".join([
               f"Q: {faq['question']}\nA: {faq['answer']}"
               for faq in faq_results
           ])
          
           # Build prompts
           system_prompt = self.prompt_builder.build_system_prompt(bot_config)
           user_prompt = self.prompt_builder.build_user_prompt(question, faq_context, chat_history)
          
           # Generate answer
           answer = self._generate_answer(system_prompt, user_prompt)
          
           return {
               'answer': answer,
               'sources': [{
                   'file_name': 'FAQ',
                   'page': None,
                   'chunk_id': faq.get('question_id', 'faq')
               } for faq in faq_results],
               'context': faq_context,
               'faq_matched': True
           }
      
       # STEP 2: No FAQ match - search document collection
       chunks = self.retriever.retrieve(
           query=question,
           bot_id=bot_id,
           top_k=top_k
       )
      
       # Format context
       context = self.retriever.format_context(chunks)
      
       # Build prompts with conversation history
       system_prompt = self.prompt_builder.build_system_prompt(bot_config)
       user_prompt = self.prompt_builder.build_user_prompt(question, context, chat_history)
      
       # Generate answer
       answer = self._generate_answer(system_prompt, user_prompt)
      
       # Get sources
       sources = self.retriever.get_sources(chunks)
      
       return {
           'answer': answer,
           'sources': sources,
           'context': context,
           'faq_matched': False
       }
  
   def _generate_answer(self, system_prompt: str, user_prompt: str) -> str:
       """
       Generate answer using LLM.
      
       Args:
           system_prompt: System prompt
           user_prompt: User prompt
          
       Returns:
           Generated answer
       """
       if self.provider == 'ollama':
           return self._generate_with_ollama(system_prompt, user_prompt)
       else:
           return self._generate_with_openai(system_prompt, user_prompt)
  
   def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
       """Generate answer using OpenAI-compatible API."""
       messages = self.prompt_builder.format_messages(system_prompt, user_prompt)
      
       try:
           if self.provider == 'openai':
               model = self.llm_config.get('openai', {}).get('model', 'gpt-3.5-turbo')
           else:
               model = self.llm_config.get('openai_compatible', {}).get('model', 'local-model')
          
           if not self.client:
               return "Error: OpenAI client not initialized"
          
           response = self.client.chat.completions.create(
               model=model,
               messages=messages,
               temperature=self.llm_config.get('temperature', 0.1),
               max_tokens=self.llm_config.get('max_tokens', 500)
           )
          
           return response.choices[0].message.content
       except Exception as e:
           return f"Error generating answer: {str(e)}"
  
   def _generate_with_ollama(self, system_prompt: str, user_prompt: str) -> str:
       """Generate answer using Ollama."""
       try:
           model = self.llm_config.get('ollama', {}).get('model', 'llama3.2')
          
           # Combine prompts for Ollama
           full_prompt = f"{system_prompt}\n\n{user_prompt}"
          
           response = requests.post(
               f"{self.ollama_base_url}/api/generate",
               json={
                   "model": model,
                   "prompt": full_prompt,
                   "stream": False,
                   "options": {
                       "temperature": self.llm_config.get('temperature', 0.1),
                       "num_predict": self.llm_config.get('max_tokens', 500)
                   }
               },
               timeout=60
           )
          
           if response.status_code == 200:
               return response.json().get('response', 'No response generated')
           else:
               return f"Error from Ollama: {response.status_code} - {response.text}"
       except Exception as e:
           return f"Error generating answer with Ollama: {str(e)}"
  
   def stream_query(self, question: str, bot_id: str, bot_config: Dict[str, Any],
                    top_k: int = 5):
       """
       Process a query with streaming response.
      
       Args:
           question: User's question
           bot_id: Bot ID
           bot_config: Bot configuration
           top_k: Number of chunks to retrieve
          
       Yields:
           Chunks of the answer
       """
       # Retrieve relevant chunks
       chunks = self.retriever.retrieve(
           query=question,
           bot_id=bot_id,
           top_k=top_k
       )
      
       # Format context
       context = self.retriever.format_context(chunks)
      
       # Build prompts
       system_prompt = self.prompt_builder.build_system_prompt(bot_config)
       user_prompt = self.prompt_builder.build_user_prompt(question, context)
       messages = self.prompt_builder.format_messages(system_prompt, user_prompt)
      
       # Stream answer
       if self.provider == 'ollama':
           # Ollama streaming
           try:
               model = self.llm_config.get('ollama', {}).get('model', 'llama3.2')
               full_prompt = f"{system_prompt}\n\n{user_prompt}"
              
               response = requests.post(
                   f"{self.ollama_base_url}/api/generate",
                   json={
                       "model": model,
                       "prompt": full_prompt,
                       "stream": True,
                       "options": {
                           "temperature": self.llm_config.get('temperature', 0.1),
                           "num_predict": self.llm_config.get('max_tokens', 500)
                       }
                   },
                   stream=True,
                   timeout=60
               )
              
               for line in response.iter_lines():
                   if line:
                       import json
                       chunk = json.loads(line)
                       if 'response' in chunk:
                           yield chunk['response']
           except Exception as e:
               yield f"Error generating answer: {str(e)}"
       else:
           # OpenAI-compatible streaming
           try:
               if self.provider == 'openai':
                   model = self.llm_config.get('openai', {}).get('model', 'gpt-3.5-turbo')
               else:
                   model = self.llm_config.get('openai_compatible', {}).get('model', 'local-model')
              
               if not self.client:
                   yield "Error: OpenAI client not initialized"
                   return
              
               stream = self.client.chat.completions.create(
                   model=model,
                   messages=messages,
                   temperature=self.llm_config.get('temperature', 0.1),
                   max_tokens=self.llm_config.get('max_tokens', 500),
                   stream=True
               )
              
               for chunk in stream:
                   if chunk.choices[0].delta.content is not None:
                       yield chunk.choices[0].delta.content
           except Exception as e:
               yield f"Error generating answer: {str(e)}"
