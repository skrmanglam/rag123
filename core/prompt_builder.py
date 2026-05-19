from typing import Dict, Any, List, Optional




class PromptBuilder:
   """Build prompts for the RAG system."""
  
   @staticmethod
   def build_system_prompt(bot_config: Dict[str, Any]) -> str:
       """
       Build system prompt from bot configuration.
      
       Args:
           bot_config: Bot configuration dict
          
       Returns:
           System prompt string
       """
       # If custom system prompt is provided, use it
       if bot_config.get('system_prompt'):
           return bot_config['system_prompt']
      
       # Otherwise, build from configuration
       role = bot_config.get('role', 'assistant')
       tone = bot_config.get('tone', 'professional')
       strictness = bot_config.get('strictness', 'strict')
       citation_required = bot_config.get('citation_required', True)
       fallback_behavior = bot_config.get('fallback_behavior', 'say_dont_know')
      
       # Build prompt parts
       prompt_parts = []
      
       # Role
       if role == 'hr_assistant':
           prompt_parts.append("You are a helpful HR assistant.")
       elif role == 'legal_assistant':
           prompt_parts.append("You are a knowledgeable legal assistant.")
       elif role == 'policy_assistant':
           prompt_parts.append("You are a policy assistant.")
       else:
           prompt_parts.append(f"You are a helpful {role}.")
      
       # Tone
       if tone == 'formal':
           prompt_parts.append("Maintain a formal and professional tone.")
       elif tone == 'friendly':
           prompt_parts.append("Be friendly and approachable in your responses.")
       elif tone == 'concise':
           prompt_parts.append("Keep your responses concise and to the point.")
      
       # Strictness
       if strictness == 'strict':
           prompt_parts.append("Answer ONLY using information from the provided documents.")
           prompt_parts.append("Do not use external knowledge or make assumptions.")
       elif strictness == 'balanced':
           prompt_parts.append("Primarily use information from the provided documents.")
           prompt_parts.append("You may use general knowledge to clarify, but clearly indicate when doing so.")
       else:  # flexible
           prompt_parts.append("Use the provided documents as your primary source.")
           prompt_parts.append("You may supplement with general knowledge when helpful.")
      
       # Citation
       if citation_required:
           prompt_parts.append("Always cite the document name and page number (if available) for your answers.")
           prompt_parts.append("Format citations as: [Source: filename.pdf, page X]")
      
       # Fallback behavior
       if fallback_behavior == 'say_dont_know':
           prompt_parts.append("If you cannot find the answer in the documents, clearly state:")
           prompt_parts.append('"I could not find this information in the uploaded documents."')
       elif fallback_behavior == 'ask_rephrase':
           prompt_parts.append("If you cannot find the answer, ask the user to rephrase their question.")
       elif fallback_behavior == 'escalate':
           prompt_parts.append("If you cannot find the answer, suggest escalating to a human expert.")
      
       prompt_parts.append("Do not hallucinate or make up information.")
      
       return "\n".join(prompt_parts)
  
   @staticmethod
   def build_user_prompt(query: str, context: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
       """
       Build user prompt with query, context, and optional conversation history.
      
       Args:
           query: User's question
           context: Retrieved context from documents
           chat_history: Optional list of previous messages (last 3 exchanges)
          
       Returns:
           User prompt string
       """
       prompt_parts = []
      
       # Add conversation history if available
       if chat_history and len(chat_history) > 0:
           # Get last 6 messages (3 user + 3 assistant)
           recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
          
           if recent_history:
               prompt_parts.append("Previous conversation:")
               for msg in recent_history:
                   role = "User" if msg['role'] == 'user' else "Assistant"
                   prompt_parts.append(f"{role}: {msg['content']}")
               prompt_parts.append("")  # Empty line
      
       # Add document context
       prompt_parts.append(f"Context from documents:\n{context}")
       prompt_parts.append("")  # Empty line
      
       # Add current question
       prompt_parts.append(f"Current question: {query}")
       prompt_parts.append("")  # Empty line
       prompt_parts.append("Please answer the current question based on the context provided above.")
       if chat_history:
           prompt_parts.append("Consider the previous conversation for context, but focus on answering the current question.")
      
       return "\n".join(prompt_parts)
  
   @staticmethod
   def format_messages(system_prompt: str, user_prompt: str) -> list:
       """
       Format prompts as messages for LLM API.
      
       Args:
           system_prompt: System prompt
           user_prompt: User prompt
          
       Returns:
           List of message dicts
       """
       return [
           {"role": "system", "content": system_prompt},
           {"role": "user", "content": user_prompt}
       ]
