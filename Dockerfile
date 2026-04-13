FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY config.py models.py utils.py main.py ./
COPY fetch/ ./fetch/
COPY process/ ./process/
COPY storage/ ./storage/
COPY notion/ ./notion/
COPY examples/ ./examples/

# Cache and output directories (mounted as volumes in production)
RUN mkdir -p cache/arxiv cache/ar5iv papers logs

# Runtime environment variables — supply real values at docker run / compose time
ENV NOTION_TOKEN=""
ENV NOTION_ROOT_PAGE_ID=""
ENV DASHSCOPE_API_KEY=""
ENV QWEN_MODEL="qwen-plus"
ENV QWEN_ENABLED="true"
ENV ARXIV_REQUEST_DELAY="3.0"
ENV CACHE_ENABLED="true"
ENV CACHE_DIR="/app/cache"
ENV LOG_LEVEL="INFO"

# Default: print help
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
