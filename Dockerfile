# ═══════════════════════════════════════════════════════════════
#  Dockerfile — VisionaryCare AI Doctor
#  Build: docker build -t ai-doctor .
#  Run:   docker compose up
# ═══════════════════════════════════════════════════════════════

# ── Stage 1: dependency builder ─────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools for native packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libportaudio2 \
        portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: production image ────────────────────────────────────
FROM python:3.11-slim AS production

LABEL maintainer="VisionaryCare AI Doctor"
LABEL description="AI-powered medical image analysis with voice output"

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        libportaudio2 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/audio /app/flagged \
    && chown -R appuser:appuser /app

# Copy application source (images, scripts)
COPY --chown=appuser:appuser \
    gradio_app.py \
    brain_of_the_doctor.py \
    voice_of_the_doctor.py \
    voice_of_the_patient.py \
    ./

# Copy sample medical images (for UI examples)
COPY --chown=appuser:appuser \
    redeye.jpg \
    skin.jpg \
    chest.jpg \
    dental.jpg \
    hair.jpg \
    burn.jpg \
    ./

USER appuser

# Gradio listens on 7860 — Nginx will proxy from 80
EXPOSE 7860

# Health check — Gradio exposes /gradio_api/startup-events when ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/gradio_api/startup-events || exit 1

# Start the app
CMD ["python", "-u", "gradio_app.py"]
