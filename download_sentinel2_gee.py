#!/usr/bin/env python3
"""
Download Cloud-Free Sentinel-2 Imagery from Google Earth Engine

This script downloads cloud-free Sentinel-2 RGB composites for multiple
geographic locations. Features include:
- Automatic cloud filtering
- Median composite creation (removes clouds)
- Multiple location support
- Quality assessment
- Direct export to Google Drive or local download

Requirements:
    pip install earthengine-api geemap

Setup:
    1. Create GEE account: https://earthengine.google.com/signup/
    2. Authenticate: earthengine authenticate
    3. Run this script

Usage:
    python download_sentinel2_gee.py --config locations.json
    python download_sentinel2_gee.py --interactive
"""

import ee
import geemap
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import time


class Sentinel2Downloader:
    """Download cloud-free Sentinel-2 imagery from Google Earth Engine"""

    def __init__(self):
        """Initialize Earth Engine"""
        try:
            ee.Initialize()
            print("✓ Earth Engine initialized successfully")
        except Exception as e:
            print("✗ Earth Engine initialization failed")
            print("Run: earthengine authenticate")
            raise e

    def get_cloud_free_composite(self, roi, start_date, end_date,
                                  cloud_percentage=10, scale=10):
        """
        Get cloud-free Sentinel-2 composite for a region

        Args:
            roi: Earth Engine Geometry (region of interest)
            start_date: Start date string (YYYY-MM-DD)
            end_date: End date string (YYYY-MM-DD)
            cloud_percentage: Maximum cloud percentage (default: 10)
            scale: Resolution in meters (default: 10 for Sentinel-2)

        Returns:
            ee.Image: Cloud-free RGB composite
        """
        print(f"\n  Querying Sentinel-2 images...")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Max cloud percentage: {cloud_percentage}%")

        # Load Sentinel-2 Surface Reflectance collection
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_percentage))

        # Count available images
        count = collection.size().getInfo()
        print(f"  Found {count} images matching criteria")

        if count == 0:
            print("  ⚠ Warning: No images found. Try:")
            print("    - Expanding date range")
            print("    - Increasing cloud percentage threshold")
            print("    - Checking if ROI is valid")
            return None

        # Select RGB bands (B4=Red, B3=Green, B2=Blue)
        collection = collection.select(['B4', 'B3', 'B2'])

        # Create median composite (automatically removes clouds)
        composite = collection.median().clip(roi)

        # Scale to 0-255 range for visualization
        composite = composite.visualize(
            min=0,
            max=3000,
            gamma=1.4
        )

        print(f"  ✓ Composite created successfully")
        return composite

    def assess_image_quality(self, image, roi):
        """
        Assess quality of the composite image

        Args:
            image: ee.Image to assess
            roi: Region of interest

        Returns:
            dict: Quality metrics
        """
        # Calculate statistics
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                reducer2=ee.Reducer.stdDev(),
                sharedInputs=True
            ),
            geometry=roi,
            scale=30,
            maxPixels=1e9
        ).getInfo()

        quality = {
            'mean': stats.get('vis-red_mean', 0),
            'std': stats.get('vis-red_stdDev', 0)
        }

        print(f"\n  Quality Assessment:")
        print(f"    Mean pixel value: {quality['mean']:.2f}")
        print(f"    Std deviation: {quality['std']:.2f}")

        # Quality warnings
        if quality['mean'] < 30:
            print("    ⚠ Warning: Very dark image (mean < 30)")
        elif quality['mean'] > 200:
            print("    ⚠ Warning: Very bright image (mean > 200)")
        else:
            print("    ✓ Good brightness range")

        if quality['std'] < 10:
            print("    ⚠ Warning: Low contrast (std < 10)")
        else:
            print("    ✓ Good contrast")

        return quality

    def export_to_drive(self, image, roi, description, folder='RSVQA_Sentinel2',
                       scale=10, crs='EPSG:3857'):
        """
        Export image to Google Drive

        Args:
            image: ee.Image to export
            roi: Region of interest
            description: Export task description
            folder: Google Drive folder name
            scale: Resolution in meters
            crs: Coordinate reference system (EPSG:3857 for Web Mercator)

        Returns:
            ee.batch.Task: Export task
        """
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder=folder,
            scale=scale,
            region=roi,
            crs=crs,
            fileFormat='GeoTIFF',
            maxPixels=1e9,
            formatOptions={
                'cloudOptimized': True
            }
        )

        task.start()
        print(f"\n  ✓ Export task started: {description}")
        print(f"    Task ID: {task.id}")
        print(f"    Check status at: https://code.earthengine.google.com/tasks")

        return task

    def download_to_local(self, image, roi, output_path, scale=10):
        """
        Download image directly to local file

        Args:
            image: ee.Image to download
            roi: Region of interest
            output_path: Local file path
            scale: Resolution in meters
        """
        print(f"\n  Downloading to: {output_path}")

        try:
            # Use geemap for local download
            geemap.ee_export_image(
                image,
                filename=output_path,
                scale=scale,
                region=roi,
                file_per_band=False
            )
            print(f"  ✓ Download complete")
        except Exception as e:
            print(f"  ✗ Download failed: {str(e)}")
            print(f"  Tip: Use export_to_drive() instead for large areas")

    def process_location(self, name, bbox, start_date, end_date,
                        cloud_percentage=10, export_method='drive',
                        output_dir='./downloads'):
        """
        Process a single location

        Args:
            name: Location name
            bbox: Bounding box [lon_min, lat_min, lon_max, lat_max]
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_percentage: Max cloud percentage
            export_method: 'drive' or 'local'
            output_dir: Output directory for local downloads

        Returns:
            dict: Processing results
        """
        print(f"\n{'='*70}")
        print(f"Processing: {name}")
        print(f"{'='*70}")

        # Create ROI
        roi = ee.Geometry.Rectangle(bbox)
        print(f"  Bounding box: {bbox}")

        # Get composite
        composite = self.get_cloud_free_composite(
            roi, start_date, end_date, cloud_percentage
        )

        if composite is None:
            return {
                'name': name,
                'success': False,
                'error': 'No images found'
            }

        # Assess quality
        quality = self.assess_image_quality(composite, roi)

        # Export
        if export_method == 'drive':
            task = self.export_to_drive(
                composite,
                roi,
                description=f'{name}_sentinel2',
                folder='RSVQA_Sentinel2'
            )
            result = {
                'name': name,
                'success': True,
                'task_id': task.id,
                'quality': quality
            }
        else:  # local
            output_path = Path(output_dir) / f'{name}_sentinel2.tif'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self.download_to_local(composite, roi, str(output_path))
            result = {
                'name': name,
                'success': True,
                'output_path': str(output_path),
                'quality': quality
            }

        return result


