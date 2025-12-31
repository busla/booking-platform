"""Contract tests for OpenAPI schema generation.

These tests validate that the generated OpenAPI schema:
1. Matches the contract schema (openapi-output.schema.json)
2. Contains all required AWS API Gateway extensions
3. Properly classifies public vs protected routes
"""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

# Test configuration - matches Terraform inputs
TEST_LAMBDA_ARN = "arn:aws:lambda:eu-west-1:123456789012:function:booking-api"
TEST_USER_POOL_ID = "eu-west-1_TestPool123"
TEST_CLIENT_ID = "test-client-id-12345"
TEST_CORS_ORIGINS = ["*"]


@pytest.fixture
def openapi_schema() -> dict:
    """Load the OpenAPI output schema for validation."""
    # Path is relative to repo root - tests run from backend/ directory
    # Use Path(__file__) to get absolute path
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent.parent.parent  # backend/tests/contract -> backend -> repo root
    schema_path = repo_root / "specs/006-backend-workspace-openapi/contracts/openapi-output.schema.json"
    return json.loads(schema_path.read_text())


@pytest.fixture
def generated_openapi() -> dict:
    """Generate OpenAPI spec with test configuration."""
    from api.scripts.generate_openapi import generate_openapi

    return generate_openapi(
        lambda_arn=TEST_LAMBDA_ARN,
        cognito_user_pool_id=TEST_USER_POOL_ID,
        cognito_client_id=TEST_CLIENT_ID,
        cors_allow_origins=TEST_CORS_ORIGINS,
    )


class TestOpenAPISchemaContract:
    """Test suite for OpenAPI schema contract compliance."""

    def test_generated_openapi_matches_contract_schema(
        self, generated_openapi: dict, openapi_schema: dict
    ) -> None:
        """Generated OpenAPI must match the contract schema."""
        # Should not raise ValidationError
        validate(instance=generated_openapi, schema=openapi_schema)

    def test_openapi_version_is_3_0_x(self, generated_openapi: dict) -> None:
        """OpenAPI version must be 3.0.x for API Gateway compatibility."""
        version = generated_openapi["openapi"]
        assert version.startswith("3.0."), f"Expected 3.0.x, got {version}"

    def test_has_info_section(self, generated_openapi: dict) -> None:
        """OpenAPI must have info section with title and version."""
        info = generated_openapi["info"]
        assert "title" in info
        assert "version" in info

    def test_has_cors_configuration(self, generated_openapi: dict) -> None:
        """OpenAPI must have x-amazon-apigateway-cors at root level."""
        cors = generated_openapi.get("x-amazon-apigateway-cors")
        assert cors is not None, "Missing x-amazon-apigateway-cors"
        assert "allowOrigins" in cors
        assert "allowMethods" in cors
        assert "allowHeaders" in cors


