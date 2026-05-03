FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy framework
COPY . .

# Default command
CMD ["python", "run.py", "--help"]