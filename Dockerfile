FROM python:3.12-slim

WORKDIR /app

# Install necessary system dependencies (gcc for compiling certain packages, libpq-dev for postgres if needed)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install them
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY backend/ .

# Expose port (Render/Railway use the PORT environment variable)
EXPOSE $PORT

# Command to run on start
# We run alembic upgrade head to ensure DB tables are created, then start gunicorn
CMD ["sh", "-c", "alembic upgrade head && gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]
