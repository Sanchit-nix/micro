# Use official slim Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set required environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COQUI_TOS_AGREED=1

# Install system dependencies + Rust (for sudachipy) + cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ffmpeg \
    libsndfile1 \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . $HOME/.cargo/env \
    && export PATH="$HOME/.cargo/bin:$PATH" \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Rust to PATH (persist across layers)
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirement file and install Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create output/voice directories (optional)
RUN mkdir -p /app/output /app/Voice

# Expose FastAPI port
EXPOSE 8002

# Start the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
