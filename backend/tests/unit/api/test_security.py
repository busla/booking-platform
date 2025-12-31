"""Unit tests for security annotations.

These tests verify that the security annotation types and dependency factory
work correctly for OpenAPI generation purposes.
"""

from unittest.mock import MagicMock

import pytest

from api.security import AuthScope, SecurityRequirement, require_auth


class TestAuthScope:
    """Test suite for AuthScope enum."""

    def test_openid_scope_value(self) -> None:
        """OPENID scope has correct string value."""
        assert AuthScope.OPENID == "openid"
        assert AuthScope.OPENID.value == "openid"

    def test_email_scope_value(self) -> None:
        """EMAIL scope has correct string value."""
        assert AuthScope.EMAIL == "email"
        assert AuthScope.EMAIL.value == "email"

    def test_profile_scope_value(self) -> None:
        """PROFILE scope has correct string value."""
        assert AuthScope.PROFILE == "profile"
        assert AuthScope.PROFILE.value == "profile"

    def test_scopes_are_string_enum(self) -> None:
        """All scopes inherit from str for JSON serialization."""
        for scope in AuthScope:
            assert isinstance(scope, str)


class TestSecurityRequirement:
    """Test suite for SecurityRequirement marker class."""

    def test_default_has_empty_scopes(self) -> None:
        """SecurityRequirement defaults to empty scopes list."""
        req = SecurityRequirement()
        assert req.scopes == []

    def test_accepts_scope_list(self) -> None:
        """SecurityRequirement accepts list of scopes."""
        scopes = [AuthScope.OPENID, AuthScope.EMAIL]
        req = SecurityRequirement(scopes=scopes)
        assert req.scopes == scopes
        assert len(req.scopes) == 2

    def test_none_scopes_becomes_empty_list(self) -> None:
        """Passing None for scopes results in empty list."""
        req = SecurityRequirement(scopes=None)
        assert req.scopes == []

    def test_has_scheme_name_constant(self) -> None:
        """SecurityRequirement has SCHEME_NAME class variable."""
        assert SecurityRequirement.SCHEME_NAME == "cognito-jwt"

    def test_scheme_name_is_class_variable(self) -> None:
        """SCHEME_NAME is shared across all instances."""
        req1 = SecurityRequirement()
        req2 = SecurityRequirement(scopes=[AuthScope.PROFILE])
        assert req1.SCHEME_NAME == req2.SCHEME_NAME == "cognito-jwt"


class TestRequireAuth:
    """Test suite for require_auth dependency factory."""

    def test_returns_callable(self) -> None:
        """require_auth returns a callable dependency function."""
        dep = require_auth()
        assert callable(dep)

    def test_returns_callable_with_scopes(self) -> None:
        """require_auth with scopes returns callable dependency."""
        dep = require_auth(scopes=[AuthScope.OPENID])
        assert callable(dep)

    def test_dependency_returns_security_requirement(self) -> None:
        """Calling the dependency returns SecurityRequirement instance."""
        dep = require_auth()
        mock_request = MagicMock()

        result = dep(mock_request)

        assert isinstance(result, SecurityRequirement)

    def test_dependency_passes_scopes(self) -> None:
        """Dependency passes scopes to SecurityRequirement."""
        scopes = [AuthScope.EMAIL, AuthScope.PROFILE]
        dep = require_auth(scopes=scopes)
        mock_request = MagicMock()

        result = dep(mock_request)

        assert result.scopes == scopes

    def test_dependency_defaults_to_empty_scopes(self) -> None:
        """Dependency with no scopes creates SecurityRequirement with empty scopes."""
        dep = require_auth()
        mock_request = MagicMock()

        result = dep(mock_request)

        assert result.scopes == []

    def test_dependency_with_none_scopes(self) -> None:
        """Dependency with None scopes creates SecurityRequirement with empty scopes."""
        dep = require_auth(scopes=None)
        mock_request = MagicMock()

        result = dep(mock_request)

        assert result.scopes == []


class TestSecurityAnnotationIntegration:
    """Integration tests for security annotations with FastAPI."""

    def test_require_auth_can_be_used_as_dependency(self) -> None:
        """require_auth can be used in FastAPI Depends()."""
        from fastapi import Depends, FastAPI

        app = FastAPI()

        # This should not raise any errors
        @app.get("/protected")
        async def protected_route(_auth: SecurityRequirement = Depends(require_auth())):
            return {"status": "ok"}

        # Verify route was registered
        routes = [r for r in app.routes if hasattr(r, "path") and r.path == "/protected"]
        assert len(routes) == 1

    def test_require_auth_with_scopes_can_be_used_as_dependency(self) -> None:
        """require_auth with scopes can be used in FastAPI Depends()."""
        from fastapi import Depends, FastAPI

        app = FastAPI()

        @app.delete("/admin-only")
        async def admin_route(
            _auth: SecurityRequirement = Depends(
                require_auth(scopes=[AuthScope.OPENID, AuthScope.EMAIL])
            )
        ):
            return {"status": "deleted"}

        # Verify route was registered
        routes = [r for r in app.routes if hasattr(r, "path") and r.path == "/admin-only"]
        assert len(routes) == 1
