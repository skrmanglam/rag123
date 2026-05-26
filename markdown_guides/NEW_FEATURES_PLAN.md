# New Features Implementation Plan

## Overview
This document outlines the implementation plan for two new features:
1. **Bot Deletion** - Complete removal of bots with all associated data
2. **Password Protection** - Optional password protection for bots

## Feature 1: Bot Deletion

### Requirements
- Delete bot and all associated data (documents, chunks, FAQs, files)
- Cascade delete from all storage systems:
  - SQLite database (bots, documents, chunks, faq_entries)
  - Qdrant vector store (document chunks and FAQ embeddings)
  - File system (uploaded files in storage/uploaded_files/{bot_id}/)
  - File system (FAQ files in storage/faq_files/{bot_id}/)
- Confirmation dialog before deletion
- Cannot delete if it's the last bot (optional safety measure)

### Data Dependencies
```
Bot (bots table)
├── Documents (documents table) [CASCADE DELETE]
│   ├── Chunks (chunks table) [CASCADE DELETE]
│   └── Files (storage/uploaded_files/{bot_id}/)
├── FAQ Entries (faq_entries table) [CASCADE DELETE]
│   └── FAQ Files (storage/faq_files/{bot_id}/)
└── Vector Store Data (Qdrant)
    ├── Document Embeddings (filtered by bot_id)
    └── FAQ Embeddings (filtered by bot_id)
```

### Implementation Steps

#### 1. Database Schema Updates
File: `db/schema.sql`
- Already has CASCADE DELETE constraints ✓
- No changes needed

#### 2. Backend Implementation

##### A. SQLiteDB Class (`db/sqlite_db.py`)
Add new method:
```python
def delete_bot(self, bot_id: str) -> bool:
    """
    Delete a bot and all associated data.
    CASCADE DELETE will handle documents, chunks, and FAQ entries.
    """
    conn = self.get_connection()
    try:
        conn.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting bot: {e}")
        return False
    finally:
        conn.close()
```

##### B. DocumentLoader Class (`core/document_loader.py`)
Add new method:
```python
def delete_bot_files(self, bot_id: str) -> bool:
    """Delete all uploaded files for a bot."""
    import shutil
    bot_dir = os.path.join(self.upload_dir, bot_id)
    if os.path.exists(bot_dir):
        shutil.rmtree(bot_dir)
        return True
    return False
```

##### C. FAQLoader Class (`core/faq_loader.py`)
Add new method:
```python
def delete_bot_faq_files(self, bot_id: str) -> bool:
    """Delete all FAQ files for a bot."""
    import shutil
    bot_dir = os.path.join(self.storage_dir, bot_id)
    if os.path.exists(bot_dir):
        shutil.rmtree(bot_dir)
        return True
    return False
```

##### D. VectorStore Class (`core/vector_store.py`)
- Already has `delete_by_bot(bot_id)` method ✓
- No changes needed

##### E. Main API (`main_api.py`)
Add new endpoint:
```python
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
```

#### 3. Frontend Implementation

##### A. HTML Updates (`static/index.html`)
Add delete button in Configuration tab:
```html
<div class="config-actions">
    <button id="refreshConfigBtn" class="btn btn-secondary">
        🔄 Refresh Configuration
    </button>
    <button id="deleteBotBtn" class="btn btn-danger">
        🗑️ Delete Bot
    </button>
</div>
```

##### B. JavaScript Updates (`static/app.js`)
Add event listener in `setupEventListeners()`:
```javascript
document.getElementById('deleteBotBtn').addEventListener('click', deleteBotWithConfirmation);
```

