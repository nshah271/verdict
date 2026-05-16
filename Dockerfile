FROM python:3.11-slim

# Install git (required for git diff to work)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and install verdict from source (the PyPI package named verdict-ai
# is unrelated to this project; do not install from PyPI).
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir .

# Set entrypoint
ENTRYPOINT ["verdict", "run"]

# Made with Bob
