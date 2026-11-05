FROM python:3.11-slim

WORKDIR /app

# Set timezone and Python environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and definitions
COPY . .

# Expose SSE HTTP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/sse')" || exit 0

# Default command: run as SSE server on 0.0.0.0:8000
CMD ["python3", "server.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
