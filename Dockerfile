# ============================================
# Stage 1: Frontend builder (Vite/React)
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci && echo "✅ NPM modules installed"

COPY frontend/ .
RUN npm run build && echo "✅ Frontend build complete" && ls -l dist/


# ============================================
# Stage 2: Final image with backend + Nginx
# ============================================
FROM python:3.11-slim AS final

# Install OS dependencies including supervisor
RUN apt-get update && \
    apt-get install -y nginx curl supervisor dnsutils && \
    apt-get clean

# Create a non-root user
RUN useradd -m -u 1000 user
USER user

# Create a working directory
WORKDIR /home/user/app

# Create a virtual environment
RUN python -m venv /home/user/venv
ENV PATH="/home/user/venv/bin:$PATH"

# Create the backend directory inside the container
RUN mkdir backend

# Copy the requirements file into the new backend directory
COPY --chown=user:user backend/requirements.txt backend/

# Install dependencies from the requirements file
RUN pip install --upgrade pip && pip install --no-cache-dir uvicorn fastapi gunicorn -r backend/requirements.txt && echo "✅ Python packages installed"

# Copy all backend source code EXCEPT the knowledge folder into the backend folder
COPY --chown=user:user backend/ backend/


# Set the PYTHONPATH to include the /app directory
# This allows Python to find the 'backend' module.
# The `PYTHONPATH` will be set to `/app`
# This allows Python to find the 'backend' module and prevents the warning.
ENV PYTHONPATH=/home/user/app

# confirm
RUN which uvicorn && uvicorn --version

# Copy frontend build
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Create a logs directory for the application and data
RUN mkdir -p /home/user/app/log /home/user/app/proposal-documents /home/user/app/knowledge && chmod -R 755 /home/user/app/log /home/user/app/proposal-documents /home/user/app/knowledge

# Copy the knowledge files for crewai
COPY --chown=user:user ./backend/knowledge/*.json /home/user/app/knowledge/
# Let's confirm the file exists in the right place
RUN echo "Checking knowledge dir after copy:" && ls -la /home/user/app/knowledge

# Copy custom nginx config
COPY nginx-proxy/nginx.conf /etc/nginx/conf.d/default.conf

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