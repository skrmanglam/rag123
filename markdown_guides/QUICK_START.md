# Quick Start Guide - New Features

## 🎉 What's New

Two powerful new features have been added:

1. **🗑️ Bot Deletion** - Delete bots completely with all data
2. **🔒 Password Protection** - Protect bots with optional passwords

## 🚀 Getting Started (Existing Users)

### Step 1: Migrate Your Database

**The database has already been migrated!** ✅

If you need to run it again:
```bash
python migrate_db.py
```

### Step 2: Start the Application

```bash
python main_api.py
```

Or use the startup script:
```bash
./start_web.sh
```

### Step 3: Open Your Browser

Navigate to: **http://localhost:8000**

## 🎯 Try the New Features

### Create a Password-Protected Bot

1. Click "Create New Bot" or select from dropdown
2. Fill in bot details (name, role, tone, etc.)
3. **NEW:** Enter a password in the "🔒 Password Protection" field
   - Leave empty for a public bot
   - Enter a password to protect it
4. Click "Create Bot"
5. Your bot now has a 🔒 icon in the dropdown!

### Access a Protected Bot

1. Select a bot with 🔒 icon from dropdown
2. Enter the password when prompted
3. Access granted for your session!
4. You won't be asked again until you close the browser

### Delete a Bot

1. Select any bot
2. Go to the **Configuration** tab
3. Scroll down and click **"🗑️ Delete Bot"** button
4. Confirm in the dialog
5. Type the exact bot name to confirm
6. Bot and ALL data permanently deleted!

## 📋 What Gets Deleted

When you delete a bot, everything is removed:
- ✅ Bot configuration
- ✅ All uploaded documents
- ✅ All FAQ entries
- ✅ All chat history
- ✅ All files from storage
- ✅ All vector embeddings

**⚠️ This is permanent and cannot be undone!**

## 🔐 Password Security

### How It Works
- Passwords are hashed with SHA-256 (client-side)
- Never stored in plain text
- Session-based authentication
- Lock icon (🔒) shows protected bots

### Important Notes
- ⚠️ This is demo-level security
- ⚠️ No password recovery mechanism
- ⚠️ Not for production use with sensitive data
- ✅ Good for demos and testing

## 💡 Tips

### Password Protection
- Use unique passwords for different bots
- Remember your passwords (no recovery!)
- Leave password empty for public bots
- Protected bots show 🔒 icon

### Bot Deletion
- Double-check before deleting
- Type exact bot name to confirm
- Export important data first
- Keep at least one bot for testing

## 🐛 Troubleshooting

### "Field required [type=missing]" Error

**Fixed!** The database migration has been completed.

If you still see this error:
```bash
python migrate_db.py
```

### Can't Access Protected Bot

- Make sure you're entering the correct password
- Password is case-sensitive
- Try closing and reopening the browser

### Delete Button Not Working

- Check browser console for errors
- Refresh the page
- Make sure you're on the Configuration tab

## 📚 Documentation

- **[FEATURE_GUIDE.md](markdown_files/FEATURE_GUIDE.md)** - Complete user guide
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Detailed migration steps
- **[NEW_FEATURES_PLAN.md](markdown_files/NEW_FEATURES_PLAN.md)** - Technical details

## ✅ Verification Checklist

After starting the app, verify:

- [ ] Existing bots still work
- [ ] Can create new bot without password (public)
- [ ] Can create new bot with password (protected)
- [ ] Lock icon shows for protected bots
- [ ] Password prompt appears when selecting protected bot
- [ ] Can delete a bot
- [ ] All bot data is removed after deletion

## 🎊 You're All Set!

The features are ready to use. Start the application and try them out!

```bash
python main_api.py
```

Then open: **http://localhost:8000**

Enjoy your new features! 🚀