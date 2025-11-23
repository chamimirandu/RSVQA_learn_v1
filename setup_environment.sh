#!/bin/bash

echo "================================================"
echo "RSVQA Environment Setup Script"
echo "================================================"
echo ""

# Check if conda is available
if command -v conda &> /dev/null; then
    echo "✓ Conda found"
    echo "Creating conda environment 'rsvqa' with Python 3.7..."
    conda create --name rsvqa python=3.7 -y
    echo ""
    echo "To activate the environment, run:"
    echo "  conda activate rsvqa"
    echo ""
else
    echo "✗ Conda not found. Using system Python."
    echo "Current Python version: $(python --version)"
    echo ""
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "Installing PyTorch and torchvision..."
pip install torch torchvision

echo ""
echo "Additional dependencies for full pipeline:"
echo "  - PostgreSQL + PostGIS (for automatic QA generation)"
echo "  - rasterio (for geospatial image processing)"
echo "  - psycopg2 (for PostgreSQL connection)"
echo ""

read -p "Install additional dependencies? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install rasterio psycopg2-binary shapely
    echo "✓ Additional dependencies installed"
fi

echo ""
echo "Installing skip-thoughts for text encoding..."
read -p "Clone and install skip-thoughts? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git clone https://github.com/Cadene/skip-thoughts.torch.git
    cd skip-thoughts.torch/pytorch
    python setup.py install
    cd ../..
    echo "✓ Skip-thoughts installed"
fi

echo ""
echo "Downloading seq2vec.py..."
mkdir -p VQA_model/models
cd VQA_model/models
wget https://raw.githubusercontent.com/Cadene/vqa.pytorch/master/vqa/models/seq2vec.py
cd ../..

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Place your GEE images in: data/images/"
echo "2. Create question-answer pairs in: data/questions/"
echo "3. Read GETTING_STARTED.md for detailed instructions"
echo ""
echo "For a simple start, see: data/questions/example_qa_template.json"
echo ""
