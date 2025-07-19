FROM python:3.10-slim
WORKDIR /app

# Install system deps
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.4.2 && \
    poetry config virtualenvs.create false

# Copy and install dependencies
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --with dev --no-interaction --no-ansi

# Copy project
COPY . /app

ENV PYTHONUNBUFFERED=1