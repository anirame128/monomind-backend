FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including libatomic for Prisma
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Generate Prisma client
RUN prisma generate

# Expose port
EXPOSE 8080

# Run migrations and start app
CMD prisma migrate deploy && uvicorn src.main:app --host 0.0.0.0 --port 8080