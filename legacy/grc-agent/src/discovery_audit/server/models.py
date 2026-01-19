"""
Server Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent connection status"""
    ONLINE = "online"
    OFFLINE = "offline"
    SCANNING = "scanning"
    ERROR = "error"


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8443
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    api_key: Optional[str] = None
    database_url: str = "sqlite:///./grc_audit.db"
    jwt_secret: str = "change-me-in-production"
    cors_origins: list[str] = field(default_factory=lambda: ["*"])


class AgentRegistration(BaseModel):
    """Agent registration request"""
    hostname: str
    ip_address: str
    os_type: str
    os_version: str
    agent_version: str
    capabilities: list[str] = Field(default_factory=list)


class AgentInfo(BaseModel):
    """Agent information stored on server"""
    id: str
    hostname: str
    ip_address: str
    os_type: str
    os_version: str
    agent_version: str
    capabilities: list[str] = Field(default_factory=list)
    status: AgentStatus = AgentStatus.OFFLINE
    last_seen: datetime = Field(default_factory=datetime.now)
    registered_at: datetime = Field(default_factory=datetime.now)
    current_task: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class ScanTask(BaseModel):
    """Scan task to be executed by an agent"""
    id: str
    agent_id: str
    task_type: str  # "full", "quick", "network", "system", "ad", "compliance"
    targets: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed


class ScanResult(BaseModel):
    """Scan result submitted by an agent"""
    task_id: str
    agent_id: str
    result_data: dict[str, Any]
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    score: float
    grade: str
    completed_at: datetime = Field(default_factory=datetime.now)
