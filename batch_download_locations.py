#!/usr/bin/env python3
"""
Batch Download Script for Multiple Locations with Enhanced Cloud Filtering

This script downloads Sentinel-2 imagery for multiple locations with:
- Advanced cloud filtering strategies
- Automatic retry with relaxed parameters
- Progress tracking and resume capability
- Quality assessment
- Download status reporting

Usage:
    # Download all remaining locations
    python batch_download_locations.py --all

    # Download specific locations
    python batch_download_locations.py --locations california_coast arizona_desert chicago_urban

    # Download with custom cloud threshold
    python batch_download_locations.py --all --max-cloud 20

    # Skip already downloaded locations
    python batch_download_locations.py --all --skip-existing
"""

import ee
import geemap
import argparse
import json
from datetime import datetime
from pathlib import Path
import time
import numpy as np
from PIL import Image
import sys


class BatchDownloader:
    """Batch download Sentinel-2 imagery with enhanced cloud filtering"""

    def __init__(self, output_dir="downloads", skip_existing=False):
        """Initialize Earth Engine and setup directories"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.skip_existing = skip_existing
        self.download_log = []

        try:
            ee.Initialize()
            print("✓ Earth Engine initialized successfully\n")
        except Exception as e:
            print("✗ Earth Engine initialization failed")
            print("Run: earthengine authenticate")
            raise e

    def get_cloud_free_composite(self, roi, start_date, end_date,
                                  cloud_percentage=10, location_name=""):
        """
        Get cloud-free Sentinel-2 composite with enhanced filtering

        This method uses multiple strategies:
        1. Filter by CLOUDY_PIXEL_PERCENTAGE metadata
        2. Apply SCL (Scene Classification Layer) cloud mask
        3. Create median composite to remove remaining clouds

        Args:
            roi: Earth Engine Geometry
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_percentage: Max cloud percentage threshold
            location_name: Name for logging

        Returns:
            ee.Image or None
        """
        print(f"  📡 Querying Sentinel-2 for {location_name}...")
        print(f"     Date range: {start_date} to {end_date}")
        print(f"     Max cloud: {cloud_percentage}%")

        # Strategy 1: Filter by cloud percentage metadata
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_percentage))

        count = collection.size().getInfo()
        print(f"     Found {count} images after cloud filtering")

        if count == 0:
            print("     ⚠ No images found with current parameters")
            return None

        # Strategy 2: Apply cloud masking using SCL band
        def mask_clouds(image):
            """Mask clouds using Scene Classification Layer (SCL)"""
            scl = image.select('SCL')
            # SCL values: 3=cloud shadows, 8=cloud medium prob, 9=cloud high prob, 10=thin cirrus
            cloud_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            return image.updateMask(cloud_mask)

        # Apply cloud mask to each image
        masked_collection = collection.map(mask_clouds)

        # Select RGB bands
        rgb_collection = masked_collection.select(['B4', 'B3', 'B2'])

        # Strategy 3: Median composite (removes remaining cloud pixels)
        composite = rgb_collection.median().clip(roi)

        # Normalize to 0-255 range for RGB visualization
        composite = composite.visualize(
            min=0,
            max=3000,
            gamma=1.4
        )

        print(f"     ✓ Cloud-free composite created")
        return composite

    def assess_quality(self, image_path):
        """
        Assess downloaded image quality

        Checks for:
        - Adequate brightness (not too dark/bright)
        - Good contrast (not uniform/ocean)
        - No excessive black pixels (missing data)
        """
        try:
            img = Image.open(image_path)
            img_array = np.array(img)

            # Calculate statistics
            mean_value = np.mean(img_array)
            std_dev = np.std(img_array)
            black_pixels = np.sum(img_array == 0) / img_array.size * 100

            print(f"\n  📊 Quality Assessment:")
            print(f"     Mean brightness: {mean_value:.1f}")
            print(f"     Std deviation: {std_dev:.1f}")
            print(f"     Black pixels: {black_pixels:.1f}%")

            # Quality checks
            warnings = []
            if mean_value < 30:
                warnings.append("Very dark image (possibly ocean/shadows)")
            elif mean_value > 225:
                warnings.append("Very bright (possibly clouds/snow)")
            else:
                print(f"     ✓ Good brightness range")

            if std_dev < 10:
                warnings.append("Low contrast (uniform area/ocean)")
            else:
                print(f"     ✓ Good contrast")

            if black_pixels > 20:
                warnings.append(f"High missing data ({black_pixels:.1f}%)")
            else:
                print(f"     ✓ Minimal missing data")

            if warnings:
                print("     ⚠ Warnings:")
                for w in warnings:
                    print(f"       - {w}")
                return False

            return True

        except Exception as e:
            print(f"     ✗ Quality assessment failed: {e}")
            return False

    def download_location(self, location_config, override_cloud=None):
        """
        Download imagery for a single location with retry logic

        Args:
            location_config: Dict with location parameters
            override_cloud: Optional cloud threshold override

        Returns:
            bool: Success status
        """
        name = location_config['name']
        description = location_config.get('description', '')
        bbox = location_config['bbox']
        start_date = location_config['start_date']
        end_date = location_config['end_date']
        cloud_pct = override_cloud if override_cloud else location_config.get('cloud_percentage', 10)

        output_path = self.output_dir / f"{name}.tif"

        # Skip if already exists
        if self.skip_existing and output_path.exists():
            print(f"⏭️  Skipping {name} (already exists)")
            self.download_log.append({
                'name': name,
                'status': 'skipped',
                'reason': 'already_exists'
            })
            return True

        print(f"\n{'='*70}")
        print(f"📍 Location: {name}")
        print(f"   {description}")
        print(f"{'='*70}")

        # Create region of interest
        roi = ee.Geometry.Rectangle(bbox)

        # Try downloading with current cloud threshold
        composite = self.get_cloud_free_composite(
            roi, start_date, end_date, cloud_pct, name
        )

        # If failed, try with relaxed cloud threshold
        if composite is None and cloud_pct < 25:
            relaxed_cloud = min(cloud_pct + 10, 25)
            print(f"\n  🔄 Retrying with relaxed cloud threshold: {relaxed_cloud}%")
            composite = self.get_cloud_free_composite(
                roi, start_date, end_date, relaxed_cloud, name
            )

        # If still failed, try expanding date range
        if composite is None:
            print(f"\n  🔄 Attempting to expand date range...")
            from datetime import datetime, timedelta
            start_dt = datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=30)
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=30)
            expanded_start = start_dt.strftime('%Y-%m-%d')
            expanded_end = end_dt.strftime('%Y-%m-%d')

            composite = self.get_cloud_free_composite(
                roi, expanded_start, expanded_end, cloud_pct, name
            )

        if composite is None:
            print(f"\n  ✗ Failed to download {name}")
            self.download_log.append({
                'name': name,
                'status': 'failed',
                'reason': 'no_images_found'
            })
            return False

        # Download the image
        print(f"\n  💾 Downloading to {output_path}...")
        try:
            # Use geemap to download
            geemap.ee_export_image(
                composite,
                filename=str(output_path),
                scale=10,
                region=roi,
                file_per_band=False
            )

            print(f"  ✓ Download complete")

            # Assess quality
            quality_ok = self.assess_quality(output_path)

            self.download_log.append({
                'name': name,
                'status': 'success',
                'file': str(output_path),
                'quality': 'good' if quality_ok else 'warning'
            })

            return True

        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            self.download_log.append({
                'name': name,
                'status': 'error',
                'reason': str(e)
            })
            return False

    def download_batch(self, locations, override_cloud=None):
        """
        Download multiple locations

        Args:
            locations: List of location configs
            override_cloud: Optional cloud threshold for all locations
        """
        total = len(locations)
        successful = 0
        failed = 0

        print(f"\n🚀 Starting batch download for {total} locations")
        print(f"   Output directory: {self.output_dir}")

        start_time = time.time()

        for idx, location in enumerate(locations, 1):
            print(f"\n[{idx}/{total}] Processing: {location['name']}")

            success = self.download_location(location, override_cloud)

            if success:
                successful += 1
            else:
                failed += 1

            # Brief pause between downloads to avoid rate limiting
            if idx < total:
                time.sleep(2)

        # Summary
        elapsed = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"Total locations: {total}")
        print(f"✓ Successful: {successful}")
        print(f"✗ Failed: {failed}")
        print(f"⏱️  Time elapsed: {elapsed/60:.1f} minutes")
        print(f"\nDetailed log:")
        for log in self.download_log:
            status_icon = {'success': '✓', 'failed': '✗', 'skipped': '⏭️', 'error': '✗'}
            icon = status_icon.get(log['status'], '?')
            print(f"  {icon} {log['name']}: {log['status']}")
            if 'reason' in log:
                print(f"      Reason: {log['reason']}")

        # Save log to file
        log_path = self.output_dir / 'download_log.json'
        with open(log_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': total,
                'successful': successful,
                'failed': failed,
                'elapsed_minutes': elapsed/60,
                'locations': self.download_log
            }, f, indent=2)
        print(f"\nLog saved to: {log_path}")


def load_locations(config_file):
    """Load locations from JSON config file"""
    with open(config_file) as f:
        data = json.load(f)
    return data['locations'], data.get('configuration', {})


def main():
    parser = argparse.ArgumentParser(
        description='Batch download Sentinel-2 imagery with cloud filtering'
    )
    parser.add_argument(
        '--config',
        default='locations_example.json',
        help='JSON config file with locations (default: locations_example.json)'
    )
    parser.add_argument(
        '--locations',
        nargs='+',
        help='Specific location names to download (space-separated)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all locations from config'
    )
    parser.add_argument(
        '--exclude',
        nargs='+',
        default=['newyork_manhattan', 'iowa_farmland', 'amazon_rainforest'],
        help='Locations to exclude (default: first 3 examples)'
    )
    parser.add_argument(
        '--max-cloud',
        type=int,
        help='Override cloud percentage threshold for all locations'
    )
    parser.add_argument(
        '--output-dir',
        default='downloads',
        help='Output directory for downloads (default: downloads)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip locations that already have downloaded files'
    )

    args = parser.parse_args()

    # Load config
    print("📂 Loading configuration...")
    try:
        all_locations, config = load_locations(args.config)
        print(f"   Found {len(all_locations)} locations in config")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        sys.exit(1)

    # Select locations to download
    if args.all:
        # Download all except excluded
        locations_to_download = [
            loc for loc in all_locations
            if loc['name'] not in args.exclude
        ]
        print(f"   Downloading all locations except: {', '.join(args.exclude)}")
    elif args.locations:
        # Download specific locations
        location_names = set(args.locations)
        locations_to_download = [
            loc for loc in all_locations
            if loc['name'] in location_names
        ]
        if len(locations_to_download) < len(location_names):
            found = {loc['name'] for loc in locations_to_download}
            missing = location_names - found
            print(f"   ⚠ Warning: Locations not found in config: {', '.join(missing)}")
    else:
        print("✗ Must specify either --all or --locations")
        parser.print_help()
        sys.exit(1)

    if not locations_to_download:
        print("✗ No locations selected for download")
        sys.exit(1)

    print(f"   Selected {len(locations_to_download)} locations:")
    for loc in locations_to_download:
        print(f"     - {loc['name']}: {loc.get('description', '')}")

    # Initialize downloader
    downloader = BatchDownloader(
        output_dir=args.output_dir,
        skip_existing=args.skip_existing
    )

    # Start batch download
    downloader.download_batch(locations_to_download, args.max_cloud)


if __name__ == '__main__':
    main()
