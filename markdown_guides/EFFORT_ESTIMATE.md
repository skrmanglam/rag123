# 📊 Effort Estimate: New Features

## Requirement 1: Persistent Chat Sessions (ChatGPT-style sidebar)

### Description
Add a sidebar with scrollable list of chat sessions, similar to ChatGPT interface.

### What Needs to Be Done

#### Database Changes (15 min)
- Add `chat_sessions` table
  ```sql
  CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    bot_id TEXT,
    session_name TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    message_count INTEGER
  )
  ```
- Add `session_id` to `chat_history` (if we want to persist in DB)
- Or keep in session state and save on demand

#### UI Changes (30 min)
- Add sidebar with `st.sidebar`
- List all sessions for current bot
- Click to load session
- "New Chat" button
- "Rename" and "Delete" options
- Auto-generate session names from first message

#### Backend Logic (20 min)
- Load/save sessions from database
- Switch between sessions
- Auto-save current session
- Generate session titles

**Total Effort: ~1-1.5 hours**

**Complexity: Medium**

---

## Requirement 2: Conversational Context (Last 3 messages)

### Description
Use previous messages as context for next response, keeping last 3 messages.

### What Needs to Be Done

#### Prompt Builder Changes (10 min)
- Modify `build_user_prompt` to include conversation history
- Format last 3 messages (6 total: 3 user + 3 assistant)
- Structure: 
  ```
  Previous conversation:
  User: [message 1]
  Assistant: [response 1]
  User: [message 2]
  Assistant: [response 2]
  
  Context from documents:
  [retrieved chunks]
  
  Current question: [new message]
  ```

#### RAG Chain Changes (15 min)
- Pass conversation history to query method
- Extract last N messages
- Format for context
- Handle edge cases (first message, less than 3 messages)

#### UI Changes (5 min)
- Pass chat history to RAG chain
- No visual changes needed

**Total Effort: ~30 minutes**

**Complexity: Low**

---

## Combined Estimate

### If Implementing Both:

**Total Time: ~2 hours**

**Breakdown:**
- Requirement 1 (Chat Sessions): 1-1.5 hours
- Requirement 2 (Context): 30 minutes
- Testing both together: 15-20 minutes

### Priority Recommendation:

**Option A: Implement Both** (Recommended)
- Time: 2 hours
- They work well together
- Chat sessions make context more useful
- Better UX overall

**Option B: Context First, Sessions Later**
- Context: 30 min (quick win!)
- Sessions: Later when needed
- Faster to see results

**Option C: Sessions First, Context Later**
- Sessions: 1.5 hours
- Context: Add later (easy)
- Better organization first

---

## Detailed Implementation Plan

### Requirement 1: Chat Sessions

#### Step 1: Database (15 min)
```python
# Add to schema.sql
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    session_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (bot_id) REFERENCES bots(bot_id)
);

# Add methods to sqlite_db.py
def create_session(bot_id, session_name)
def get_sessions(bot_id)
def update_session(session_id, messages)
def delete_session(session_id)
```

#### Step 2: UI Sidebar (30 min)
```python
# In app_streamlit.py
with st.sidebar:
    st.subheader("💬 Chat Sessions")
    
    if st.button("➕ New Chat"):
        # Create new session
        
    sessions = db.get_sessions(bot_id)
    for session in sessions:
        if st.button(session['name']):
            # Load session
```

#### Step 3: Session Management (20 min)
- Auto-save on each message
- Generate names from first message
- Switch between sessions
- Delete old sessions

### Requirement 2: Conversational Context

#### Step 1: Update Prompt Builder (10 min)
```python
# In prompt_builder.py
def build_user_prompt_with_history(
    query: str, 
    context: str,
    chat_history: List[Dict],
    max_history: int = 3
):
    # Format last N messages
    history_text = format_history(chat_history[-max_history*2:])
    
    return f"""
Previous conversation:
{history_text}

Context from documents:
{context}

Current question: {query}
"""
```

#### Step 2: Update RAG Chain (15 min)
```python
# In rag_chain.py
def query(self, question, bot_id, bot_config, 
          chat_history=None, top_k=5):
    # Extract last N messages
    recent_history = chat_history[-6:] if chat_history else []
    
    # Build prompt with history
    user_prompt = self.prompt_builder.build_user_prompt_with_history(
        question, context, recent_history
    )
```

#### Step 3: Update UI (5 min)
```python
# Pass history to RAG chain
result = rag_chain.query(
    question=question,
    bot_id=bot_id,
    bot_config=bot,
    chat_history=st.session_state['chat_history'],
    top_k=config['retrieval']['top_k']
)
```

---

## Risk Assessment

### Requirement 1 (Chat Sessions)

**Risks:**
- Medium complexity
- Need to handle session switching smoothly
- Storage considerations (how many sessions to keep?)

**Mitigation:**
- Start simple (just save/load)
- Add features incrementally
- Limit to 50 sessions per bot

### Requirement 2 (Context)

**Risks:**
- Low complexity
- Token limit concerns (context + history + documents)
- May confuse bot if history is irrelevant

**Mitigation:**
- Limit to last 3 messages (manageable size)
- Clear context when switching topics
- Test with different conversation flows

---

## Recommendation

### Best Approach:

**Implement Requirement 2 First (30 min)**
- Quick win
- Immediate value
- Low risk
- Easy to test

**Then Implement Requirement 1 (1.5 hours)**
- Builds on working context feature
- Better UX with both features
- More time to design UI properly

**Total: 2 hours for both features**

### Alternative: Quick MVP

**Super Quick Version (1 hour total):**

1. **Simple Context** (20 min)
   - Just pass last 3 messages
   - No fancy formatting
   - Works immediately

2. **Simple Sessions** (40 min)
   - Store in session state only (no DB)
   - Simple list in sidebar
   - New/Switch/Delete only
   - No persistence across restarts

This gives you both features to test quickly!

---

## Questions to Consider

1. **Session Persistence:**
   - Save to database? (persistent)
   - Or session state only? (temporary)
   - Recommendation: Start with session state, add DB later

2. **Session Naming:**
   - Auto-generate from first message?
   - Let user rename?
   - Recommendation: Auto-generate, allow rename

3. **Context Length:**
   - Last 3 messages? (6 total with responses)
   - Or last 5? (10 total)
   - Recommendation: Start with 3, make configurable

4. **Token Limits:**
   - Monitor total prompt size
   - May need to reduce retrieved chunks if history is long
   - Recommendation: Keep eye on total tokens

---

## Next Steps

**If you want to proceed:**

1. Choose approach:
   - Both features (2 hours)
   - Context only (30 min)
   - Quick MVP (1 hour)

2. I'll implement in order:
   - Database changes (if needed)
   - Backend logic
   - UI updates
   - Testing

3. Iterate based on feedback

**Ready to start when you are!** 🚀