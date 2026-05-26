# Implementation Checklist for New Features

## Quick Reference Guide

This checklist provides a step-by-step guide to implement the bot deletion and password protection features.

---

## 📋 Pre-Implementation Checklist

- [x] Review current architecture
- [x] Identify data dependencies
- [x] Design feature specifications
- [x] Create implementation plan
- [ ] Backup current database
- [ ] Create feature branch (optional)

---

## 🗑️ Feature 1: Bot Deletion

### Backend Changes

#### 1. Update Database Schema
**File:** `db/schema.sql`
- ✅ No changes needed (CASCADE DELETE already configured)

#### 2. Update SQLiteDB Class
**File:** `db/sqlite_db.py`
- [ ] Add `delete_bot(bot_id)` method

```python
def delete_bot(self, bot_id: str) -> bool:
    """Delete a bot and all associated data via CASCADE."""
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

#### 3. Update DocumentLoader Class
**File:** `core/document_loader.py`
- [ ] Add `delete_bot_files(bot_id)` method

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

#### 4. Update FAQLoader Class
**File:** `core/faq_loader.py`
- [ ] Add `delete_bot_faq_files(bot_id)` method

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

#### 5. Add DELETE Endpoint
**File:** `main_api.py`
- [ ] Add `DELETE /bots/{bot_id}` endpoint (see plan for full code)

### Frontend Changes

#### 6. Update HTML
**File:** `static/index.html`
- [ ] Add delete button in Configuration tab
- [ ] Add to `setupEventListeners()` in app.js

#### 7. Update JavaScript
**File:** `static/app.js`
- [ ] Add `deleteBotWithConfirmation()` function
- [ ] Wire up event listener

#### 8. Update CSS (Optional)
**File:** `static/styles.css`
- [ ] Add `.btn-danger` styles
- [ ] Add `.config-actions` styles

### Testing
- [ ] Create test bot with documents
- [ ] Delete bot and verify all data removed
- [ ] Test cancellation flow
- [ ] Test error handling

---

## 🔒 Feature 2: Password Protection

### Backend Changes

#### 1. Update Database Schema
**File:** `db/schema.sql`
- [ ] Add `password_hash TEXT` column to bots table

```sql
ALTER TABLE bots ADD COLUMN password_hash TEXT;
```

**Migration:** Run this SQL on existing database or recreate database.

#### 2. Update SQLiteDB Class
**File:** `db/sqlite_db.py`
- [ ] Add `password_hash` parameter to `create_bot()` method
- [ ] Update INSERT statement to include password_hash

#### 3. Update API Models
**File:** `main_api.py`
- [ ] Add `password_hash: Optional[str]` to `BotCreateRequest`
- [ ] Add `is_protected: bool` to `BotInfo`

#### 4. Update Endpoints
**File:** `main_api.py`
- [ ] Update `list_bots()` to include `is_protected` field
- [ ] Update `create_bot()` to accept and store password_hash
- [ ] Add `POST /bots/{bot_id}/verify-password` endpoint

### Frontend Changes

#### 5. Update HTML
**File:** `static/index.html`
- [ ] Add password field to bot creation form
- [ ] Add help text explaining optional password

#### 6. Update JavaScript
**File:** `static/app.js`
- [ ] Add `hashPassword(password)` utility function
- [ ] Update `handleBotCreation()` to hash and send password
- [ ] Update `loadBots()` to show lock icon for protected bots
- [ ] Add `verifyBotPassword(botId)` function
- [ ] Update `handleBotSelection()` to check password

#### 7. Update CSS (Optional)
**File:** `static/styles.css`
- [ ] Add `.help-text` styles

### Testing
- [ ] Create public bot (no password)
- [ ] Create protected bot (with password)
- [ ] Test accessing public bot
- [ ] Test accessing protected bot with correct password
- [ ] Test accessing protected bot with wrong password
- [ ] Test session persistence
- [ ] Test password cancellation

---

## 🚀 Deployment Steps

1. [ ] Backup current database
2. [ ] Run database migration (add password_hash column)
3. [ ] Deploy updated backend files
4. [ ] Deploy updated frontend files
5. [ ] Restart application
6. [ ] Test both features end-to-end
7. [ ] Update user documentation

---

## 📝 Files to Modify

### Backend Files (6 files)
1. `db/schema.sql` - Add password_hash column
2. `db/sqlite_db.py` - Add delete_bot and update create_bot
3. `core/document_loader.py` - Add delete_bot_files
4. `core/faq_loader.py` - Add delete_bot_faq_files
5. `main_api.py` - Add endpoints and update models
6. `core/vector_store.py` - ✅ Already has delete_by_bot

### Frontend Files (3 files)
1. `static/index.html` - Add UI elements
2. `static/app.js` - Add functions and logic
3. `static/styles.css` - Add styles

### Documentation Files (2 files)
1. `markdown_files/NEW_FEATURES_PLAN.md` - ✅ Created
2. `markdown_files/FEATURE_GUIDE.md` - User-facing guide

---

## ⚠️ Important Notes

### Bot Deletion
- Deletion is **permanent** and **cannot be undone**
- All associated data is removed (documents, FAQs, files, embeddings)
- Requires double confirmation (dialog + name verification)
- Uses CASCADE DELETE for database integrity

### Password Protection
- Uses SHA-256 hashing (client-side)
- Passwords are **never** stored in plain text
- Session-based authentication (cleared on browser close)
- Optional feature (NULL = public bot)
- Demo-level security (not production-grade)

### Database Migration
For existing installations:
```sql
-- Run this SQL command on your database
ALTER TABLE bots ADD COLUMN password_hash TEXT;
```

Or simply delete and recreate the database (will lose all data).

---

## 🧪 Testing Scenarios

### Bot Deletion Tests
1. ✅ Delete bot with no documents
2. ✅ Delete bot with documents
3. ✅ Delete bot with FAQs
4. ✅ Delete bot with both documents and FAQs
5. ✅ Cancel deletion
6. ✅ Verify all data removed from:
   - SQLite database
   - Qdrant vector store
   - File system (uploaded_files)
   - File system (faq_files)

### Password Protection Tests
1. ✅ Create bot without password
2. ✅ Create bot with password
3. ✅ Access public bot (no prompt)
4. ✅ Access protected bot (prompt shown)
5. ✅ Enter correct password
6. ✅ Enter wrong password
7. ✅ Cancel password prompt
8. ✅ Session persistence (same session)
9. ✅ Session expiry (new session)
10. ✅ Lock icon display in bot list

---

## 📊 Estimated Time

- **Bot Deletion**: 2-3 hours
- **Password Protection**: 2-3 hours
- **Testing**: 1-2 hours
- **Documentation**: 1 hour

**Total**: 6-9 hours

---

## 🎯 Success Criteria

### Bot Deletion
- ✅ Bot and all data completely removed
- ✅ No orphaned records in database
- ✅ No orphaned files in storage
- ✅ No orphaned vectors in Qdrant
- ✅ Proper error handling
- ✅ User confirmation required

### Password Protection
- ✅ Password hashed before storage
- ✅ Lock icon shown for protected bots
- ✅ Password prompt on access
- ✅ Session remembers verification
- ✅ Wrong password rejected
- ✅ Public bots work without password
- ✅ Backward compatible with existing bots

---

## 🔗 Related Documentation

- [NEW_FEATURES_PLAN.md](./NEW_FEATURES_PLAN.md) - Detailed implementation plan
- [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - Project overview
- [WEB_INTERFACE_GUIDE.md](../WEB_INTERFACE_GUIDE.md) - UI guide

---

## 💡 Tips

1. **Test incrementally**: Implement and test each feature separately
2. **Backup first**: Always backup database before migration
3. **Use version control**: Commit after each working feature
4. **Test edge cases**: Empty bots, network errors, etc.
5. **Document changes**: Update user guide after implementation

---

## ✅ Final Checklist

Before marking complete:
- [ ] All backend changes implemented
- [ ] All frontend changes implemented
- [ ] Database migrated successfully
- [ ] All tests passing
- [ ] Documentation updated
- [ ] User guide created
- [ ] Code reviewed
- [ ] Deployed to production (if applicable)

---

**Ready to implement? Start with the backend changes, then move to frontend, and finally test everything together!**