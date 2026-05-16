FROM python:3.11-slim

# Install git (required for git diff to work)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install verdict-ai
RUN pip install --no-cache-dir verdict-ai

# Set entrypoint
ENTRYPOINT ["verdict", "run"]

# Made with Bob
