# ============================================
# Stage 1: Frontend builder (Vite/React)
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install && echo "✅ NPM modules installed"

COPY frontend/ .
RUN npm run build && echo "✅ Frontend build complete" && ls -l dist/


# ============================================
# Stage 2: Final image with backend + Nginx
# ============================================
FROM python:3.11-slim AS final

# Install OS dependencies including supervisor
RUN apt-get update && \
    apt-get install -y nginx curl supervisor dnsutils gettext-base  && \
    apt-get clean

# Create a working directory
WORKDIR /app

# Create a virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy backend code and install dependencies inside the venv
COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir uvicorn fastapi gunicorn  -r requirements.txt && echo "✅ Python packages installed"

# Copy backend source
COPY backend/ .

# confirm
RUN which uvicorn && uvicorn --version

# Copy frontend build
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Create folders for logs/data
RUN mkdir -p crew_logs proposal-documents && chmod -R 755 crew_logs proposal-documents

# Copy custom nginx config
COPY nginx-proxy/nginx.conf /etc/nginx/conf.d/default.conf

## ensure logs can be written
RUN chmod 777 /dev/stdout /dev/stderr

# Expose Cloud Run default port
EXPOSE 8080


# ============================================
# Stage 3: Start FastAPI + Nginx in parallel 
# ============================================
# Copy supervisor config
COPY supervisor/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
# CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

## using a dedicated script..
# Copy the startup script and make it executable
COPY supervisor/start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

CMD ["/usr/local/bin/start.sh"]