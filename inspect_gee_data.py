#!/usr/bin/env python3
"""
Script to inspect Google Earth Engine images
This helps you understand your data before building the RSVQA system
"""

import os
from glob import glob

def inspect_images(image_dir="data/images"):
    """Inspect images in the data directory"""

    print("=" * 60)
    print("GEE Image Data Inspector")
    print("=" * 60)
    print()

    if not os.path.exists(image_dir):
        print(f"❌ Directory not found: {image_dir}")
        print(f"Please create it and place your GEE images there.")
        return

    # Find all image files
    image_extensions = ['*.tif', '*.tiff', '*.TIF', '*.TIFF', '*.jpg', '*.jpeg', '*.png']
    images = []
    for ext in image_extensions:
        images.extend(glob(os.path.join(image_dir, ext)))

    if not images:
        print(f"❌ No images found in {image_dir}")
        print()
        print("Supported formats: GeoTIFF (.tif), JPEG (.jpg), PNG (.png)")
        print()
        print("Please place your Google Earth Engine images in this directory.")
        return

    print(f"✓ Found {len(images)} images")
    print()

    # Try to import rasterio for geospatial analysis
    try:
        import rasterio
        import numpy as np
        has_rasterio = True
    except ImportError:
        has_rasterio = False
        print("⚠ rasterio not installed - limited inspection available")
        print("Install with: pip install rasterio")
        print()

    # Inspect each image
    for i, img_path in enumerate(images[:5], 1):  # Show first 5 images
        print(f"\n--- Image {i}: {os.path.basename(img_path)} ---")

        # Basic file info
        file_size = os.path.getsize(img_path) / (1024 * 1024)  # MB
        print(f"  File size: {file_size:.2f} MB")

        if has_rasterio and img_path.lower().endswith(('.tif', '.tiff')):
            try:
                with rasterio.open(img_path) as src:
                    print(f"  Dimensions: {src.width} x {src.height} pixels")
                    print(f"  Bands: {src.count}")
                    print(f"  Data type: {src.dtypes[0]}")

                    if src.crs:
                        print(f"  CRS: {src.crs}")
                        print(f"  ✓ Georeferenced")
                    else:
                        print(f"  ⚠ Not georeferenced")

                    if src.bounds:
                        print(f"  Bounds: {src.bounds}")

                    # Read first band statistics
                    band1 = src.read(1)
                    print(f"  Value range: [{np.min(band1)}, {np.max(band1)}]")
                    print(f"  Mean: {np.mean(band1):.2f}")

            except Exception as e:
                print(f"  ❌ Error reading with rasterio: {e}")
        else:
            print(f"  (Install rasterio for detailed GeoTIFF inspection)")

    if len(images) > 5:
        print(f"\n... and {len(images) - 5} more images")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total images: {len(images)}")

    if has_rasterio:
        # Check if images are georeferenced
        georef_count = 0
        for img_path in images:
            if img_path.lower().endswith(('.tif', '.tiff')):
                try:
                    with rasterio.open(img_path) as src:
                        if src.crs:
                            georef_count += 1
                except:
                    pass

        if georef_count > 0:
            print(f"Georeferenced: {georef_count}/{len(images)}")
        else:
            print("⚠ No georeferenced images found")
            print("  For automatic QA generation, images should be georeferenced")

    print()
    print("Next steps:")
    print("1. Review the image properties above")
    print("2. Check GETTING_STARTED.md for setup instructions")
    print("3. Decide between:")
    print("   - Simple approach: Create manual QA pairs")
    print("   - Full pipeline: Use OSM data for automatic QA generation")
    print()


if __name__ == "__main__":
    import sys

    # Allow custom directory as argument
    img_dir = sys.argv[1] if len(sys.argv) > 1 else "data/images"
    inspect_images(img_dir)
