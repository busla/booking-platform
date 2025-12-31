"""AgentCore Runtime entrypoint for Quesada Apartment Booking Agent.

This module provides the HTTP interface required by AWS Bedrock AgentCore Runtime:
- POST /invocations - Agent invocation endpoint (streaming via SSE)
- GET /ping - Health check endpoint

Implements Vercel AI SDK v6 UI Message Stream Protocol for frontend compatibility.

Session Management:
- Uses Strands S3SessionManager for conversation persistence
- Each session_id from the frontend maps to a unique conversation history
- Uses stream_async for native async streaming (follows AgentCore samples pattern)

Authentication (Spec 005 - AgentCore Identity OAuth2):
- Reservation tools use @requires_access_token decorator
- When user consent is needed, decorator puts auth URL in shared queue
- Entrypoint yields auth URL events to frontend for OAuth2 redirect
- After login, frontend callback completes token binding
- Decorator polling succeeds and tool executes with injected access_token
"""

import asyncio
import contextlib
import logging
import os
import sys
import uuid
from collections.abc import AsyncGenerator
from typing import Any

# Configure logging FIRST - before any application imports
# This ensures module-level logging in src.tools.reservations is captured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,  # Override any existing configuration
)

logger = logging.getLogger(__name__)
logger.info("[AGENT_APP] Logging configured successfully")

# Application imports - after logging is configured
# These imports trigger module-level logging in reservations.py
from bedrock_agentcore.runtime import BedrockAgentCoreApp  # noqa: E402
from strands.session.s3_session_manager import S3SessionManager  # noqa: E402

from src.agent import create_booking_agent  # noqa: E402
from src.tools import set_auth_url_queue  # noqa: E402

# Initialize AgentCore app
app = BedrockAgentCoreApp()

# Session configuration from environment
SESSION_BUCKET = os.environ.get("SESSION_BUCKET", "")
SESSION_PREFIX = os.environ.get("SESSION_PREFIX", "agent-sessions/")


def _create_session_agent(session_id: str) -> Any:
    """Create an agent with session management for conversation persistence.

    Args:
        session_id: Unique identifier for the conversation session.
                   Conversations with the same session_id share history.

    Returns:
        Agent instance configured with S3 session manager (if SESSION_BUCKET is set)
        or a basic agent without session persistence (for local development).
    """
    if SESSION_BUCKET:
        # Production: Use S3 for session persistence
        logger.info(f"Creating agent with S3 session: bucket={SESSION_BUCKET}, session={session_id}")
        session_manager = S3SessionManager(
            session_id=session_id,
            bucket=SESSION_BUCKET,
            prefix=SESSION_PREFIX,
        )
        return create_booking_agent(session_manager=session_manager)
    else:
        # Development/fallback: No session persistence
        logger.warning("SESSION_BUCKET not set - agent will not persist conversation history")
        return create_booking_agent()


@app.entrypoint
async def invoke(payload: dict[str, Any]) -> AsyncGenerator[dict[str, Any]]:
    """Handle agent invocation requests with AI SDK v6 streaming.

    Uses stream_async for native async streaming (follows AgentCore samples pattern).

    Args:
        payload: Request payload containing:
            - prompt: User message (required)
            - session_id: Session identifier for conversation continuity (required)

    Yields:
        AI SDK v6 UI Message Stream Protocol events:
        - {"type": "start", "messageId": "..."}
        - {"type": "text-start", "id": "..."}
        - {"type": "text-delta", "id": "...", "delta": "..."}
        - {"type": "text-end", "id": "..."}
        - {"type": "auth_required", "authorization_url": "..."} (OAuth2 login needed)
        - {"type": "finish", "finishReason": "stop"}
    """
    prompt = payload.get("prompt", "")
    session_id = payload.get("session_id", str(uuid.uuid4()))
    message_id = f"msg_{uuid.uuid4().hex[:16]}"
    text_part_id = f"text_{uuid.uuid4().hex[:16]}"

    logger.info(f"Agent invocation: session_id={session_id}, prompt_length={len(prompt)}")

    if not prompt:
        # Emit error as AI SDK v6 stream
        yield {"type": "start", "messageId": message_id}
        yield {"type": "text-start", "id": text_part_id}
        yield {
            "type": "text-delta",
            "id": text_part_id,
            "delta": "Error: No prompt provided. Please include a 'prompt' key in the request.",
        }
        yield {"type": "text-end", "id": text_part_id}
        yield {"type": "finish", "finishReason": "error"}
        return

    # Emit start events
    yield {"type": "start", "messageId": message_id}
    yield {"type": "text-start", "id": text_part_id}

    # Create auth URL queue for OAuth2 login flow
    # The @requires_access_token decorator puts auth URLs here when consent is needed
    auth_url_queue: asyncio.Queue[str] = asyncio.Queue()

    # Event queue to merge stream events and auth URLs
    # This allows us to yield auth URLs while the decorator is polling for tokens
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    try:
        # Register the queue so @requires_access_token callbacks can use it
        set_auth_url_queue(auth_url_queue)

        # Create a session-bound agent
        agent = _create_session_agent(session_id)

        async def stream_events() -> None:
            """Run agent stream and put events into merged queue."""
            try:
                async for event in agent.stream_async(prompt):
                    if "data" in event and event["data"]:
                        await event_queue.put({
                            "type": "text-delta",
                            "id": text_part_id,
                            "delta": event["data"],
                        })
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await event_queue.put({
                    "type": "text-delta",
                    "id": text_part_id,
                    "delta": f"\n\nError: {str(e)}",
                })
            finally:
                # Signal stream completion
                await event_queue.put({"type": "_stream_done"})

        async def monitor_auth_urls() -> None:
            """Monitor auth URL queue and forward to event queue.

            This runs concurrently with stream_events, so auth URLs are
            yielded immediately when the decorator puts them in the queue,
            even if the decorator is blocking while polling for tokens.
            """
            while True:
                try:
                    # Wait for auth URL with timeout to allow checking for completion
                    auth_url = await asyncio.wait_for(auth_url_queue.get(), timeout=0.1)
                    logger.info("Auth URL monitor: forwarding auth_required event")
                    await event_queue.put({"type": "auth_required", "authorization_url": auth_url})
                except TimeoutError:
                    # Check if we should stop (stream task done check happens in main loop)
                    pass
                except asyncio.CancelledError:
                    break

        # Start both tasks concurrently
        stream_task = asyncio.create_task(stream_events())
        auth_monitor_task = asyncio.create_task(monitor_auth_urls())

        try:
            # Yield events from merged queue until stream completes
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)

                    if event.get("type") == "_stream_done":
                        # Stream finished, exit loop
                        break

                    yield event
                except TimeoutError:
                    # Check if stream task is done (shouldn't happen without _stream_done)
                    if stream_task.done():
                        break
        finally:
            # Clean up tasks
            auth_monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await auth_monitor_task

    except Exception as e:
        logger.error(f"Invoke error: {e}")
        yield {
            "type": "text-delta",
            "id": text_part_id,
            "delta": f"\n\nError: {str(e)}",
        }
    finally:
        # Clean up queue reference to prevent stale references
        set_auth_url_queue(None)

    # Emit end events
    yield {"type": "text-end", "id": text_part_id}
    yield {"type": "finish", "finishReason": "stop"}


if __name__ == "__main__":
    app.run()
