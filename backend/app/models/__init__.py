"""
ApexAurum Cloud - SQLAlchemy Models

Import order matters for SQLAlchemy relationship resolution.
Models referenced in relationships must be imported before the
models that reference them.
"""

# Import models that are referenced by others FIRST
from app.models.vector import UserVector
from app.models.file import File, Folder
from app.models.conversation import Conversation, Message
from app.models.agent import Agent
from app.models.village import VillageKnowledge
from app.models.memory import Memory
from app.models.music import MusicTask
from app.models.agent_memory import AgentMemory

# User references all of the above, so import LAST
from app.models.user import User

__all__ = [
    "User",
    "Conversation",
    "Message",
    "Agent",
    "VillageKnowledge",
    "Memory",
    "MusicTask",
    "AgentMemory",
    "File",
    "Folder",
    "UserVector",
]
