#!/usr/bin/env python3
"""
Simplified Custom Location Downloader

Downloads Sentinel-2 imagery for all custom locations in locations_extended.json
Features:
- Automatic dependency checking
- Clear error messages
- Resume capability
- Quality assessment
- Progress tracking

Usage:
    python3 download_custom_locations.py
"""

import sys
import json
from pathlib import Path
import time
from datetime import datetime

# Check for required packages
try:
    import ee
    import geemap
    import numpy as np
    from PIL import Image
except ImportError as e:
    print("❌ Missing required package!")
    print(f"Error: {e}")
    print("\nPlease run setup first:")
    print("  bash setup_download_environment.sh")
    sys.exit(1)


class CustomLocationDownloader:
    """Simple downloader for custom locations"""

    def __init__(self, output_dir="custom_imagery"):
        """Initialize downloader"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

        # Initialize Google Earth Engine
        print("🌍 Initializing Google Earth Engine...")
        try:
            ee.Initialize()
            print("✓ Connected to Google Earth Engine\n")
        except Exception as e:
            print("❌ Failed to initialize Google Earth Engine")
            print("\nPlease authenticate first:")
            print("  earthengine authenticate")
            print("\nThen run this script again.")
            sys.exit(1)

    def get_cloud_free_image(self, bbox, start_date, end_date,
                             max_cloud=10, name=""):
        """Get cloud-free Sentinel-2 composite"""

        print(f"  📡 Searching for imagery...")
        print(f"     Date range: {start_date} to {end_date}")
        print(f"     Max cloud: {max_cloud}%")

        # Create region of interest
        roi = ee.Geometry.Rectangle(bbox)

        # Query Sentinel-2 collection
        collection = ee.ImageCollection('COPERNICUS/S2_SR') \
            .filterBounds(roi) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud))

        count = collection.size().getInfo()
        print(f"     Found {count} images")

        if count == 0:
            # Try with higher cloud threshold
            print(f"  🔄 Retrying with 20% cloud threshold...")
            collection = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterBounds(roi) \
                .filterDate(start_date, end_date) \
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            count = collection.size().getInfo()
            print(f"     Found {count} images")

            if count == 0:
                return None

        # Apply cloud masking
        def mask_clouds(image):
            scl = image.select('SCL')
            # Mask clouds, cloud shadows, and cirrus
            mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            return image.updateMask(mask)

        # Create median composite
        composite = collection.map(mask_clouds) \
                             .select(['B4', 'B3', 'B2']) \
                             .median() \
                             .clip(roi)

        # Visualize for RGB
        composite = composite.visualize(min=0, max=3000, gamma=1.4)

        print(f"     ✓ Composite created")
        return composite, roi

    def assess_quality(self, image_path):
        """Quick quality check"""
        try:
            img = Image.open(image_path)
            arr = np.array(img)

            mean_val = np.mean(arr)
            black_pct = np.sum(arr == 0) / arr.size * 100

            print(f"  📊 Quality: mean={mean_val:.1f}, black={black_pct:.1f}%")

            if mean_val < 20 or black_pct > 30:
                print(f"     ⚠ Quality warning (too dark or missing data)")
                return False
            else:
                print(f"     ✓ Quality looks good")
                return True
        except Exception as e:
            print(f"     ⚠ Could not assess quality: {e}")
            return False

    def download_location(self, location):
        """Download a single location"""

        name = location['name']
        description = location.get('description', '')

        output_path = self.output_dir / f"{name}.tif"

        # Skip if already exists
        if output_path.exists():
            print(f"⏭️  Skipping {name} (already downloaded)")
            self.results.append({
                'name': name,
                'status': 'skipped',
                'file': str(output_path)
            })
            return True

        print(f"\n{'='*70}")
        print(f"📍 {name}")
        print(f"   {description}")
        print(f"{'='*70}")

        try:
            # Get cloud-free composite
            result = self.get_cloud_free_image(
                bbox=location['bbox'],
                start_date=location['start_date'],
                end_date=location['end_date'],
                max_cloud=location.get('cloud_percentage', 10),
                name=name
            )

            if result is None:
                print(f"  ❌ No images found for {name}")
                self.results.append({
                    'name': name,
                    'status': 'failed',
                    'reason': 'no_images'
                })
                return False

            composite, roi = result

            # Download
            print(f"  💾 Downloading...")
            geemap.ee_export_image(
                composite,
                filename=str(output_path),
                scale=10,
                region=roi,
                file_per_band=False
            )

            print(f"  ✓ Saved to: {output_path}")

            # Quality check
            quality_ok = self.assess_quality(output_path)

            self.results.append({
                'name': name,
                'status': 'success',
                'file': str(output_path),
                'quality': 'good' if quality_ok else 'warning'
            })

            return True

        except Exception as e:
            print(f"  ❌ Error downloading {name}: {e}")
            self.results.append({
                'name': name,
                'status': 'error',
                'reason': str(e)
            })
            return False

    def download_all(self, locations):
        """Download all locations"""

        total = len(locations)
        print(f"\n🚀 Starting download of {total} locations")
        print(f"   Output: {self.output_dir}/")
        print()

        start_time = time.time()
        success_count = 0

        for idx, location in enumerate(locations, 1):
            print(f"\n[{idx}/{total}]", end=" ")

            if self.download_location(location):
                success_count += 1

            # Pause between downloads
            if idx < total:
                time.sleep(2)

        # Summary
        elapsed = time.time() - start_time
        failed = total - success_count

        print(f"\n{'='*70}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*70}")
        print(f"Total: {total}")
        print(f"✓ Successful: {success_count}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")

        # Detailed results
        print(f"\nDetailed results:")
        for result in self.results:
            status = result['status']
            icon = {'success': '✓', 'failed': '❌', 'error': '❌', 'skipped': '⏭️'}
            print(f"  {icon.get(status, '?')} {result['name']}: {status}")
            if 'reason' in result:
                print(f"      Reason: {result['reason']}")

        # Save log
        log_path = self.output_dir / 'download_log.json'
        with open(log_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total': total,
                'successful': success_count,
                'failed': failed,
                'elapsed_minutes': elapsed/60,
                'results': self.results
            }, f, indent=2)

        print(f"\n💾 Log saved to: {log_path}")

        return success_count, failed


def load_custom_locations():
    """Load custom locations from config"""

    config_file = Path('locations_extended.json')

    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        print("Make sure you're running this from the repository root.")
        sys.exit(1)

    with open(config_file) as f:
        data = json.load(f)

    all_locations = data['locations']

    # Skip the first 3 example locations
    exclude = ['newyork_manhattan', 'iowa_farmland', 'amazon_rainforest']
    custom_locations = [
        loc for loc in all_locations
        if loc['name'] not in exclude
    ]

    print(f"📂 Loaded {len(custom_locations)} custom locations")
    print(f"   (Excluded {len(exclude)} example locations)")

    return custom_locations


def main():
    """Main download function"""

    print("=" * 70)
    print("Custom Location Imagery Downloader")
    print("=" * 70)
    print()

    # Load locations
    locations = load_custom_locations()

    print(f"\nLocations to download:")
    for i, loc in enumerate(locations, 1):
        print(f"  {i:2d}. {loc['name']:25s} - {loc.get('description', '')}")

    print()
    input("Press ENTER to start downloading (or Ctrl+C to cancel)...")

    # Download
    downloader = CustomLocationDownloader()
    success, failed = downloader.download_all(locations)

    print("\n" + "=" * 70)
    if failed == 0:
        print("🎉 All downloads completed successfully!")
    else:
        print(f"⚠️  Completed with {failed} failures")
        print("   You can re-run this script to retry failed downloads")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Download cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
