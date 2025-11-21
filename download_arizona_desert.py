#!/usr/bin/env python3
"""
Quick-start script to download Arizona Desert

This location features:
- Arid desert terrain with minimal vegetation
- Excellent cloud-free conditions (5% threshold)
- Distinct geological features and sand patterns
- Great for terrain type and color questions

Just run: python download_arizona_desert.py
"""

import ee
import geemap
from pathlib import Path

def main():
    # Initialize Earth Engine
    try:
        ee.Initialize()
        print("✓ Earth Engine initialized\n")
    except:
        print("✗ Please run: earthengine authenticate")
        return

    # Location configuration
    location = {
        'name': 'arizona_desert',
        'description': 'Arizona desert region',
        'bbox': [-111.1, 33.4, -111.0, 33.5],
        'start_date': '2023-06-01',
        'end_date': '2023-09-30',
        'cloud_percentage': 5  # Very low clouds in desert
    }

    print(f"📍 Downloading: {location['description']}")
    print(f"   Date range: {location['start_date']} to {location['end_date']}")
    print(f"   Cloud threshold: {location['cloud_percentage']}%\n")

    # Create ROI
    roi = ee.Geometry.Rectangle(location['bbox'])

    # Query Sentinel-2 with cloud filtering
    collection = ee.ImageCollection('COPERNICUS/S2_SR') \
        .filterBounds(roi) \
        .filterDate(location['start_date'], location['end_date']) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', location['cloud_percentage']))

    count = collection.size().getInfo()
    print(f"📡 Found {count} cloud-free images")

    if count == 0:
        print("⚠ No images found. Try increasing cloud threshold or expanding date range.")
        return

    # Apply cloud masking and create composite
    def mask_clouds(image):
        scl = image.select('SCL')
        cloud_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
        return image.updateMask(cloud_mask)

    composite = collection.map(mask_clouds) \
        .select(['B4', 'B3', 'B2']) \
        .median() \
        .clip(roi)

    # Normalize for visualization
    composite = composite.visualize(min=0, max=3000, gamma=1.4)

    # Download
    output_dir = Path('downloads')
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{location['name']}.tif"

    print(f"💾 Downloading to {output_path}...")
    geemap.ee_export_image(
        composite,
        filename=str(output_path),
        scale=10,
        region=roi,
        file_per_band=False
    )

    print(f"✓ Download complete!")
    print(f"\nNext steps:")
    print(f"  1. Verify image: Open {output_path} in QGIS or other GIS software")
    print(f"  2. Preprocess: python prepare_sentinel2_data.py")

if __name__ == '__main__':
    main()
