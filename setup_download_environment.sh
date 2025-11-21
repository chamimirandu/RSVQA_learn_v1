#!/bin/bash
# Setup script for downloading custom location imagery
# This installs all required packages and sets up Google Earth Engine

set -e  # Exit on error

echo "================================================"
echo "Setting up Download Environment"
echo "================================================"
echo ""

echo "Step 1: Installing required Python packages..."
pip3 install -q earthengine-api geemap requests numpy Pillow --upgrade

echo "✓ Packages installed successfully"
echo ""

echo "Step 2: Checking Google Earth Engine authentication..."
python3 -c "import ee; ee.Initialize()" 2>/dev/null && {
    echo "✓ Google Earth Engine already authenticated"
} || {
    echo "⚠ Google Earth Engine not authenticated yet"
    echo ""
    echo "Please run the following command to authenticate:"
    echo "  earthengine authenticate"
    echo ""
    echo "This will:"
    echo "  1. Open a browser window"
    echo "  2. Ask you to sign in with your Google account"
    echo "  3. Give you an authentication code to paste back"
    echo ""
    echo "After authentication, run this script again."
    exit 1
}

echo ""
echo "================================================"
echo "✓ Setup Complete!"
echo "================================================"
echo ""
echo "You can now run:"
echo "  python3 download_custom_locations.py"
echo ""