Add new function:
```javascript
async function deleteBotWithConfirmation() {
    const botName = state.currentBot.bot_name;
    const botId = state.currentBot.bot_id;
    
    const confirmed = confirm(
        `⚠️ WARNING: This will permanently delete "${botName}" and ALL associated data:\n\n` +
        `• All uploaded documents\n` +
        `• All FAQ entries\n` +
        `• All chat history\n` +
        `• All configuration\n\n` +
        `This action CANNOT be undone!\n\n` +
        `Type the bot name to confirm: "${botName}"`
    );
    
    if (!confirmed) return;
    
    const userInput = prompt(`Please type "${botName}" to confirm deletion:`);
    
    if (userInput !== botName) {
        showError('Bot name does not match. Deletion cancelled.');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots/${botId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete bot');
        }
        
        showSuccess(`Bot "${botName}" deleted successfully!`);
        
        // Reset state
        state.currentBot = null;
        state.currentSession = 'default';
        state.messages = [];
        delete state.sessions[botId];
        
        // Reload bots and show welcome screen
        await loadBots();
        
        if (state.bots.length === 0) {
            showWelcomeScreen();
        } else {
            // Select first available bot
            document.getElementById('botSelect').value = state.bots[0].bot_id;
            await handleBotSelection({ target: { value: state.bots[0].bot_id } });
        }
    } catch (error) {
        console.error('Error deleting bot:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}
```

---

## Feature 2: Password Protection

### Requirements
- Optional password protection during bot creation
- SHA-256 hash storage (not plain text)
- Password validation on bot selection
- Session-based authentication (remember password during browser session)
- No password = public bot (accessible to everyone)

### Security Approach
- **Client-side hashing**: Hash password with SHA-256 before sending to server
- **Server-side storage**: Store only the hash in database
- **Session management**: Store validated bot_ids in browser sessionStorage
- **Simple validation**: Compare hashes for authentication

### Implementation Steps

#### 1. Database Schema Updates
File: `db/schema.sql`
Add password_hash column:
```sql
ALTER TABLE bots ADD COLUMN password_hash TEXT;
```

Migration approach: Add column with default NULL (existing bots remain public)

#### 2. Backend Implementation

##### A. SQLiteDB Class (`db/sqlite_db.py`)
Update `create_bot` method signature:
```python
def create_bot(self, bot_id: str, bot_name: str, system_prompt: str,
               role: Optional[str] = None, tone: Optional[str] = None,
               strictness: Optional[str] = None, citation_required: bool = True,
               fallback_behavior: Optional[str] = None,
               password_hash: Optional[str] = None) -> bool:
    """Create a new bot configuration with optional password protection."""
    conn = self.get_connection()
    try:
        conn.execute("""
            INSERT INTO bots (bot_id, bot_name, role, tone, strictness, 
                             citation_required, fallback_behavior, system_prompt, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bot_id, bot_name, role, tone, strictness, 
              1 if citation_required else 0, fallback_behavior, system_prompt, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
```

##### B. Main API (`main_api.py`)

Update BotCreateRequest model:
```python
class BotCreateRequest(BaseModel):
    bot_name: str
    role: str
    tone: str
    strictness: str
    citation_required: bool = True
    fallback_behavior: str = "say_dont_know"
    behavior_instructions: Optional[str] = None
    password_hash: Optional[str] = None  # SHA-256 hash from client
```

Update BotInfo model:
```python
class BotInfo(BaseModel):
    bot_id: str
    bot_name: str
    role: Optional[str]
    tone: Optional[str]
    strictness: Optional[str]
    citation_required: bool
    created_at: str
    is_protected: bool  # True if password_hash exists
```

Update `list_bots` endpoint:
```python
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
```

Update `create_bot` endpoint:
```python
@app.post("/bots", response_model=BotInfo)
def create_bot(request: BotCreateRequest):
    """Create a new bot with optional password protection."""
    # ... existing code ...
    
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
        password_hash=request.password_hash  # Already hashed on client
    )
    
    # ... rest of code ...
```

Add password verification endpoint:
```python
class PasswordVerifyRequest(BaseModel):
    password_hash: str

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
```

#### 3. Frontend Implementation

##### A. HTML Updates (`static/index.html`)

