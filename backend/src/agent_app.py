"""AgentCore Runtime entrypoint for Quesada Apartment Booking Agent.

This module provides the HTTP interface required by AWS Bedrock AgentCore Runtime:
- POST /invocations - Agent invocation endpoint
- GET /ping - Health check endpoint
"""

from datetime import UTC, datetime
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent import create_booking_agent

# Initialize AgentCore app and agent
app = BedrockAgentCoreApp()
agent = create_booking_agent()


@app.entrypoint
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle agent invocation requests.

    Args:
        payload: Request payload containing:
            - prompt: User message (required)
            - session_id: Optional session identifier

    Returns:
        Response containing agent output
    """
    prompt = payload.get("prompt", "")

    if not prompt:
        return {
            "error": "No prompt provided. Please include a 'prompt' key in the request.",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    try:
        # Invoke the Strands agent
        result = agent(prompt)

        return {
            "message": result.message,
            "timestamp": datetime.now(UTC).isoformat(),
            "agent": "booking-agent",
        }

    except Exception as e:
        return {
            "error": f"Agent processing failed: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat(),
        }


if __name__ == "__main__":
    app.run()
