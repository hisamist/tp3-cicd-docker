# Use a lightweight Python base image
FROM python:3.11-slim

# Install 'uv' by copying the binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Ensures uv.lock is not updated during build
# --no-cache: Reduces image size by not storing cache files
RUN uv sync --frozen --no-cache

# Copy the application source code
COPY ./src ./src

# Execution command
# 'uv run' handles the virtual environment and path resolution automatically
# We bind to 0.0.0.0 to allow external access (from outside the container)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]