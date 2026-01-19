"""
Agent Communication Layer
Client for connecting agents to the central server
"""

from .client import AgentClient
from .daemon import AgentDaemon

__all__ = [
    "AgentClient",
    "AgentDaemon",
]
