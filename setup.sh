#!/bin/bash
# Setup script for talk2n8n project

echo "Setting up talk2n8n project..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo "Setup complete! You can now run the project with:"
echo "source venv/bin/activate"
echo "python main.py"
