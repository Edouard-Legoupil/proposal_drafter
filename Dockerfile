# ========================
# Backend build stage
# ========================
FROM python:3.11-slim AS backend-builder

WORKDIR /app


COPY backend/requirements.txt .

RUN python -m venv /venv && \
    . /venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "✅ Python dependencies installed"

COPY backend/ .

# ========================
# Frontend build stage
# ========================
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Install frontend dependencies
COPY frontend/package*.json ./

RUN npm install && echo "✅ NPM dependencies installed"

# Build Vite frontend
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=/api

COPY frontend/ .

RUN npm run build && echo "✅ Frontend build completed" && ls -l dist/



# ========================
# Final image: Nginx + backend + frontend
# ========================
FROM nginx:alpine

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip bash

# Copy Python virtual environment and backend app
COPY --from=backend-builder /venv /venv
COPY --from=backend-builder /app /app

# Activate the venv path
ENV PATH="/venv/bin:$PATH"
WORKDIR /app

# Copy frontend build to Nginx root
COPY --from=frontend-builder /app/dist /usr/share/nginx/html


# Create folders for data
RUN mkdir -p crew_logs proposal-documents && chmod -R 755 crew_logs proposal-documents

# Copy custom nginx config
COPY nginx-proxy/nginx.conf /etc/nginx/conf.d/default.conf

# Expose the Nginx port
EXPOSE 80

# Copy the wrapper script
COPY backend/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8080

# Start FastAPI + Nginx in parallel
CMD ["/start.sh"]


