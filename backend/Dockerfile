FROM python:3.11-slim-bookworm
# Use a slim version of Python 3.11 on Debian Bullseye  

# Install dependencies and CA certificates
RUN apt-get update && \
    apt-get install  -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libsqlite3-dev \
    && update-ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# Ensure pip is updated
RUN python -m pip install --upgrade pip setuptools
# Install Python dependencies
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
COPY . .

# Create directories for logs and ensure proper permissions
RUN mkdir -p crew_logs proposal-documents && \
    chmod -R 755 crew_logs proposal-documents

# Expose port for FastAPI
EXPOSE 80

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8502"]