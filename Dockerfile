FROM python:3.10-slim-buster

WORKDIR /app

# Install system dependencies
RUN apt-get -qq update --fix-missing && \
    apt-get -qq upgrade -y && \
    apt-get install -y git curl wget gnupg2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 fzuser && \
    chown -R fzuser:fzuser /app

USER fzuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose port
EXPOSE 8000

CMD ["bash","start.sh"]