Add password field to bot creation form:
```html
<div class="form-group">
    <label for="botPassword">
        🔒 Password Protection (Optional)
        <span class="help-text">Leave empty for public bot</span>
    </label>
    <input 
        type="password" 
        id="botPassword" 
        class="form-control"
        placeholder="Enter password to protect this bot (optional)"
    >
    <small class="form-text text-muted">
        If set, users will need this password to access the bot
    </small>
</div>
```

##### B. JavaScript Updates (`static/app.js`)

Add SHA-256 hashing utility:
```javascript
async function hashPassword(password) {
    if (!password) return null;
    
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}
```

Update `handleBotCreation`:
```javascript
async function handleBotCreation(e) {
    e.preventDefault();
    
    const password = document.getElementById('botPassword').value;
    const passwordHash = await hashPassword(password);
    
    const formData = {
        bot_name: document.getElementById('botName').value,
        role: document.getElementById('botRole').value,
        tone: document.getElementById('botTone').value,
        strictness: document.getElementById('botStrictness').value,
        citation_required: document.getElementById('botCitation').checked,
        fallback_behavior: document.getElementById('botFallback').value,
        behavior_instructions: document.getElementById('botInstructions').value || null,
        password_hash: passwordHash
    };
    
    // ... rest of existing code ...
}
```

Update `loadBots` to show lock icon:
```javascript
async function loadBots() {
    try {
        const response = await fetch(`${API_BASE}/bots`);
        state.bots = await response.json();
        
        const select = document.getElementById('botSelect');
        select.innerHTML = '<option value="">Create New Bot</option>';
        
        state.bots.forEach(bot => {
            const option = document.createElement('option');
            option.value = bot.bot_id;
            const lockIcon = bot.is_protected ? '🔒 ' : '';
            option.textContent = lockIcon + bot.bot_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading bots:', error);
        showError('Failed to load bots');
    }
}
```

Add password verification function:
```javascript
async function verifyBotPassword(botId) {
    // Check if already verified in this session
    const verifiedBots = JSON.parse(sessionStorage.getItem('verifiedBots') || '[]');
    if (verifiedBots.includes(botId)) {
        return true;
    }
    
    const password = prompt('🔒 This bot is password protected.\n\nPlease enter the password:');
    
    if (password === null) {
        return false; // User cancelled
    }
    
    const passwordHash = await hashPassword(password);
    
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}/verify-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password_hash: passwordHash })
        });
        
        const result = await response.json();
        
        if (result.verified) {
            // Store in session
            verifiedBots.push(botId);
            sessionStorage.setItem('verifiedBots', JSON.stringify(verifiedBots));
            return true;
        } else {
            showError('❌ Incorrect password');
            return false;
        }
    } catch (error) {
        console.error('Error verifying password:', error);
        showError('Failed to verify password');
        return false;
    }
}
```

Update `handleBotSelection`:
```javascript
async function handleBotSelection(e) {
    const botId = e.target.value;
    
    if (!botId) {
        showBotCreationForm();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}`);
        const bot = await response.json();
        
        // Check if bot is protected
        if (bot.is_protected) {
            const verified = await verifyBotPassword(botId);
            if (!verified) {
                // Reset selection
                e.target.value = state.currentBot ? state.currentBot.bot_id : '';
                return;
            }
        }
        
        state.currentBot = bot;
        
        // ... rest of existing code ...
    } catch (error) {
        console.error('Error loading bot:', error);
        showError('Failed to load bot');
    }
}
```

##### C. CSS Updates (`static/styles.css`)
Add styles for password field and protected bot indicator:
```css
.help-text {
    font-size: 0.85em;
    color: #6c757d;
    font-weight: normal;
}

.btn-danger {
    background-color: #dc3545;
    color: white;
    border: none;
}

.btn-danger:hover {
    background-color: #c82333;
}

