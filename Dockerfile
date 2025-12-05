# ============================================
# Stage 1: Frontend builder (Vite/React)
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install && echo "✅ NPM modules installed"

COPY frontend/ .
RUN npm run build && echo "✅ Frontend build complete"


# ============================================
# Stage 2: Final Python application image
# ============================================
FROM python:3.11-slim AS final

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    curl \
    supervisor \
    dnsutils \
    gettext-base \
    procps \
    net-tools \
    util-linux \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------
# Create app directory
# ------------------------------------------------
WORKDIR /app

# Create Python venv
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Set the PYTHONPATH to include the /app directory
# This allows Python to find the 'backend' module.
# The `PYTHONPATH` will be set to `/app`
# This allows Python to find the 'backend' module and prevents the warning.
ENV PYTHONPATH=/app

# ------------------------------------------------
# Copy backend first (for dependency install)
# ------------------------------------------------
RUN mkdir -p backend
COPY backend/requirements.txt backend/

# Install backend Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir uvicorn fastapi gunicorn && \
    pip install --no-cache-dir -r backend/requirements.txt

# ------------------------------------------------
# Install NLTK data
# ------------------------------------------------
# Set a NLTK data directory inside the container
ENV NLTK_DATA=/app/nltk_data

RUN mkdir -p $NLTK_DATA && \
    python - <<EOF
import nltk
nltk.data.path.append("$NLTK_DATA")
nltk.download("punkt", download_dir="$NLTK_DATA")
nltk.download("punkt_tab", download_dir="$NLTK_DATA")
EOF

# ------------------------------------------------
# Copy backend source code
# ------------------------------------------------
COPY backend/ backend/

# ------------------------------------------------
# Copy frontend static build files
# ------------------------------------------------
COPY --from=frontend-builder /app/dist /app/frontend/dist

# ------------------------------------------------
# Create directories for logs & data
# ------------------------------------------------
RUN mkdir -p /app/log /app/proposal-documents /app/knowledge && \
    chmod -R 755 /app/log /app/proposal-documents /app/knowledge

# Copy the knowledge files for crewai
COPY ./backend/knowledge/combine_example.json /app/knowledge/

# Ensure stdout/stderr logging works
RUN chmod 777 /dev/stdout /dev/stderr

# Cloud Run port
EXPOSE 8080

# ------------------------------------------------
# Add start script
# ------------------------------------------------
COPY supervisor/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

CMD ["/usr/local/bin/start.sh"]
