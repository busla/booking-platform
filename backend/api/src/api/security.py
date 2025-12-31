"""Security annotations for FastAPI routes.

This module provides marker-based security annotations for OpenAPI generation.
IMPORTANT: These do NOT perform actual JWT validation - API Gateway handles that.
They only serve to mark routes for the OpenAPI generation script.
"""

from enum import Enum
from typing import ClassVar

from fastapi import Request


class AuthScope(str, Enum):
    """OAuth2 scopes for JWT authorization.

    These map to Cognito user pool scopes.
    """

    OPENID = "openid"
    EMAIL = "email"
    PROFILE = "profile"
    # Add custom scopes as needed:
    # RESERVATIONS_WRITE = "reservations:write"
    # RESERVATIONS_READ = "reservations:read"


class SecurityRequirement:
    """Marker class for security annotations.

    This is NOT an actual authorizer - API Gateway handles JWT validation.
    This class marks routes for OpenAPI generation only.

    Usage:
        @app.post("/reservations", dependencies=[Depends(require_auth())])
        async def create_reservation(...):
            ...

    The dependency `require_auth` returns an instance of this class.
    """

    SCHEME_NAME: ClassVar[str] = "cognito-jwt"

    def __init__(self, scopes: list[AuthScope] | None = None):
        """Initialize security requirement.

        Args:
            scopes: Optional list of required OAuth2 scopes.
                    Empty list means authenticated but no specific scopes.
        """
        self.scopes = scopes or []


def require_auth(scopes: list[AuthScope] | None = None):
    """Create a security requirement dependency.

    This dependency does NOT perform JWT validation (API Gateway does).
    It serves as a marker for the OpenAPI generation script to add
    security requirements to the schema.

    Args:
        scopes: Optional list of required OAuth2 scopes.

    Returns:
        Dependency function that returns SecurityRequirement.

    Example:
        # Route requiring authentication (no specific scopes)
        @app.post("/reservations", dependencies=[Depends(require_auth())])

        # Route requiring specific scope
        @app.delete("/reservations/{id}",
                    dependencies=[Depends(require_auth([AuthScope.RESERVATIONS_WRITE]))])
    """

    def _require_auth(request: Request) -> SecurityRequirement:
        # In production, API Gateway has already validated the JWT
        # by the time this runs. This is just a marker.
        return SecurityRequirement(scopes=scopes)

    return _require_auth
