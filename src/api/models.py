"""
Pydantic models for the React frontend API.
These define the contract between backend and frontend.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Shared Types
# =============================================================================

class Message(BaseModel):
    """A single message in a conversation."""
    role: Literal["user", "assistant"]
    content: str
    speaker: Optional[str] = None  # Character name for assistant messages
    emoji: Optional[str] = None
    timestamp: Optional[str] = None


class CharacterInfo(BaseModel):
    """Basic character information."""
    name: str
    emoji: str
    color: str


# =============================================================================
# Chat API
# =============================================================================

class ChatRequest(BaseModel):
    """Request body for POST /api/chat"""
    message: str = Field(..., min_length=1)
    history: list[Message] = Field(default_factory=list)
    api_key: Optional[str] = Field(None, alias="apiKey")
    mentions: Optional[list[str]] = None  # Pre-parsed @mentions from client


class ChatResponseMetadata(BaseModel):
    """Metadata returned with chat responses."""
    responding_characters: list[str]
    timestamp: str
    duration_ms: Optional[float] = None


class ChatResponse(BaseModel):
    """Response body for POST /api/chat"""
    history: list[Message]
    metadata: ChatResponseMetadata


# WebSocket message types
class WSChatMessage(BaseModel):
    """WebSocket message for streaming chat."""
    type: Literal["start", "chunk", "done", "error"]
    character: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Deliberation API
# =============================================================================

class DeliberationRequest(BaseModel):
    """Request body for POST /api/deliberate"""
    question: str = Field(..., min_length=1)
    rounds: int = Field(1, ge=1, le=3)
    summariser: str = "Moderator"
    api_key: Optional[str] = Field(None, alias="apiKey")


class PhaseEntry(BaseModel):
    """A single entry in a deliberation phase."""
    cycle: int
    phase: Literal["thesis", "antithesis", "synthesis"]
    character: str
    content: str
    timestamp: Optional[str] = None


class CycleSummary(BaseModel):
    """Summary of a deliberation cycle."""
    cycle: int
    summary: str


class FinalSummary(BaseModel):
    """Final summary from the summariser."""
    by: str
    content: str


class DeliberationMetadata(BaseModel):
    """Metadata for deliberation results."""
    character_order: list[str]
    seed: int
    duration_ms: Optional[float] = None


class DeliberationResponse(BaseModel):
    """Response body for POST /api/deliberate"""
    question: str
    rounds: int
    phases: dict[str, list[PhaseEntry]]  # {"thesis": [...], "antithesis": [...], "synthesis": [...]}
    cycle_summaries: list[CycleSummary]
    final_summary: FinalSummary
    metadata: DeliberationMetadata


# WebSocket message types for deliberation streaming
class WSDeliberationMessage(BaseModel):
    """WebSocket message for streaming deliberation."""
    type: Literal["phase_start", "character_start", "chunk", "character_done", "phase_done", "summary", "done", "error"]
    phase: Optional[str] = None
    cycle: Optional[int] = None
    character: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# System / Meta
# =============================================================================

class HealthResponse(BaseModel):
    """Response for GET /api/health"""
    status: Literal["ok", "degraded", "error"]
    gradio_available: bool
    timestamp: str


class CharactersResponse(BaseModel):
    """Response for GET /api/characters"""
    characters: list[CharacterInfo]
