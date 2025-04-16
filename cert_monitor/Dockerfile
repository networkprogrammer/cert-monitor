# Use the official Python image as the base image
FROM python:3.9-slim

# Install PostgreSQL development libraries
RUN apt-get update && apt-get install -y \
    libpq-dev gcc --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the application
CMD ["python3", "main.py"]