# Quesada Apartment Booking Backend - AgentCore Runtime Container
# Platform: linux/arm64 (required by AgentCore Runtime)

FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy root workspace config first for better caching
# The root pyproject.toml defines the UV workspace members
COPY pyproject.toml uv.lock README.md ./

# Copy all workspace packages (configs + source)
# UV workspaces with src-layout need source dirs during sync
# because UV builds editable installs and validates module existence
COPY shared/ ./shared/
COPY agent/ ./agent/
COPY api/ ./api/

# Install production dependencies only (no dev deps)
# UV will build workspace packages and install external deps
RUN uv sync --frozen --no-cache --no-dev --all-packages

# Force unbuffered Python output (ensures prints appear immediately in CloudWatch)
ENV PYTHONUNBUFFERED=1

# Expose the standard AgentCore Runtime port
EXPOSE 8080

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ping || exit 1

# Run the AgentCore entrypoint using the agent workspace package
# The agent.main module contains the BedrockAgentCoreApp entrypoint
CMD ["uv", "run", "python", "-m", "agent.main"]

# Rebuild trigger: 2025-12-31T11:30:00Z
