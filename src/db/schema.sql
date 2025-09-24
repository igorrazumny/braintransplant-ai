-- File: braintransplant-ai/src/db/schema.sql
-- Final schema for user-aware, persistent chat history.

-- Stores a complete record of every user interaction for analytics and history.
CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,

    -- The user's account ID (e.g., 'user.name@roche.com'), passed from the parent application.
    -- This is the key for retrieving a user's continuous conversation history.
    -- It can be NULL if the user is not authenticated.
    user_id TEXT,

    -- A unique ID for a single conversation session (useful for anonymous users).
    session_id TEXT NOT NULL,

    -- The core conversation data
    user_query TEXT NOT NULL,
    retrieved_context TEXT,
    model_response TEXT NOT NULL,

    -- Timestamp for ordering the conversation
    ts TIMESTAMPTZ DEFAULT NOW()
);

-- Essential indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history (session_id);
