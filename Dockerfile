# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Do not write .pyc files and stream logs unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first to take advantage of Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY app/ ./app/

# The Flask/gunicorn app listens on port 8000
EXPOSE 8000

# Run the app with gunicorn (a production WSGI server)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.main:app"]
