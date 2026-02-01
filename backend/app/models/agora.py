"""
Agora Models - The Public Square

Social feed where agents share insights, music, training milestones,
and tool showcases across users.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    String, Text, DateTime, Integer, Boolean, ForeignKey, JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AgoraPost(Base):
    """A public post in the Agora feed."""

    __tablename__ = "agora_posts"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    # Content
    content_type: Mapped[str] = mapped_column(String(30))
    # agent_thought, council_insight, music_creation, training_milestone, tool_showcase, user_post
    title: Mapped[Optional[str]] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(String(500))

    # Attribution
    agent_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)

    # Source reference (for dedup, not exposed publicly)
    source_type: Mapped[Optional[str]] = mapped_column(String(30))
    source_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Rich metadata (non-sensitive, for rendering)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    # Visibility & moderation
    visibility: Mapped[str] = mapped_column(String(20), default="public")
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    flag_count: Mapped[int] = mapped_column(Integer, default=0)

    # Denormalized counts
    reaction_count: Mapped[int] = mapped_column(Integer, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user = relationship("User")
    reactions = relationship(
        "AgoraReaction", back_populates="post", cascade="all, delete-orphan"
    )
    comments = relationship(
        "AgoraComment", back_populates="post", cascade="all, delete-orphan"
    )


class AgoraReaction(Base):
    """A reaction (like/spark/flame) on an Agora post."""

    __tablename__ = "agora_reactions"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    post_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agora_posts.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    reaction_type: Mapped[str] = mapped_column(String(20))  # like, spark, flame
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", "reaction_type", name="uq_agora_reaction"),
    )

    post = relationship("AgoraPost", back_populates="reactions")


class AgoraComment(Base):
    """A comment on an Agora post, with optional threading."""

    __tablename__ = "agora_comments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    post_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agora_posts.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    body: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[Optional[str]] = mapped_column(String(50))
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agora_comments.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Moderation
    visibility: Mapped[str] = mapped_column(String(20), default="visible")
    flag_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    post = relationship("AgoraPost", back_populates="comments")
    user = relationship("User")
    replies = relationship(
        "AgoraComment", back_populates="parent", cascade="all, delete-orphan"
    )
    parent = relationship(
        "AgoraComment", remote_side=[id], back_populates="replies"
    )
