FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories for logs and ensure proper permissions
RUN mkdir -p crew_logs proposal-documents && \
    chmod -R 755 crew_logs proposal-documents

# Expose port for FastAPI
EXPOSE 80

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
