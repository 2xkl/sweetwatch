FROM python:3.11-slim AS base

WORKDIR /app

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools wheel

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install dependencies
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "sweetwatch.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
