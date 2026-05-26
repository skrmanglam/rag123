#!/usr/bin/env python3
"""
Database migration script for adding password_hash column to bots table.
Run this before starting the application if you have an existing database.
"""

import sqlite3
import os
import sys

DB_PATH = "db/rag_builder.db"

def migrate_database():
    """Add password_hash column to bots table if it doesn't exist."""
    
    if not os.path.exists(DB_PATH):
        print(f"✅ Database not found at {DB_PATH}")
        print("   A new database will be created automatically on first run.")
        return True
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if password_hash column already exists
        cursor.execute("PRAGMA table_info(bots)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'password_hash' in columns:
            print("✅ Database already migrated (password_hash column exists)")
            conn.close()
            return True
        
        # Add password_hash column
        print("🔄 Adding password_hash column to bots table...")
        cursor.execute("ALTER TABLE bots ADD COLUMN password_hash TEXT")
        conn.commit()
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(bots)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'password_hash' in columns:
            print("✅ Migration successful! password_hash column added.")
            conn.close()
            return True
        else:
            print("❌ Migration failed! Column was not added.")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("RAG Chatbot - Database Migration")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    print()
    if success:
        print("✅ Migration complete! You can now start the application.")
        print()
        print("To start the application:")
        print("  python main_api.py")
        print("  or")
        print("  ./start_web.sh")
        sys.exit(0)
    else:
        print("❌ Migration failed! Please check the errors above.")
        print()
        print("Manual migration:")
        print(f"  sqlite3 {DB_PATH} \"ALTER TABLE bots ADD COLUMN password_hash TEXT;\"")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Made with Bob
