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

# Install OS dependencies
RUN apt-get update && apt-get install -y nginx curl && apt-get clean

# Create a working directory
WORKDIR /app

# Create a virtual environment
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Copy backend code and install dependencies inside the venv
COPY backend/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && echo "✅ Python packages installed"

# Copy backend source
COPY backend/ .

# Copy frontend build
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

# Expose Cloud Run default port
ENV PORT=8080
EXPOSE 8080

# Start FastAPI + Nginx in parallel
CMD ["/start.sh"]


