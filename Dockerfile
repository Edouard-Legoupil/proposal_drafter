
# ============================================
# Stage 1: Frontend builder (Vite/React)
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app
# Use separate copy to leverage Docker layer caching on npm installs
COPY frontend/package*.json ./
RUN npm ci && echo "✅ NPM modules installed"

COPY frontend/ .
RUN npm run build && echo "✅ Frontend build complete"


# ============================================
# Stage 2: Final Python application image
# ============================================
FROM python:3.11-slim AS final

# Install OS dependencies (only what we need)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dnsutils \
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

# ------------------------------------------------
# Create ONE Python venv used by the whole image
# ------------------------------------------------
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
# Let Python resolve 'backend' via /app
ENV PYTHONPATH=/app

# ------------------------------------------------
# Dependency install (use requirements.txt first)
# ------------------------------------------------
# Copy only requirements first to maximize cache hits
RUN mkdir -p backend
COPY backend/requirements.txt backend/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir uvicorn fastapi gunicorn \
    && pip install --no-cache-dir -r backend/requirements.txt

# ------------------------------------------------
# Optional: NLTK data
# ------------------------------------------------
ENV NLTK_DATA=/app/nltk_data
RUN mkdir -p $NLTK_DATA \
    && python - <<'PY'
import nltk, os
path = os.getenv("NLTK_DATA", "/app/nltk_data")
nltk.data.path.append(path)
try:
    nltk.download("punkt", download_dir=path)
    nltk.download("punkt_tab", download_dir=path)
    print("✅ NLTK data downloaded")
except Exception as e:
    print("⚠️ NLTK download failed:", e)
PY

# ------------------------------------------------
# Copy backend source code
# ------------------------------------------------
COPY backend/ backend/

# IMPORTANT: ensure no local virtualenv sneaks in
RUN rm -rf /app/backend/venv || true

# ------------------------------------------------
# Copy frontend static build files
# ------------------------------------------------
COPY --from=frontend-builder /app/dist /app/frontend/dist

# ------------------------------------------------
# Create directories for logs & data
# ------------------------------------------------
RUN mkdir -p /app/log /app/proposal-documents   \
    && chmod -R 755 /app/log /app/proposal-documents /app/backend/knowledge

# Copy the knowledge files (if any) for your app
COPY ./backend/knowledge/combine_example.json /app/backend/knowledge/

# Ensure stdout/stderr logging works (azure collects container stdout/stderr automatically)
# You generally don't need to chmod /dev/stdout|/dev/stderr; leave them as-is
# RUN chmod 777 /dev/stdout /dev/stderr

# ------------------------------------------------
# Expose the container port (informational)
# Azure App Service will route to the container port set via WEBSITES_PORT in App Settings
# ------------------------------------------------
EXPOSE 8080

# ------------------------------------------------
# Add start script
# ------------------------------------------------
COPY supervisor/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# ------------------------------------------------
# Allow for SSH
# ------------------------------------------------


# Install OpenSSH server
RUN apt-get update && apt-get install -y --no-install-recommends openssh-server \
 && rm -rf /var/lib/apt/lists/*

# Generate host keys and prepare runtime dir
RUN ssh-keygen -A && mkdir -p /var/run/sshd

# Azure tunnel expects this credential (used only via the localhost tunnel)
RUN echo "root:Docker!" | chpasswd

# Provide Azure-compatible SSH config (Port 2222, compatible ciphers/MACs)
COPY sshd_config /etc/ssh/sshd_config


#  expose 2222
COPY sshd_config /etc/ssh/sshd_config
EXPOSE 2222


# ------------------------------------------------
# Default command
# ------------------------------------------------
CMD ["/usr/local/bin/start.sh"]
