FROM python:3.11-slim

# Install git (required for git diff to work)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install from source. Published on PyPI as `myverdict` (the older
# `verdict-ai` slot was taken by an unrelated project before we shipped).
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

# Set entrypoint
ENTRYPOINT ["verdict", "run"]

# Made with Bob
