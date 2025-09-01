# Use the Microsoft devcontainer universal image as base
# Platform specified for consistency across ARM and x86 hosts
FROM --platform=linux/amd64 mcr.microsoft.com/devcontainers/universal:2

# Switch to root to install packages
USER root

# Set platform for consistency
ARG TARGETPLATFORM=linux/amd64

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 using apt (more reliable than pyenv in containers)
USER root
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 20 directly using NodeSource repository
USER root
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install/Update AWS CLI v2
USER root
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install --update && \
    rm -rf awscliv2.zip aws

# Create workspace directory structure
RUN mkdir -p /workspaces/amazon-nova-robotics && \
    chown -R codespace:codespace /workspaces

# Switch back to codespace user
USER codespace

# Set working directory
WORKDIR /workspaces

# Verify installations
RUN python --version && \
    python3 --version && \
    node --version && \
    npm --version && \
    aws --version

# Set default shell
SHELL ["/bin/bash", "-c"]

# Expose common ports
EXPOSE 3000 8000 8080 5000
