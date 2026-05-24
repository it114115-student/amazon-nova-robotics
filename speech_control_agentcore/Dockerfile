# Dockerfile for Robot Voice Control AgentCore
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including portaudio for strands-agents)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install pinned dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose microservice port
EXPOSE 8080

# Run the voice control agent
CMD ["python", "robot_voice_agent.py"]
