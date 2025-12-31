"""AWS API Gateway OpenAPI extension types.

This module defines Pydantic models for AWS-specific OpenAPI extensions used
when generating the API Gateway configuration from FastAPI routes.
"""

from typing import Literal

from pydantic import BaseModel, Field


class AWSIntegration(BaseModel):
    """AWS API Gateway Lambda proxy integration.

    Represents x-amazon-apigateway-integration for HTTP API.
    All Lambda integrations use AWS_PROXY with POST method.
    """

    type: Literal["AWS_PROXY"] = "AWS_PROXY"
    httpMethod: Literal["POST"] = "POST"
    uri: str = Field(
        ...,
        description=(
            "Lambda invocation URI: "
            "arn:aws:apigateway:{region}:lambda:path/2015-03-31/functions/{arn}/invocations"
        ),
    )
    payloadFormatVersion: Literal["2.0"] = "2.0"

    @classmethod
    def from_lambda_arn(cls, lambda_arn: str) -> "AWSIntegration":
        """Create integration from Lambda ARN.

        Args:
            lambda_arn: Full Lambda ARN
                (e.g., arn:aws:lambda:eu-west-1:123456789:function:my-func)

        Returns:
            AWSIntegration with properly formatted URI.

        Raises:
            ValueError: If ARN format is invalid.
        """
        # Parse region from ARN: arn:aws:lambda:{region}:{account}:function:{name}
        parts = lambda_arn.split(":")
        if len(parts) < 4 or parts[0] != "arn" or parts[2] != "lambda":
            raise ValueError(f"Invalid Lambda ARN format: {lambda_arn}")

        region = parts[3]
        uri = (
            f"arn:aws:apigateway:{region}:lambda:path/2015-03-31"
            f"/functions/{lambda_arn}/invocations"
        )

        return cls(uri=uri)


class JWTConfiguration(BaseModel):
    """JWT authorizer configuration for Cognito.

    Used in x-amazon-apigateway-authorizer.jwtConfiguration.
    """

    issuer: str = Field(
        ...,
        description=(
            "Cognito issuer URL: "
            "https://cognito-idp.{region}.amazonaws.com/{userPoolId}"
        ),
    )
    audience: list[str] = Field(
        ..., description="List of allowed client IDs (typically one app client)"
    )

    @classmethod
    def from_cognito(cls, user_pool_id: str, client_id: str) -> "JWTConfiguration":
        """Create JWT config from Cognito identifiers.

        Args:
            user_pool_id: Cognito User Pool ID (e.g., eu-west-1_ABC123xyz)
            client_id: Cognito App Client ID

        Returns:
            JWTConfiguration with properly formatted issuer URL.
        """
        # Extract region from user pool ID (format: {region}_{id})
        region = user_pool_id.split("_")[0]
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

        return cls(issuer=issuer, audience=[client_id])


class AWSAuthorizer(BaseModel):
    """AWS API Gateway JWT authorizer.

    Represents x-amazon-apigateway-authorizer for HTTP API JWT auth.
    """

    type: Literal["jwt"] = "jwt"
    identitySource: str = "$request.header.Authorization"
    jwtConfiguration: JWTConfiguration


class CORSConfiguration(BaseModel):
    """AWS API Gateway CORS configuration.

    Represents x-amazon-apigateway-cors at OpenAPI root level.
    """

    allowOrigins: list[str] = Field(
        default=["*"],
        description="Allowed origins (use specific origins in production)",
    )
    allowMethods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods",
    )
    allowHeaders: list[str] = Field(
        default=["Content-Type", "Authorization", "X-Requested-With", "X-Amz-Date"],
        description="Allowed request headers",
    )
    exposeHeaders: list[str] = Field(
        default=["X-Request-Id"], description="Headers exposed to browser"
    )
    maxAge: int = Field(
        default=86400, description="Preflight cache duration in seconds"
    )
    allowCredentials: bool = Field(
        default=True, description="Whether credentials are supported"
    )
