# Use the official AWS Lambda Python 3.13 base image
FROM public.ecr.aws/lambda/python:3.13

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements file first for better caching
COPY requirements.txt ./

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# Copy the application code
COPY . ./

# Set the CMD to your handler
CMD ["app.handler"]
