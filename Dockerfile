# Use official lightweight Python runtime
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Create a non-root application user
RUN useradd -m -u 1000 appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and knowledge base
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser research/ ./research/
COPY --chown=appuser:appuser .env.example ./

# Switch to non-root user
USER appuser

# Expose container port
EXPOSE 8000

# Health check using existing /health endpoint supporting dynamic PORT
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; port=os.environ.get('PORT', '8000'); res=urllib.request.urlopen(f'http://127.0.0.1:{port}/health'); exit(0 if res.getcode()==200 else 1)"

# Start uvicorn server binding to 0.0.0.0 with dynamic PORT support for Render/cloud deployments
CMD ["sh", "-c", "uvicorn app.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
