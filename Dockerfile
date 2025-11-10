FROM python:3.9-alpine as base

# Install system dependencies
RUN apk --update add ffmpeg

FROM base as builder

WORKDIR /install
COPY requirements.txt /requirements.txt

RUN apk add gcc libc-dev zlib zlib-dev jpeg-dev
RUN pip install --prefix="/install" -r /requirements.txt

FROM base

# Copy Python packages
COPY --from=builder /install /usr/local/lib/python3.9/site-packages
RUN mv /usr/local/lib/python3.9/site-packages/lib/python3.9/site-packages/* /usr/local/lib/python3.9/site-packages/ 2>/dev/null || true

# Copy application code
COPY zotify /app/zotify
COPY downloader /app/downloader

# Create necessary directories
RUN mkdir -p /app/data /app/downloads

WORKDIR /app

# Default command runs the main service
CMD ["python3", "-m", "downloader.main"]