class TestAWSIntegrations:
    """Test suite for AWS API Gateway integration configuration."""

    def test_all_operations_have_lambda_integration(
        self, generated_openapi: dict
    ) -> None:
        """Every operation must have x-amazon-apigateway-integration."""
        for path, path_item in generated_openapi["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                integration = operation.get("x-amazon-apigateway-integration")
                assert integration is not None, (
                    f"Missing integration for {method.upper()} {path}"
                )

    def test_integration_type_is_aws_proxy(self, generated_openapi: dict) -> None:
        """All integrations must use AWS_PROXY type."""
        for path, path_item in generated_openapi["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                integration = path_item[method].get("x-amazon-apigateway-integration", {})
                assert integration.get("type") == "AWS_PROXY", (
                    f"Expected AWS_PROXY for {method.upper()} {path}"
                )

    def test_integration_uri_contains_lambda_arn(
        self, generated_openapi: dict
    ) -> None:
        """Integration URI must contain the Lambda ARN."""
        for path, path_item in generated_openapi["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                integration = path_item[method].get("x-amazon-apigateway-integration", {})
                uri = integration.get("uri", "")
                assert TEST_LAMBDA_ARN in uri, (
                    f"Lambda ARN not found in URI for {method.upper()} {path}"
                )

    def test_payload_format_version_is_2_0(self, generated_openapi: dict) -> None:
        """All integrations must use payloadFormatVersion 2.0."""
        for path, path_item in generated_openapi["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                integration = path_item[method].get("x-amazon-apigateway-integration", {})
                assert integration.get("payloadFormatVersion") == "2.0", (
                    f"Expected payloadFormatVersion 2.0 for {method.upper()} {path}"
                )


class TestJWTAuthorizer:
    """Test suite for JWT authorizer configuration."""

    def test_has_cognito_jwt_security_scheme(self, generated_openapi: dict) -> None:
        """Must have cognito-jwt security scheme in components."""
        schemes = generated_openapi.get("components", {}).get("securitySchemes", {})
        assert "cognito-jwt" in schemes, "Missing cognito-jwt security scheme"

    def test_security_scheme_type_is_oauth2(self, generated_openapi: dict) -> None:
        """Security scheme type must be oauth2."""
        scheme = generated_openapi["components"]["securitySchemes"]["cognito-jwt"]
        assert scheme["type"] == "oauth2"

    def test_has_jwt_authorizer_extension(self, generated_openapi: dict) -> None:
        """Must have x-amazon-apigateway-authorizer with JWT type."""
        scheme = generated_openapi["components"]["securitySchemes"]["cognito-jwt"]
        authorizer = scheme.get("x-amazon-apigateway-authorizer")
        assert authorizer is not None, "Missing x-amazon-apigateway-authorizer"
        assert authorizer["type"] == "jwt"

    def test_jwt_issuer_matches_cognito_url(self, generated_openapi: dict) -> None:
        """JWT issuer must be Cognito User Pool URL."""
        scheme = generated_openapi["components"]["securitySchemes"]["cognito-jwt"]
        authorizer = scheme["x-amazon-apigateway-authorizer"]
        jwt_config = authorizer["jwtConfiguration"]

        expected_issuer = (
            f"https://cognito-idp.eu-west-1.amazonaws.com/{TEST_USER_POOL_ID}"
        )
        assert jwt_config["issuer"] == expected_issuer

    def test_jwt_audience_contains_client_id(self, generated_openapi: dict) -> None:
        """JWT audience must contain the Cognito client ID."""
        scheme = generated_openapi["components"]["securitySchemes"]["cognito-jwt"]
        authorizer = scheme["x-amazon-apigateway-authorizer"]
        jwt_config = authorizer["jwtConfiguration"]

        assert TEST_CLIENT_ID in jwt_config["audience"]


class TestRouteSecurityClassification:
    """Test suite for route security classification.

    These tests verify that routes are correctly marked as public or protected
    based on the presence of require_auth dependency.
    """

    def test_all_operations_have_security_field(self, generated_openapi: dict) -> None:
        """Every operation must have explicit security field."""
        for path, path_item in generated_openapi["paths"].items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                assert "security" in operation, (
                    f"Missing security field for {method.upper()} {path}"
                )

    def test_public_routes_have_empty_security(self, generated_openapi: dict) -> None:
        """Public routes must have security: []."""
        # Currently all routes in this API are public (session status, health)
        # Note: /api prefix is included because routers are mounted with prefix="/api"
        # OAuth2 callback is handled by frontend SDK, not backend API
        public_routes = [
            ("get", "/api/ping"),
            ("get", "/api/health"),
            ("get", "/api/auth/session/{session_id}"),
            ("post", "/api/auth/refresh"),
        ]

        for method, path in public_routes:
            path_item = generated_openapi["paths"].get(path, {})
            if method not in path_item:
                continue  # Route may not exist

            operation = path_item[method]
            assert operation.get("security") == [], (
                f"Expected empty security for public route {method.upper()} {path}"
            )


class TestCORSConfiguration:
    """Test suite for CORS configuration."""

    def test_cors_allow_origins_matches_config(self, generated_openapi: dict) -> None:
        """CORS allowOrigins must match configuration."""
        cors = generated_openapi["x-amazon-apigateway-cors"]
        assert cors["allowOrigins"] == TEST_CORS_ORIGINS

    def test_cors_includes_standard_methods(self, generated_openapi: dict) -> None:
        """CORS must allow standard HTTP methods."""
        cors = generated_openapi["x-amazon-apigateway-cors"]
        required_methods = {"GET", "POST", "PUT", "DELETE", "OPTIONS"}
        assert required_methods.issubset(set(cors["allowMethods"]))

    def test_cors_includes_authorization_header(self, generated_openapi: dict) -> None:
        """CORS must allow Authorization header for JWT."""
        cors = generated_openapi["x-amazon-apigateway-cors"]
        assert "Authorization" in cors["allowHeaders"]

    def test_cors_allows_credentials_for_specific_origins(
        self, generated_openapi: dict
    ) -> None:
        """CORS allowCredentials depends on origin configuration.

        AWS API Gateway security constraint: allowCredentials cannot be true
        when allowOrigins is ["*"]. This test uses wildcard origins, so
        allowCredentials must be False.
        """
        cors = generated_openapi["x-amazon-apigateway-cors"]
        # With TEST_CORS_ORIGINS = ["*"], credentials must be False
        assert cors.get("allowCredentials") is False