def load_locations_from_json(json_path):
    """Load location definitions from JSON file"""
    with open(json_path, 'r') as f:
        config = json.load(f)
    return config


def interactive_mode():
    """Interactive mode to define locations"""
    print("\n" + "="*70)
    print("Interactive Sentinel-2 Download")
    print("="*70)

    locations = []

    while True:
        print("\n" + "-"*70)
        name = input("Location name (or 'done' to finish): ").strip()
        if name.lower() == 'done':
            break

        print("\nEnter bounding box coordinates:")
        lon_min = float(input("  Longitude min: "))
        lat_min = float(input("  Latitude min: "))
        lon_max = float(input("  Longitude max: "))
        lat_max = float(input("  Latitude max: "))
        bbox = [lon_min, lat_min, lon_max, lat_max]

        # Date range
        print("\nDate range (YYYY-MM-DD):")
        start_date = input("  Start date [2023-01-01]: ").strip() or "2023-01-01"
        end_date = input("  End date [2023-12-31]: ").strip() or "2023-12-31"

        # Cloud threshold
        cloud_pct = input("  Max cloud percentage [10]: ").strip()
        cloud_pct = int(cloud_pct) if cloud_pct else 10

        locations.append({
            'name': name,
            'bbox': bbox,
            'start_date': start_date,
            'end_date': end_date,
            'cloud_percentage': cloud_pct
        })

        print(f"\n✓ Added location: {name}")

    return locations


def get_predefined_locations():
    """Get predefined example locations"""
    return [
        {
            'name': 'newyork_manhattan',
            'bbox': [-74.05, 40.7, -73.95, 40.8],
            'start_date': '2023-06-01',
            'end_date': '2023-09-30',
            'cloud_percentage': 10
        },
        {
            'name': 'iowa_farmland',
            'bbox': [-93.65, 41.55, -93.55, 41.65],
            'start_date': '2023-07-01',
            'end_date': '2023-09-30',
            'cloud_percentage': 10
        },
        {
            'name': 'amazon_rainforest',
            'bbox': [-60.1, -3.1, -60.0, -3.0],
            'start_date': '2023-06-01',
            'end_date': '2023-09-30',
            'cloud_percentage': 15
        },
        {
            'name': 'california_coast',
            'bbox': [-122.5, 37.7, -122.4, 37.8],
            'start_date': '2023-06-01',
            'end_date': '2023-09-30',
            'cloud_percentage': 5
        },
        {
            'name': 'arizona_desert',
            'bbox': [-111.1, 33.4, -111.0, 33.5],
            'start_date': '2023-06-01',
            'end_date': '2023-09-30',
            'cloud_percentage': 5
        }
    ]


