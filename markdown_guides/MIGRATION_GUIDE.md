# Migration Guide - New Features

## Overview
This guide helps you migrate your existing RAG chatbot installation to include the new bot deletion and password protection features.

## What's New

### 1. Bot Deletion Feature
- Delete bots completely with all associated data
- Cascade delete from database, vector store, and file system
- Double confirmation required

### 2. Password Protection Feature
- Optional password protection for bots
- SHA-256 hashed passwords
- Session-based authentication
- Lock icon indicator for protected bots

## Migration Steps

### Step 1: Backup Your Data

**IMPORTANT:** Before proceeding, backup your data!

```bash
# Backup database
cp db/rag_builder.db db/rag_builder.db.backup

# Backup uploaded files
cp -r storage storage_backup

# Backup Qdrant data (if using Docker)
docker exec qdrant-container tar czf /qdrant/storage/backup.tar.gz /qdrant/storage
```

### Step 2: Update Database Schema

You have two options:

#### Option A: Add Column to Existing Database (Preserves Data)

Run this SQL command on your existing database:

```bash
sqlite3 db/rag_builder.db "ALTER TABLE bots ADD COLUMN password_hash TEXT;"
```

Or use Python:

```python
import sqlite3

conn = sqlite3.connect('db/rag_builder.db')
conn.execute("ALTER TABLE bots ADD COLUMN password_hash TEXT;")
conn.commit()
conn.close()
print("Migration complete!")
```

#### Option B: Recreate Database (Loses Data)

If you don't have important data:

```bash
# Delete old database
rm db/rag_builder.db

# The new schema will be created automatically on next startup
```

### Step 3: Update Code Files

All code files have been updated. If you're using git:

```bash
git pull origin main
```

Or manually ensure these files are updated:
- `db/schema.sql`
- `db/sqlite_db.py`
- `core/document_loader.py`
- `core/faq_loader.py`
- `main_api.py`
- `static/index.html`
- `static/app.js`
- `static/styles.css`

### Step 4: Restart Application

```bash
# Stop the application
# (Press Ctrl+C if running in terminal)

# Restart
python main_api.py
# or
./start_web.sh
```

### Step 5: Verify Migration

1. **Check Database Schema:**
```bash
sqlite3 db/rag_builder.db ".schema bots"
```

You should see `password_hash TEXT` in the bots table.

2. **Test Existing Bots:**
- Open the web interface
- Verify existing bots still appear in the dropdown
- Select an existing bot (should work without password)
- Verify documents and FAQs are still accessible

3. **Test New Features:**
- Create a new bot with password
- Verify lock icon appears
- Test password protection
- Test bot deletion

## Compatibility Notes

### Existing Bots
- All existing bots will have `password_hash = NULL`
- They remain **public** (no password required)
- No data loss or functionality changes
- You can add passwords later by recreating the bot

### Backward Compatibility
- ✅ Existing bots work without changes
- ✅ All existing features remain functional
- ✅ No breaking changes to API
- ✅ Frontend gracefully handles missing `is_protected` field

## Troubleshooting

### Issue: "No such column: password_hash"

**Solution:** Run the database migration:
```bash
sqlite3 db/rag_builder.db "ALTER TABLE bots ADD COLUMN password_hash TEXT;"
```

### Issue: Bots don't show lock icons

**Solution:** 
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. Check browser console for errors

### Issue: Password prompt doesn't appear

**Solution:**
1. Verify bot has `password_hash` set in database
2. Check browser console for JavaScript errors
3. Ensure `is_protected` field is returned by API

### Issue: Delete button doesn't work

**Solution:**
1. Check browser console for errors
2. Verify API endpoint is accessible
3. Ensure bot exists in database

### Issue: "Failed to delete bot"

**Possible causes:**
- Bot doesn't exist
- Database locked
- File system permissions
- Qdrant connection issues

**Solution:**
1. Check server logs for detailed error
2. Verify file permissions on storage directories
3. Ensure Qdrant is running
4. Try restarting the application

## Rollback Instructions

If you need to rollback:

### Step 1: Restore Backup

```bash
# Restore database
cp db/rag_builder.db.backup db/rag_builder.db

# Restore files
rm -rf storage
cp -r storage_backup storage
```

### Step 2: Revert Code

```bash
git checkout <previous-commit-hash>
```

### Step 3: Restart Application

```bash
python main_api.py
```

## Testing Checklist

After migration, test these scenarios:

### Bot Deletion
- [ ] Delete bot with no documents
- [ ] Delete bot with documents
- [ ] Delete bot with FAQs
- [ ] Cancel deletion
- [ ] Verify all data removed (database, files, vectors)

### Password Protection
- [ ] Create public bot (no password)
- [ ] Create protected bot (with password)
- [ ] Access public bot (no prompt)
- [ ] Access protected bot (prompt shown)
- [ ] Enter correct password
- [ ] Enter wrong password
- [ ] Cancel password prompt
- [ ] Session persistence

### Existing Functionality
- [ ] Upload documents
- [ ] Chat with bot
- [ ] Upload FAQs
- [ ] Update system prompt
- [ ] Create new sessions
- [ ] Switch between bots

## Performance Impact

### Database
- Minimal impact (one additional column)
- No index changes needed
- Query performance unchanged

### API
- Two new endpoints (minimal overhead)
- Password hashing on client-side (no server impact)
- Delete operation is I/O intensive but infrequent

### Frontend
- Negligible JavaScript overhead
- Session storage used for auth state
- No performance degradation

## Security Considerations

### Password Protection
- ⚠️ Demo-level security only
- ✅ SHA-256 hashing
- ✅ No plain text storage
- ❌ No rate limiting
- ❌ No password recovery
- ❌ No encryption at rest

### Bot Deletion
- ✅ Double confirmation required
- ✅ Cascade delete prevents orphaned data
- ❌ No soft delete / recovery
- ❌ No audit trail

## Support

If you encounter issues:

1. Check this migration guide
2. Review troubleshooting section
3. Check server logs: `tail -f logs/app.log`
4. Check browser console for errors
5. Refer to [FEATURE_GUIDE.md](markdown_files/FEATURE_GUIDE.md)
6. Refer to [NEW_FEATURES_PLAN.md](markdown_files/NEW_FEATURES_PLAN.md)

## Next Steps

After successful migration:

1. Read the [FEATURE_GUIDE.md](markdown_files/FEATURE_GUIDE.md) for user documentation
2. Test all features thoroughly
3. Update your team/users about new capabilities
4. Consider implementing additional security measures for production use

---

**Migration completed successfully? Great! Enjoy your new features! 🎉**