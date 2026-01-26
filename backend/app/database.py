"""
ApexAurum Cloud - Database Connection

Async SQLAlchemy setup with PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

# Lazy initialization to avoid import-time database connection
_engine = None
_async_session = None


def get_engine():
    """Get or create database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.async_database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    """Get or create session factory (lazy initialization)."""
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables and run migrations)."""
    engine = get_engine()
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

        # Run migrations for new columns (safe to run multiple times)
        # v23-multiverse: Add branching columns to conversations table
        # v25-vault: Add folders and files tables
        migrations = [
            # ═══════════════════════════════════════════════════════════════════════
            # THE VAULT - v25: User file storage system
            # ═══════════════════════════════════════════════════════════════════════
            """
            CREATE TABLE IF NOT EXISTS folders (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                color VARCHAR(20),
                icon VARCHAR(50),
                is_archived BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_folder_user_parent ON folders(user_id, parent_id);
            """,
            """
            CREATE TABLE IF NOT EXISTS files (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                folder_id UUID REFERENCES folders(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                original_filename VARCHAR(500) NOT NULL,
                mime_type VARCHAR(100),
                file_type VARCHAR(50) NOT NULL,
                size_bytes INTEGER NOT NULL,
                storage_path VARCHAR(500) NOT NULL,
                checksum VARCHAR(64),
                description TEXT,
                tags TEXT[] DEFAULT '{}',
                status VARCHAR(20) DEFAULT 'ready',
                error TEXT,
                is_archived BOOLEAN DEFAULT FALSE,
                favorite BOOLEAN DEFAULT FALSE,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_file_user_folder ON files(user_id, folder_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_file_user_favorite ON files(user_id, favorite);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_file_user_type ON files(user_id, file_type);
            """,
            # ═══════════════════════════════════════════════════════════════════════
            # v23-multiverse: Conversation branching
            # ═══════════════════════════════════════════════════════════════════════
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'conversations' AND column_name = 'parent_id')
                THEN
                    ALTER TABLE conversations ADD COLUMN parent_id UUID REFERENCES conversations(id) ON DELETE SET NULL;
                    CREATE INDEX IF NOT EXISTS ix_conversations_parent_id ON conversations(parent_id);
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'conversations' AND column_name = 'branch_point_message_id')
                THEN
                    ALTER TABLE conversations ADD COLUMN branch_point_message_id UUID;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'conversations' AND column_name = 'branch_label')
                THEN
                    ALTER TABLE conversations ADD COLUMN branch_label VARCHAR(100);
                END IF;
            END $$;
            """,
            # ═══════════════════════════════════════════════════════════════════════
            # TIER 8: VECTOR SEARCH - The Remembering Deep
            # Semantic memory using pgvector extension
            # Note: All vector migrations wrapped in exception handlers for graceful fallback
            # ═══════════════════════════════════════════════════════════════════════
            """
            DO $$
            BEGIN
                CREATE EXTENSION IF NOT EXISTS vector;
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'pgvector extension not available, vector search disabled';
            END $$;
            """,
            """
            DO $$
            BEGIN
                CREATE TABLE IF NOT EXISTS user_vectors (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    collection VARCHAR(100) DEFAULT 'default',
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    embedding vector(1536),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            EXCEPTION WHEN OTHERS THEN
                RAISE NOTICE 'user_vectors table creation failed (pgvector may not be available)';
            END $$;
            """,
            """
            DO $$
            BEGIN
                CREATE INDEX IF NOT EXISTS idx_vectors_user ON user_vectors(user_id);
                CREATE INDEX IF NOT EXISTS idx_vectors_collection ON user_vectors(user_id, collection);
            EXCEPTION WHEN OTHERS THEN
                NULL;
            END $$;
            """,
            # ═══════════════════════════════════════════════════════════════════════
            # TIER 11: NEO-CORTEX - Unified Memory System
            # Memory layers, visibility realms, attention tracking
            # ═══════════════════════════════════════════════════════════════════════
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'layer') THEN
                    ALTER TABLE user_vectors ADD COLUMN layer VARCHAR(20) DEFAULT 'working' NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'visibility') THEN
                    ALTER TABLE user_vectors ADD COLUMN visibility VARCHAR(20) DEFAULT 'private' NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'agent_id') THEN
                    ALTER TABLE user_vectors ADD COLUMN agent_id VARCHAR(50);
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'message_type') THEN
                    ALTER TABLE user_vectors ADD COLUMN message_type VARCHAR(50) DEFAULT 'observation' NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'attention_weight') THEN
                    ALTER TABLE user_vectors ADD COLUMN attention_weight FLOAT DEFAULT 1.0 NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'access_count') THEN
                    ALTER TABLE user_vectors ADD COLUMN access_count INTEGER DEFAULT 0 NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'last_accessed_at') THEN
                    ALTER TABLE user_vectors ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'responding_to') THEN
                    ALTER TABLE user_vectors ADD COLUMN responding_to JSONB DEFAULT '[]'::jsonb NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'conversation_thread') THEN
                    ALTER TABLE user_vectors ADD COLUMN conversation_thread VARCHAR(100);
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'related_agents') THEN
                    ALTER TABLE user_vectors ADD COLUMN related_agents JSONB DEFAULT '[]'::jsonb NOT NULL;
                END IF;
            END $$;
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name = 'user_vectors' AND column_name = 'tags') THEN
                    ALTER TABLE user_vectors ADD COLUMN tags JSONB DEFAULT '[]'::jsonb NOT NULL;
                END IF;
            END $$;
            """,
            # Neo-Cortex indexes
            """
            CREATE INDEX IF NOT EXISTS idx_vectors_layer ON user_vectors(layer);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_vectors_visibility ON user_vectors(visibility);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_vectors_agent ON user_vectors(agent_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_vectors_user_visibility ON user_vectors(user_id, visibility);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_vectors_user_layer ON user_vectors(user_id, layer);
            """,
        ]

        from sqlalchemy import text
        for migration in migrations:
            await conn.execute(text(migration))
        print("Database migrations complete")


async def close_db():
    """Close database connections."""
    engine = get_engine()
    await engine.dispose()


# Convenience alias for tools - returns the session factory
def async_session():
    """Get async session factory. Usage: async with async_session() as db: ..."""
    return get_session_factory()()
