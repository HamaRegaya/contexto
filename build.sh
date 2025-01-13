#!/bin/bash
echo "Building Flask application..."

# Install Python dependencies
pip install -r requirements.txt

# Copy static files
mkdir -p build/static
cp -r static/* build/static/

# Copy templates
mkdir -p build/templates
cp -r templates/* build/templates/

# Copy Python files
cp app.py build/
cp dynamodb.py build/

# Copy requirements and Procfile
cp requirements.txt build/
cp Procfile build/

echo "Build completed!"
