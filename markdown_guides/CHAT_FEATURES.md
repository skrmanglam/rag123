# 💬 Chat Features Documentation

## New Features Implemented

### 1. ✅ Conversational Context (Last 3 Messages)
### 2. ✅ Persistent Chat Sessions (ChatGPT-style Sidebar)

---

## Feature 1: Conversational Context

### What It Does

The bot now remembers the last 3 exchanges (6 messages total: 3 user + 3 assistant) and uses them as context for new responses.

### How It Works

**Before:**
```
User: What is the leave policy?
Bot: [Answers from documents]

User: How many days?
Bot: [Doesn't understand "days" refers to leave]
```

**After:**
```
User: What is the leave policy?
Bot: [Answers from documents]

User: How many days?
Bot: [Understands from context this is about leave days]
```

### Technical Implementation

1. **Prompt Builder** (`core/prompt_builder.py`):
   - Added `chat_history` parameter
   - Formats last 6 messages into context
   - Includes in prompt sent to LLM

2. **RAG Chain** (`core/rag_chain.py`):
   - Accepts `chat_history` parameter
   - Passes to prompt builder
   - LLM sees conversation context

3. **Streamlit UI** (`app_streamlit.py`):
   - Passes `chat_history[:-1]` to RAG chain
   - Excludes current question (already in prompt)

### Example Prompt Format

```
Previous conversation:
User: What is the leave policy?
Assistant: Employees get 20 days annual leave...
User: Can I carry forward?
Assistant: Yes, up to 5 days can be carried forward...

Context from documents:
[Retrieved chunks about leave policy]

Current question: How many days can I carry forward?

Please answer the current question based on the context provided above.
Consider the previous conversation for context, but focus on answering the current question.
```

### Benefits

✅ Better follow-up questions
✅ Natural conversation flow
✅ Understands pronouns (it, that, this)
✅ Maintains topic continuity

---

## Feature 2: Persistent Chat Sessions

### What It Does

Sidebar with scrollable list of chat sessions, similar to ChatGPT. Each session maintains its own conversation history.

### UI Layout

```
┌─────────────────────────────────────┐
│ Sidebar                             │
│ ┌─────────────────────────────────┐ │
│ │ Bot Management                  │ │
│ │ Select Bot: [Customer Support]  │ │
│ ├─────────────────────────────────┤ │
│ │ 💬 Chat Sessions                │ │
│ │ [➕ New Chat]                   │ │
│ │                                 │ │
│ │ ▶ What is the leave policy... 🗑│ │
│ │   How do I apply for leave?   🗑│ │
│ │   Office furniture options    🗑│ │
│ │   New Chat                    🗑│ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Features

#### New Chat Button
- Creates a new empty session
- Switches to it automatically
- Named "New Chat" initially

#### Session List
- Shows all sessions for current bot
- Current session marked with ▶
- Click to switch between sessions
- Auto-named from first message

#### Delete Button (🗑️)
- Delete individual sessions
- Can't delete if only one session
- Auto-switches to another session

#### Auto-Naming
- First message becomes session name
- Truncated to 30 characters
- Example: "What is the leave policy..."

### How It Works

#### Session Storage

```python
st.session_state['chat_sessions'] = {
    'bot_id_1': {
        'session_1': {
            'name': 'What is the leave policy...',
            'messages': [
                {'role': 'user', 'content': '...'},
                {'role': 'assistant', 'content': '...'}
            ],
            'created_at': None
        },
        'session_2': {
            'name': 'Office furniture options',
            'messages': [...],
            'created_at': None
        }
    }
}
```

#### Session Switching

1. Click session in sidebar
2. Load messages from that session
3. Update `chat_history`
4. UI refreshes with that conversation

#### Auto-Save

- Every message automatically saved to current session
- Session name updated from first message
- No manual save needed

### Usage

#### Start New Conversation
1. Click "➕ New Chat"
2. Start chatting
3. Session auto-named from first message

#### Switch Conversations
1. Click any session in sidebar
2. Previous conversation loads
3. Continue where you left off

#### Delete Old Conversations
1. Click 🗑️ next to session
2. Session deleted
3. Switches to another session

---

## Combined Benefits

### Better Conversations
- Context from previous messages
- Multiple conversation threads
- Easy to switch topics

### Organization
- Keep different topics separate
- Find old conversations easily
- Clean workspace

### Workflow
```
1. Create bot
2. Upload documents
3. Start chatting (auto-creates session)
4. Ask follow-up questions (uses context)
5. Start new topic (click "New Chat")
6. Switch back to previous topic (click session)
7. Continue conversation (context maintained)
```

---

## Technical Details

### Context Window

**Current:** Last 3 exchanges (6 messages)

**Why 3?**
- Balances context vs token limit
- Enough for most follow-ups
- Doesn't overwhelm the prompt

**Can be adjusted in code:**
```python
# In app_streamlit.py
chat_history=st.session_state['chat_history'][-6:]  # Last 6 messages
```

### Session Storage

**Current:** Session state (temporary)

**Persistence:**
- Sessions lost on browser refresh
- Could add database persistence later
- Good for MVP/testing

**To add DB persistence:**
1. Add `chat_sessions` table to schema
2. Save on each message
3. Load on bot selection

### Token Management

**Considerations:**
- Context + History + Documents = Total tokens
- Monitor total prompt size
- May need to reduce `top_k` if history is long

**Current approach:**
- Last 3 exchanges (manageable)
- 5 document chunks (default)
- Should fit in most model limits

---

## Usage Examples

### Example 1: Follow-up Questions

```
Session: "Leave Policy Questions"

