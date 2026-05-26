# RAG Chatbot Web Interface Guide


## Overview


The new web interface replaces Streamlit with a clean, modern HTML/CSS/JavaScript frontend that uses your existing FastAPI backend. This eliminates the persistent rendering issues you experienced with Streamlit.


## Architecture


```
┌─────────────────────────────────────┐
│   Frontend (HTML/CSS/JS)            │
│   - Clean, responsive UI            │
│   - Session management              │
│   - Real-time chat                  │
└──────────────┬──────────────────────┘
              │ HTTP/REST API
┌──────────────▼──────────────────────┐
│   FastAPI Backend                   │
│   - Existing endpoints              │
│   - RAG processing                  │
│   - FAQ management                  │
└─────────────────────────────────────┘
```


## Features


✅ **Bot Selection** - Choose from available bots in sidebar
✅ **Chat Sessions** - Create, switch, and delete chat sessions
✅ **Real-time Chat** - Send messages and get responses
✅ **Fuzzy FAQ Toggle** - Switch between vector and fuzzy search
✅ **Source Citations** - View document sources for answers
✅ **Responsive Design** - Works on desktop and mobile
✅ **No Framework Issues** - Pure HTML/CSS/JS, no rendering bugs


## Getting Started


### 1. Start the Server


```bash
# Option 1: Using the startup script
./start_web.sh


# Option 2: Direct Python command
python main_api.py
```


The server will start on `http://localhost:8000`


### 2. Access the Interface


Open your browser and navigate to:
```
http://localhost:8000
```


### 3. Using the Interface


1. **Select a Bot**: Choose a bot from the dropdown in the sidebar
2. **Start Chatting**: Type your question in the input box at the bottom
3. **View Sources**: Click on "📚 Sources" to see document references
4. **Manage Sessions**:
  - Click "➕ New Chat" to create a new session
  - Click on a session to switch to it
  - Click 🗑️ to delete a session
5. **Toggle Fuzzy FAQ**: Enable/disable fuzzy search for FAQ queries
6. **Clear Chat**: Click "🗑️ Clear Chat" to reset the current session


## File Structure


```
static/
├── index.html      # Main HTML structure
├── styles.css      # Modern, responsive styling
└── app.js          # JavaScript for API interactions


main_api.py         # FastAPI backend (updated)
start_web.sh        # Startup script
```


## Key Improvements Over Streamlit


| Feature | Streamlit | New Web Interface |
|---------|-----------|-------------------|
| Rendering Issues | ❌ Frequent blank screens | ✅ Stable, no issues |
| Session Management | ❌ Complex, buggy | ✅ Simple, reliable |
| Performance | ⚠️ Slower | ✅ Fast, lightweight |
| Customization | ⚠️ Limited | ✅ Full control |
| Cross-platform | ❌ Windows issues | ✅ Works everywhere |
| Dependencies | ⚠️ Heavy | ✅ Minimal |


## API Endpoints Used


The frontend uses these FastAPI endpoints:


- `GET /bots` - List all bots
- `GET /bots/{bot_id}` - Get bot details
- `POST /chat/{bot_id}` - Send chat message
- `GET /bots/{bot_id}/documents` - List bot documents
- `POST /bots/{bot_id}/faq/search` - Search FAQ


## Customization


### Changing Colors


Edit `static/styles.css` and modify the CSS variables:


```css
:root {
   --primary-color: #2563eb;      /* Main blue color */
   --primary-hover: #1d4ed8;      /* Hover state */
   --background: #f8fafc;         /* Page background */
   /* ... more variables ... */
}
```


### Adding Features


The JavaScript is modular and easy to extend. Key functions:


- `sendMessage()` - Handles sending messages
- `addMessage()` - Adds messages to UI
- `renderMessages()` - Renders all messages
- `createNewSession()` - Creates new chat session


## Troubleshooting


### Port Already in Use


If port 8000 is already in use:


```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9


# Or use a different port
uvicorn main_api:app --host 0.0.0.0 --port 8001
```


### Static Files Not Loading


Ensure the `static/` directory exists and contains all three files:
- index.html
- styles.css
- app.js


### CORS Issues


If accessing from a different domain, add CORS middleware to `main_api.py`:


```python
from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)
```


## Migration from Streamlit


### What Changed


1. **UI Framework**: Streamlit → HTML/CSS/JS
2. **Entry Point**: `app_streamlit.py` → `main_api.py`
3. **Startup**: `streamlit run` → `python main_api.py`


### What Stayed the Same


1. ✅ All backend logic (RAG, embeddings, vector store)
2. ✅ Database structure
3. ✅ FAQ functionality
4. ✅ Document processing
5. ✅ Bot configurations


### Migrating Data


No migration needed! The new interface uses the same:
- SQLite database
- Qdrant vector store
- Document storage
- FAQ data


## Performance Tips


1. **Browser Caching**: Static files are cached automatically
2. **Session Storage**: Chat sessions stored in browser memory
3. **Lazy Loading**: Messages rendered on demand
4. **Debouncing**: Input events are optimized


## Security Considerations


For production deployment:


1. **Enable HTTPS**: Use a reverse proxy (nginx, Caddy)
2. **Add Authentication**: Implement user login
3. **Rate Limiting**: Prevent API abuse
4. **Input Validation**: Already handled by FastAPI
5. **CORS**: Configure allowed origins


## Next Steps


### Optional Enhancements


1. **File Upload UI**: Add document upload interface
2. **Bot Creation**: Add bot creation form
3. **FAQ Management**: Add FAQ upload/management UI
4. **User Authentication**: Add login system
5. **Dark Mode**: Add theme toggle
6. **Export Chat**: Download chat history


### Deployment


For production:


```bash
# Install production server
pip install gunicorn


# Run with gunicorn
gunicorn main_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```


## Support


If you encounter any issues:


1. Check browser console for JavaScript errors (F12)
2. Check FastAPI logs for backend errors
3. Verify all static files are present
4. Ensure port 8000 is available


## Conclusion


The new web interface provides a stable, reliable alternative to Streamlit with:
- ✅ No rendering issues
- ✅ Better performance
- ✅ Full customization
- ✅ Cross-platform compatibility
- ✅ Professional appearance


Enjoy your bug-free chatbot interface! 🎉

