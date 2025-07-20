#!/bin/bash

# Cloud Cost Guardian Installation Script

echo "Installing Cloud Cost Guardian..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is required but not installed. Please install AWS CLI and try again."
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate the virtual environment and install dependencies
echo "Installing dependencies..."
source "$SCRIPT_DIR/venv/bin/activate"
pip install -r "$SCRIPT_DIR/requirements.txt"
deactivate

# Check if AWS credentials are configured
if [ ! -f ~/.aws/credentials ]; then
    echo "AWS credentials not found. Please configure AWS CLI:"
    aws configure
fi

# Create a symbolic link to make the tool available system-wide
echo "Creating symbolic link..."
if [ ! -d ~/.local/bin ]; then
    mkdir -p ~/.local/bin
fi

ln -sf "$SCRIPT_DIR/cost-guardian" ~/.local/bin/cost-guardian

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "Added ~/.local/bin to PATH in ~/.bashrc"
    echo "Please run 'source ~/.bashrc' or restart your terminal to update your PATH."
fi

echo "Installation complete! You can now run 'cost-guardian' from anywhere."
echo "Try 'cost-guardian overview' to get started."