User: What is the annual leave policy?
Bot: Employees get 20 days of annual leave per year...

User: Can I carry forward unused days?
Bot: [Uses context - knows "days" means leave days]
     Yes, you can carry forward up to 5 unused days...

User: What about sick leave?
Bot: [New topic, but maintains conversation flow]
     Sick leave is separate. Employees get 10 days...
```

### Example 2: Multiple Topics

```
Session 1: "Leave Policy"
- Questions about leave
- Carry forward rules
- Sick leave

[Click "New Chat"]

Session 2: "Office Furniture"
- Desk options
- Chair recommendations
- Budget questions

[Click Session 1]
- Back to leave discussion
- Context maintained
```

---

## Best Practices

### For Users

1. **Start New Chat for New Topics**
   - Keeps conversations organized
   - Easier to find later

2. **Use Descriptive First Messages**
   - Session auto-named from first message
   - "What is X?" better than "Hi"

3. **Delete Old Sessions**
   - Keep sidebar clean
   - Remove test conversations

### For Developers

1. **Monitor Token Usage**
   - Context + history can be large
   - Adjust `top_k` if needed

2. **Consider DB Persistence**
   - Add if users need permanent history
   - Current: session state only

3. **Adjust Context Window**
   - Change from 3 to 5 exchanges if needed
   - Balance context vs tokens

---

## Troubleshooting

### Context Not Working?

**Check:**
1. Is `chat_history` being passed?
2. Are messages in correct format?
3. Is prompt builder receiving history?

**Debug:**
```python
# In app_streamlit.py
print("Chat history:", st.session_state['chat_history'])
```

### Sessions Not Saving?

**Check:**
1. Is `chat_sessions` initialized?
2. Is `current_session_id` set?
3. Are messages being appended?

**Debug:**
```python
# In app_streamlit.py
print("Sessions:", st.session_state.get('chat_sessions', {}))
```

### Session Names Not Updating?

**Check:**
1. Is first message being captured?
2. Is name being truncated correctly?
3. Is session being saved?

---

## Future Enhancements

### Potential Improvements

1. **Database Persistence**
   - Save sessions to SQLite
   - Persist across browser refreshes
   - Share sessions across devices

2. **Session Search**
   - Search within sessions
   - Filter by date
   - Tag sessions

3. **Export/Import**
   - Export conversation as PDF
   - Share sessions
   - Import old conversations

4. **Advanced Context**
   - Configurable context window
   - Smart context selection
   - Summarize old messages

5. **Session Management**
   - Rename sessions manually
   - Archive old sessions
   - Session folders/categories

---

## Summary

### What You Get

✅ **Conversational Context**
- Last 3 exchanges remembered
- Better follow-up questions
- Natural conversation flow

✅ **Chat Sessions**
- Multiple conversation threads
- Easy switching
- Auto-naming
- Clean organization

### No Restart Needed!

Both features work immediately:
- Context: Automatic
- Sessions: In session state
- Just restart Streamlit to see changes

---

**Enjoy better conversations with your RAG chatbot!** 🎉