def main():
    parser = argparse.ArgumentParser(
        description='Download cloud-free Sentinel-2 imagery from Google Earth Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode
    python download_sentinel2_gee.py --interactive

    # Use predefined locations
    python download_sentinel2_gee.py --predefined --export_method drive

    # Load from JSON config
    python download_sentinel2_gee.py --config locations.json --export_method local

JSON Config Format:
    {
        "locations": [
            {
                "name": "newyork",
                "bbox": [-74.05, 40.7, -73.95, 40.8],
                "start_date": "2023-06-01",
                "end_date": "2023-09-30",
                "cloud_percentage": 10
            }
        ]
    }

Tips for selecting good locations:
    1. Start with 0.1° × 0.1° areas (about 11km × 11km)
    2. Choose summer months (Jun-Sep) for less cloud cover
    3. Coastal/tropical areas: increase cloud percentage to 15-20
    4. Desert/arid areas: can use lower cloud percentage (5)
    5. Use Google Earth to preview areas first
        """
    )

    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode to define locations')
    parser.add_argument('--predefined', action='store_true',
                       help='Use predefined example locations')
    parser.add_argument('--config', type=str,
                       help='JSON config file with locations')
    parser.add_argument('--export_method', type=str, default='drive',
                       choices=['drive', 'local'],
                       help='Export to Google Drive or download locally')
    parser.add_argument('--output_dir', type=str, default='./downloads',
                       help='Output directory for local downloads')

    args = parser.parse_args()

    # Get locations
    if args.interactive:
        locations = interactive_mode()
    elif args.predefined:
        locations = get_predefined_locations()
        print("\n" + "="*70)
        print("Using Predefined Locations:")
        print("="*70)
        for loc in locations:
            print(f"  - {loc['name']}: {loc['bbox']}")
    elif args.config:
        config = load_locations_from_json(args.config)
        locations = config['locations']
        print(f"\nLoaded {len(locations)} locations from {args.config}")
    else:
        print("Error: Must specify --interactive, --predefined, or --config")
        return

    if not locations:
        print("No locations to process")
        return

    # Initialize downloader
    print("\nInitializing Earth Engine...")
    downloader = Sentinel2Downloader()

    # Process each location
    results = []
    for location in locations:
        result = downloader.process_location(
            name=location['name'],
            bbox=location['bbox'],
            start_date=location['start_date'],
            end_date=location['end_date'],
            cloud_percentage=location.get('cloud_percentage', 10),
            export_method=args.export_method,
            output_dir=args.output_dir
        )
        results.append(result)

        # Small delay between requests
        time.sleep(2)

    # Summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nSuccessful: {len(successful)}/{len(results)}")
    for r in successful:
        print(f"  ✓ {r['name']}")
        if args.export_method == 'drive':
            print(f"    Task ID: {r['task_id']}")
        else:
            print(f"    Saved to: {r['output_path']}")
        print(f"    Quality: mean={r['quality']['mean']:.1f}, std={r['quality']['std']:.1f}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  ✗ {r['name']}: {r['error']}")

    if args.export_method == 'drive':
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print("1. Check export status at: https://code.earthengine.google.com/tasks")
        print("2. Wait for tasks to complete (usually 5-30 minutes)")
        print("3. Download from Google Drive folder: RSVQA_Sentinel2")
        print("4. Run preprocessing: python prepare_sentinel2_data.py")
    else:
        print("\n" + "="*70)
        print("NEXT STEPS:")
        print("="*70)
        print(f"1. Check downloads in: {args.output_dir}")
        print("2. Run preprocessing: python prepare_sentinel2_data.py")

    # Save results to JSON
    results_file = 'download_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'export_method': args.export_method,
            'results': results
        }, f, indent=2)
    print(f"\nResults saved to: {results_file}")


if __name__ == '__main__':
    main()
