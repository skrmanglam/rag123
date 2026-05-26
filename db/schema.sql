-- Bot configuration table
CREATE TABLE IF NOT EXISTS bots (
    bot_id TEXT PRIMARY KEY,
    bot_name TEXT NOT NULL,
    role TEXT,
    tone TEXT,
    strictness TEXT,
    citation_required INTEGER DEFAULT 1,
    fallback_behavior TEXT,
    system_prompt TEXT,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document metadata table
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (bot_id) REFERENCES bots(bot_id) ON DELETE CASCADE
);

-- Chunk metadata table
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    page_number INTEGER,
    section_name TEXT,
    has_table INTEGER DEFAULT 0,
    chunk_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(bot_id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

-- FAQ entries table
CREATE TABLE IF NOT EXISTS faq_entries (
    faq_id TEXT PRIMARY KEY,
    bot_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_id) REFERENCES bots(bot_id) ON DELETE CASCADE,
    UNIQUE(bot_id, question_id)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_documents_bot_id ON documents(bot_id);
CREATE INDEX IF NOT EXISTS idx_chunks_bot_id ON chunks(bot_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_faq_bot_id ON faq_entries(bot_id);
CREATE INDEX IF NOT EXISTS idx_faq_question_id ON faq_entries(question_id);
