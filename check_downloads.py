#!/usr/bin/env python3
"""
Check Downloaded Locations Status

This script checks which locations have been downloaded and provides
recommendations for additional downloads to improve dataset diversity.

Usage:
    python check_downloads.py
    python check_downloads.py --config locations_extended.json
"""

import json
import argparse
from pathlib import Path
from PIL import Image
import numpy as np


def check_downloads(config_file, download_dir):
    """Check status of downloaded locations"""

    # Load configuration
    try:
        with open(config_file) as f:
            data = json.load(f)
        locations = data['locations']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    download_path = Path(download_dir)

    # Categorize locations
    downloaded = []
    not_downloaded = []
    categories = {}

    print(f"\n{'='*70}")
    print(f"DOWNLOAD STATUS CHECK")
    print(f"{'='*70}\n")
    print(f"Config file: {config_file}")
    print(f"Download directory: {download_dir}")
    print(f"Total locations in config: {len(locations)}\n")

    # Check each location
    for loc in locations:
        name = loc['name']
        file_path = download_path / f"{name}.tif"
        category = loc.get('category', 'uncategorized')

        if category not in categories:
            categories[category] = {'downloaded': 0, 'total': 0}
        categories[category]['total'] += 1

        if file_path.exists():
            # Get file size
            size_mb = file_path.stat().st_size / (1024 * 1024)

            # Quick quality check
            try:
                img = Image.open(file_path)
                img_array = np.array(img)
                mean_val = np.mean(img_array)
                quality = "✓ Good" if 30 < mean_val < 225 else "⚠ Check"
            except:
                quality = "? Unknown"

            downloaded.append({
                'name': name,
                'category': category,
                'size_mb': size_mb,
                'quality': quality
            })
            categories[category]['downloaded'] += 1
        else:
            not_downloaded.append({
                'name': name,
                'category': category,
                'description': loc.get('description', ''),
                'cloud_pct': loc.get('cloud_percentage', 10)
            })

    # Print downloaded locations
    print(f"{'='*70}")
    print(f"DOWNLOADED LOCATIONS ({len(downloaded)})")
    print(f"{'='*70}\n")

    if downloaded:
        for loc in downloaded:
            print(f"✓ {loc['name']:<25} [{loc['category']:<20}] "
                  f"{loc['size_mb']:>6.1f} MB  {loc['quality']}")
    else:
        print("No locations downloaded yet.")

    # Print not downloaded locations
    print(f"\n{'='*70}")
    print(f"NOT DOWNLOADED ({len(not_downloaded)})")
    print(f"{'='*70}\n")

    if not_downloaded:
        for loc in not_downloaded:
            print(f"○ {loc['name']:<25} [{loc['category']:<20}] "
                  f"Cloud: {loc['cloud_pct']}%")
            print(f"  {loc['description']}")
    else:
        print("All locations downloaded!")

    # Category breakdown
    print(f"\n{'='*70}")
    print(f"CATEGORY BREAKDOWN")
    print(f"{'='*70}\n")

    for cat, stats in sorted(categories.items()):
        pct = (stats['downloaded'] / stats['total'] * 100) if stats['total'] > 0 else 0
        bar_length = 20
        filled = int(bar_length * pct / 100)
        bar = '█' * filled + '░' * (bar_length - filled)

        print(f"{cat:<25} {bar} {stats['downloaded']}/{stats['total']} "
              f"({pct:.0f}%)")

    # Recommendations
    print(f"\n{'='*70}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*70}\n")

    # Check diversity
    total_downloaded = len(downloaded)

    if total_downloaded == 0:
        print("📥 START HERE:")
        print("   Run: python batch_download_locations.py --all")
        print("   This will download the 5 remaining core locations.")
    elif total_downloaded < 8:
        print("📥 BASIC DIVERSITY (8 locations recommended):")
        print("   You have downloaded %d locations." % total_downloaded)
        print("   Download %d more for basic diversity." % (8 - total_downloaded))
        print("\n   Suggested locations:")

        # Recommend locations from different categories
        recommended = []
        for loc in not_downloaded[:5]:
            recommended.append(f"   - {loc['name']} ({loc['category']})")
        print('\n'.join(recommended))

        print(f"\n   Quick command:")
        names = [loc['name'] for loc in not_downloaded[:5]]
        print(f"   python batch_download_locations.py --locations {' '.join(names)}")

    elif total_downloaded < 12:
        print("📊 GOOD PROGRESS!")
        print("   You have a basic diverse set.")
        print("   Consider adding 4-7 more locations for global coverage.")
        print("\n   Recommended additions:")

        # Find missing categories
        missing_cats = [cat for cat, stats in categories.items()
                       if stats['downloaded'] == 0]

        if missing_cats:
            print(f"\n   Missing categories: {', '.join(missing_cats)}")
            for cat in missing_cats[:3]:
                locs = [loc for loc in not_downloaded if loc['category'] == cat]
                if locs:
                    print(f"   - {locs[0]['name']} ({cat})")
    else:
        print("🎉 EXCELLENT DIVERSITY!")
        print("   You have downloaded %d locations." % total_downloaded)
        print("   This is sufficient for training a robust VQA model.")

        if not_downloaded:
            print(f"\n   Optional: Add {len(not_downloaded)} more for even more diversity")

    # Cloud filtering tips
    print(f"\n{'='*70}")
    print(f"CLOUD FILTERING NOTES")
    print(f"{'='*70}\n")

    print("Current implementation uses 3-layer filtering:")
    print("  1. Metadata filter: CLOUDY_PIXEL_PERCENTAGE < threshold")
    print("  2. SCL masking: Removes cloud shadows and cloud pixels")
    print("  3. Median composite: Eliminates remaining outliers")
    print("\nIf downloads fail due to clouds, try:")
    print("  - Increase threshold: --max-cloud 20")
    print("  - Use extended config with optimized date ranges")

    # Next steps
    print(f"\n{'='*70}")
    print(f"NEXT STEPS")
    print(f"{'='*70}\n")

    if downloaded:
        print("1. Verify image quality:")
        print(f"   Open {download_dir}/{downloaded[0]['name']}.tif in QGIS")
        print("\n2. Preprocess for training:")
        print("   python prepare_sentinel2_data.py")
        print("\n3. Generate VQA annotations:")
        print("   python annotation_helper.py")
    else:
        print("1. Authenticate with Google Earth Engine:")
        print("   earthengine authenticate")
        print("\n2. Download your first location:")
        print("   python download_california_coast.py")
        print("\n3. Or batch download:")
        print("   python batch_download_locations.py --all")


def main():
    parser = argparse.ArgumentParser(
        description='Check downloaded locations status'
    )
    parser.add_argument(
        '--config',
        default='locations_example.json',
        help='Config file to check (default: locations_example.json)'
    )
    parser.add_argument(
        '--download-dir',
        default='downloads',
        help='Download directory (default: downloads)'
    )

    args = parser.parse_args()
    check_downloads(args.config, args.download_dir)


if __name__ == '__main__':
    main()
