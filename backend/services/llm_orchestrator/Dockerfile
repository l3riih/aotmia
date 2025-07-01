FROM python:3.11-slim

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

# Expose port
EXPOSE 8002

# Start service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"] 