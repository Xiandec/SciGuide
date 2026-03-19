-- Initial relational schema for SciGuide.
-- PostgreSQL stores application metadata and access model.
-- Refresh tokens are expected to live in Redis with TTL.
-- Semantic search vectors and concept graph stay in Qdrant and Neo4j.

CREATE EXTENSION IF NOT EXISTS pgcrypto;


CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_email_not_blank_chk CHECK (btrim(email) <> ''),
    CONSTRAINT users_display_name_not_blank_chk CHECK (
        btrim(display_name) <> ''
    )
);

CREATE UNIQUE INDEX uq_users_email_lower
    ON users (lower(email));


CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id UUID NOT NULL REFERENCES users (id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL,
    access_mode VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT workspaces_name_not_blank_chk CHECK (btrim(name) <> ''),
    CONSTRAINT workspaces_type_chk CHECK (type IN ('private', 'shared')),
    CONSTRAINT workspaces_access_mode_chk CHECK (
        access_mode IN ('owner_only', 'by_membership', 'global')
    ),
    CONSTRAINT workspaces_type_access_mode_chk CHECK (
        (type = 'private' AND access_mode = 'owner_only')
        OR
        (type = 'shared' AND access_mode IN ('by_membership', 'global'))
    )
);

CREATE INDEX idx_workspaces_owner_user_id
    ON workspaces (owner_user_id);

CREATE INDEX idx_workspaces_type_created_at
    ON workspaces (type, created_at DESC);


CREATE TABLE workspace_members (
    workspace_id UUID NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT workspace_members_role_chk CHECK (role IN ('admin', 'user'))
);

CREATE INDEX idx_workspace_members_user_id
    ON workspace_members (user_id);


CREATE TABLE workspace_prompts (
    workspace_id UUID PRIMARY KEY REFERENCES workspaces (id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users (id),
    CONSTRAINT workspace_prompts_content_not_blank_chk CHECK (
        btrim(content) <> ''
    )
);


CREATE TABLE workspace_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    storage_key TEXT NOT NULL,
    content_type VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
    processing_stage VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    processing_error TEXT,
    uploaded_by UUID NOT NULL REFERENCES users (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT workspace_documents_filename_not_blank_chk CHECK (
        btrim(filename) <> ''
    ),
    CONSTRAINT workspace_documents_content_type_not_blank_chk CHECK (
        btrim(content_type) <> ''
    ),
    CONSTRAINT workspace_documents_size_bytes_chk CHECK (size_bytes >= 0),
    CONSTRAINT workspace_documents_status_chk CHECK (
        status IN ('uploaded', 'processing', 'processed', 'failed')
    ),
    CONSTRAINT workspace_documents_stage_chk CHECK (
        processing_stage IN (
            'uploaded',
            'text_extraction',
            'chunking',
            'embedding',
            'graph_update',
            'completed'
        )
    ),
    CONSTRAINT workspace_documents_status_stage_chk CHECK (
        (status = 'uploaded' AND processing_stage = 'uploaded')
        OR
        (
            status = 'processing'
            AND processing_stage IN (
                'text_extraction',
                'chunking',
                'embedding',
                'graph_update'
            )
        )
        OR
        (status = 'processed' AND processing_stage = 'completed')
        OR
        (status = 'failed')
    ),
    CONSTRAINT workspace_documents_failed_error_chk CHECK (
        status <> 'failed' OR processing_error IS NOT NULL
    ),
    CONSTRAINT uq_workspace_documents_storage_key UNIQUE (storage_key)
);

CREATE INDEX idx_workspace_documents_workspace_created_at
    ON workspace_documents (workspace_id, created_at DESC);

CREATE INDEX idx_workspace_documents_workspace_status
    ON workspace_documents (workspace_id, status);


CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id) ON DELETE CASCADE,
    owner_user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ,
    CONSTRAINT chats_title_not_blank_chk CHECK (btrim(title) <> ''),
    CONSTRAINT chats_last_message_at_chk CHECK (
        last_message_at IS NULL OR last_message_at >= created_at
    )
);

CREATE INDEX idx_chats_owner_workspace_updated_at
    ON chats (owner_user_id, workspace_id, updated_at DESC);

CREATE INDEX idx_chats_workspace_id
    ON chats (workspace_id);


CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats (id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT messages_role_chk CHECK (
        role IN ('user', 'assistant', 'system')
    ),
    CONSTRAINT messages_status_chk CHECK (
        status IN ('pending', 'completed', 'failed')
    ),
    CONSTRAINT messages_failed_error_chk CHECK (
        status <> 'failed' OR error_message IS NOT NULL
    )
);

CREATE INDEX idx_messages_chat_created_at
    ON messages (chat_id, created_at, id);


CREATE TABLE message_context_documents (
    message_id UUID NOT NULL REFERENCES messages (id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES workspace_documents (id)
        ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    PRIMARY KEY (message_id, document_id),
    CONSTRAINT message_context_documents_rank_chk CHECK (rank >= 1),
    CONSTRAINT uq_message_context_documents_rank UNIQUE (message_id, rank)
);

CREATE INDEX idx_message_context_documents_document_id
    ON message_context_documents (document_id);


CREATE OR REPLACE FUNCTION bootstrap_workspace_relations()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO workspace_members (
        workspace_id,
        user_id,
        role
    )
    VALUES (
        NEW.id,
        NEW.owner_user_id,
        'admin'
    )
    ON CONFLICT (workspace_id, user_id) DO NOTHING;

    INSERT INTO workspace_prompts (
        workspace_id,
        content,
        updated_by
    )
    VALUES (
        NEW.id,
        'You are a scientific assistant. Answer only within the current workspace context.',
        NEW.owner_user_id
    )
    ON CONFLICT (workspace_id) DO NOTHING;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_workspaces_set_updated_at
BEFORE UPDATE ON workspaces
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_workspaces_bootstrap_relations
AFTER INSERT ON workspaces
FOR EACH ROW
EXECUTE FUNCTION bootstrap_workspace_relations();

CREATE TRIGGER trg_workspace_prompts_set_updated_at
BEFORE UPDATE ON workspace_prompts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_workspace_documents_set_updated_at
BEFORE UPDATE ON workspace_documents
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_chats_set_updated_at
BEFORE UPDATE ON chats
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
