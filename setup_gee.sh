#!/bin/bash
# Setup script for Google Earth Engine access

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  Google Earth Engine Setup for RSVQA                             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.7 or higher."
    exit 1
fi
echo "✓ Python found"
echo ""

# Install Earth Engine packages
echo "Installing Earth Engine API and geemap..."
pip install earthengine-api geemap --upgrade

if [ $? -ne 0 ]; then
    echo "❌ Installation failed"
    exit 1
fi
echo "✓ Packages installed"
echo ""

# Authenticate with Earth Engine
echo "Authenticating with Google Earth Engine..."
echo "This will open a browser window for authentication."
echo "Please log in with your Google account."
echo ""
read -p "Press Enter to continue..."

earthengine authenticate

if [ $? -ne 0 ]; then
    echo "❌ Authentication failed"
    exit 1
fi
echo "✓ Authentication successful"
echo ""

# Test connection
echo "Testing Earth Engine connection..."
python3 << EOF
import ee
try:
    ee.Initialize()
    print("✓ Earth Engine connection successful!")

    # Get a simple test
    test_image = ee.Image('COPERNICUS/S2_SR/20230601T000000_20230601T000000_T01TBB')
    print("✓ Can access Sentinel-2 data")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Test failed"
    exit 1
fi
echo ""

# Create directories
echo "Creating directories..."
mkdir -p downloads
mkdir -p dataset/images
mkdir -p dataset/splits
echo "✓ Directories created"
echo ""

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  Setup Complete!                                                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "Option 1 - Python Script (Recommended):"
echo "  1. Edit locations_example.json with your desired locations"
echo "  2. Run: python download_sentinel2_gee.py --config locations_example.json"
echo ""
echo "Option 2 - JavaScript in GEE Code Editor:"
echo "  1. Go to: https://code.earthengine.google.com/"
echo "  2. Copy contents of download_sentinel2_gee.js"
echo "  3. Modify LOCATIONS configuration"
echo "  4. Click Run"
echo ""
echo "Option 3 - Interactive Python:"
echo "  Run: python download_sentinel2_gee.py --interactive"
echo ""
echo "Option 4 - Predefined Locations:"
echo "  Run: python download_sentinel2_gee.py --predefined"
echo ""
