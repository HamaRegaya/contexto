# Use a base image with Python and Flask pre-installed
FROM python:3.10.8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# By default, listen on port 5000
EXPOSE 8080

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .
COPY .env .
COPY glove-wiki-gigaword-50.model .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the application files
COPY . .

# Specify the command to run on container start
CMD [ "python", "./app.py" ]
