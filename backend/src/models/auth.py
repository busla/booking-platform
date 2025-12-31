"""Authentication models for AgentCore Identity OAuth2.

This module defines models for:
- WorkloadToken: Agent workload access token (in-memory only)
- OAuth2CompletionResult: Result of completing OAuth2 3LO flow
"""

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field


class WorkloadToken(BaseModel):
    """Agent workload access token from AgentCore Identity.

    This is an in-memory model - not persisted.
    Used for agent-to-AgentCore API authentication.
    Tokens are cached and auto-refreshed by the SDK.
    """

    model_config = ConfigDict(strict=True)

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_at: datetime = Field(..., description="Token expiration time (UTC)")
    workload_name: str | None = Field(default=None, description="Workload identity name")
    user_id: str | None = Field(default=None, description="User ID if user-delegated")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 30-second buffer for network latency)."""
        return datetime.now(timezone.utc) >= (self.expires_at - timedelta(seconds=30))


class OAuth2CompletionResult(BaseModel):
    """Result of completing an OAuth2 3LO flow via CompleteResourceTokenAuth.

    Used to communicate success/failure and any errors from the OAuth2 callback
    processing to the caller.
    """

    model_config = ConfigDict(strict=True)

    success: bool = Field(..., description="Whether OAuth2 completion succeeded")
    error_code: str | None = Field(default=None, description="Error code if failed")
    message: str | None = Field(default=None, description="Human-readable message")
