#!/bin/bash
# Setup script for CDN Server Selection Project (Linux/Mac)

set -e  # Exit on error

echo "🚀 CDN Server Selection Project Setup"
echo "======================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
if [ "$1" = "minimal" ]; then
    echo "📥 Installing minimal requirements..."
    pip install -r requirements-minimal.txt
else
    echo "📥 Installing full requirements..."
    pip install -r requirements.txt
fi

# Create project structure
echo "📁 Creating project directories..."
mkdir -p data/{raw,processed,external}
mkdir -p notebooks/{exploratory,analysis,modeling}
mkdir -p src/{preprocessing,models,evaluation,utils}
mkdir -p results/{figures,tables,models}
mkdir -p tests
mkdir -p docs

# Create .env template
echo "📝 Creating .env template..."
cat > .env << EOF
# RIPE Atlas API Configuration
RIPE_ATLAS_API_KEY=your_api_key_here

# Project Configuration
PROJECT_NAME=cdn-server-selection
DATA_DIR=./data
RESULTS_DIR=./results

# ML Configuration
RANDOM_SEED=42
TEST_SIZE=0.2
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate environment: source venv/bin/activate"
echo "2. Add RIPE Atlas API key to .env file"
echo "3. Run verification: python verify_installation.py"
echo "4. Start Jupyter: jupyter notebook"
