FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy python configuration files
COPY pyproject.toml ./

# Install python dependencies without cache
RUN pip install --no-cache-dir .

# Copy application code and scripts
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create necessary directories for local persistence
RUN mkdir -p data/chroma data/sessions data/failed_flows

# Expose API port
EXPOSE 8000

# Start server using uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
