"""AgentCore Runtime entrypoint for Quesada Apartment Booking Agent.

This module provides the HTTP interface required by AWS Bedrock AgentCore Runtime:
- POST /invocations - Agent invocation endpoint (streaming via SSE)
- GET /ping - Health check endpoint

Implements Vercel AI SDK v6 UI Message Stream Protocol for frontend compatibility.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent import create_booking_agent

# Initialize AgentCore app and agent
app = BedrockAgentCoreApp()
agent = create_booking_agent()


def _sse_event(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap data in SSE-compatible format for AgentCore streaming.

    AgentCore's BedrockAgentCoreApp automatically converts yielded dicts
    to SSE format: `data: {json}\n\n`
    """
    return data


@app.entrypoint
async def invoke(payload: dict[str, Any]) -> AsyncGenerator[dict[str, Any]]:
    """Handle agent invocation requests with AI SDK v6 streaming.

    Args:
        payload: Request payload containing:
            - prompt: User message (required)
            - session_id: Optional session identifier

    Yields:
        AI SDK v6 UI Message Stream Protocol events:
        - {"type": "start", "messageId": "..."}
        - {"type": "text-start", "id": "..."}
        - {"type": "text-delta", "id": "...", "delta": "..."}
        - {"type": "text-end", "id": "..."}
        - {"type": "finish", "finishReason": "stop"}
    """
    prompt = payload.get("prompt", "")
    message_id = f"msg_{uuid.uuid4().hex[:16]}"
    text_part_id = f"text_{uuid.uuid4().hex[:16]}"

    if not prompt:
        # Emit error as AI SDK v6 stream
        yield _sse_event({"type": "start", "messageId": message_id})
        yield _sse_event({"type": "text-start", "id": text_part_id})
        yield _sse_event({
            "type": "text-delta",
            "id": text_part_id,
            "delta": "Error: No prompt provided. Please include a 'prompt' key in the request.",
        })
        yield _sse_event({"type": "text-end", "id": text_part_id})
        yield _sse_event({"type": "finish", "finishReason": "error"})
        return

    # Emit start events
    yield _sse_event({"type": "start", "messageId": message_id})
    yield _sse_event({"type": "text-start", "id": text_part_id})

    try:
        # Stream from the Strands agent using async streaming
        async for event in agent.stream_async(prompt):
            # Handle different event types from Strands
            if isinstance(event, dict):
                event_type = event.get("type", "")

                # Text content events from Bedrock/Anthropic
                if event_type == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        text = delta.get("text", "")
                        if text:
                            yield _sse_event({
                                "type": "text-delta",
                                "id": text_part_id,
                                "delta": text,
                            })

                # Handle direct text in data field (Strands format)
                elif "data" in event and isinstance(event.get("data"), str):
                    yield _sse_event({
                        "type": "text-delta",
                        "id": text_part_id,
                        "delta": event["data"],
                    })

            # Handle string events (raw text chunks)
            elif isinstance(event, str) and event:
                yield _sse_event({
                    "type": "text-delta",
                    "id": text_part_id,
                    "delta": event,
                })

    except Exception as e:
        # Emit error as text delta
        yield _sse_event({
            "type": "text-delta",
            "id": text_part_id,
            "delta": f"\n\nError: {str(e)}",
        })

    # Emit end events
    yield _sse_event({"type": "text-end", "id": text_part_id})
    yield _sse_event({"type": "finish", "finishReason": "stop"})


if __name__ == "__main__":
    app.run()
