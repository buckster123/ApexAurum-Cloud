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
        migrations = [
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
        ]

        from sqlalchemy import text
        for migration in migrations:
            await conn.execute(text(migration))
        print("Database migrations complete")


async def close_db():
    """Close database connections."""
    engine = get_engine()
    await engine.dispose()