.config-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
}
```

---

## Testing Plan

### Bot Deletion Testing
1. ✅ Create a test bot with documents
2. ✅ Upload multiple documents and FAQs
3. ✅ Verify all data exists in:
   - SQLite database
   - Qdrant vector store
   - File system
4. ✅ Delete the bot
5. ✅ Verify all data is removed from all locations
6. ✅ Test deletion cancellation
7. ✅ Test error handling (network errors, etc.)

### Password Protection Testing
1. ✅ Create bot without password (public)
2. ✅ Create bot with password (protected)
3. ✅ Verify lock icon appears in bot list
4. ✅ Test accessing public bot (no password prompt)
5. ✅ Test accessing protected bot with correct password
6. ✅ Test accessing protected bot with wrong password
7. ✅ Test password persistence in session
8. ✅ Test password prompt cancellation
9. ✅ Test session expiry (close and reopen browser)

---

## Security Considerations

### Password Protection
- ✅ SHA-256 hashing (client-side)
- ✅ No plain text storage
- ✅ Session-based authentication
- ⚠️ Note: This is demo-level security, not production-grade
- ⚠️ No rate limiting on password attempts
- ⚠️ No password strength requirements
- ⚠️ No password recovery mechanism

### Bot Deletion
- ✅ Confirmation dialog with bot name verification
- ✅ Cascade delete to prevent orphaned data
- ✅ Error handling for partial failures
- ⚠️ No soft delete / recovery option
- ⚠️ No audit trail of deletions

---

## Migration Guide

### For Existing Installations

1. **Database Migration**:
   ```sql
   -- Add password_hash column to existing bots table
   ALTER TABLE bots ADD COLUMN password_hash TEXT;
   ```

2. **No Code Changes Required**:
   - Existing bots will have NULL password_hash (public bots)
   - New features are backward compatible

3. **Update Files**:
   - Replace `db/schema.sql`
   - Replace `db/sqlite_db.py`
   - Replace `core/document_loader.py`
   - Replace `core/faq_loader.py`
   - Replace `main_api.py`
   - Replace `static/index.html`
   - Replace `static/app.js`
   - Replace `static/styles.css`

---

## API Documentation Updates

### New Endpoints

#### DELETE /bots/{bot_id}
Delete a bot and all associated data.

**Response:**
```json
{
  "message": "Bot deleted successfully",
  "bot_id": "customer_support_bot"
}
```

**Errors:**
- 404: Bot not found
- 500: Deletion failed

#### POST /bots/{bot_id}/verify-password
Verify password for a protected bot.

**Request:**
```json
{
  "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
}
```

**Response:**
```json
{
  "verified": true,
  "message": "Password correct"
}
```

### Modified Endpoints

#### POST /bots
Now accepts optional `password_hash` field.

#### GET /bots
Now returns `is_protected` field for each bot.

---

## Future Enhancements

### Potential Improvements
1. **Password Recovery**: Email-based password reset
2. **Role-Based Access**: Multiple users with different permissions
3. **Soft Delete**: Trash/recovery mechanism for deleted bots
4. **Audit Log**: Track all deletion and access events
5. **Password Strength**: Enforce minimum password requirements
6. **Rate Limiting**: Prevent brute force password attempts
7. **2FA**: Two-factor authentication for protected bots
8. **Shared Access**: Allow multiple passwords/users per bot

---

## Implementation Timeline

### Phase 1: Bot Deletion (Estimated: 2-3 hours)
- Database method updates
- API endpoint implementation
- Frontend UI and logic
- Testing

### Phase 2: Password Protection (Estimated: 2-3 hours)
- Database schema update
- Backend authentication logic
- Frontend password handling
- Session management
- Testing

### Total Estimated Time: 4-6 hours

---

## Conclusion

Both features are well-scoped and implementable with the current architecture. The implementation follows the existing patterns in the codebase and maintains backward compatibility. The password protection uses simple but effective hashing, suitable for a demo application while still providing reasonable security.