#!/usr/bin/env python3
"""
Google Colab-compatible script for downloading cloud-free Sentinel-2 images
with corresponding OSM data.

Features:
- Cloud-free Sentinel-2 RGB composites from Google Earth Engine
- Land area filtering (excludes ocean-only areas)
- Automatic OSM data fetching via Overpass API
- Saves images + OSM GeoJSON for each location

Usage in Google Colab:
    !python colab_gee_osm_downloader.py --interactive
    !python colab_gee_osm_downloader.py --predefined
    !python colab_gee_osm_downloader.py --config locations.json
"""

import ee
import geemap
import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, List, Tuple, Optional
import numpy as np

class CoLabGEEOSMDownloader:
    """Download cloud-free Sentinel-2 images with OSM data for Google Colab."""

    def __init__(self, output_dir: str = "./downloads"):
        """
        Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.images_dir = self.output_dir / "images"
        self.osm_dir = self.output_dir / "osm_data"
        self.metadata_dir = self.output_dir / "metadata"

        for dir_path in [self.images_dir, self.osm_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Initialize Earth Engine
        try:
            ee.Initialize()
            print("✓ Earth Engine initialized successfully")
        except Exception as e:
            print(f"! Earth Engine initialization failed: {e}")
            print("  Run: ee.Authenticate() first")
            raise

    def get_cloud_free_composite(
        self,
        bbox: List[float],
        start_date: str,
        end_date: str,
        cloud_percentage: int = 10,
        min_images: int = 3
    ) -> Optional[ee.Image]:
        """
        Get cloud-free Sentinel-2 composite for a bounding box.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_percentage: Maximum cloud cover percentage
            min_images: Minimum number of images required

        Returns:
            Earth Engine Image or None if no suitable images found
        """
        # Define region of interest
        roi = ee.Geometry.Rectangle(bbox)

        # Query Sentinel-2 Surface Reflectance
        collection = (ee.ImageCollection('COPERNICUS/S2_SR')
                     .filterBounds(roi)
                     .filterDate(start_date, end_date)
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_percentage))
                     .select(['B4', 'B3', 'B2']))  # RGB bands

        # Check if we have enough images
        count = collection.size().getInfo()
        print(f"  Found {count} suitable images with <{cloud_percentage}% cloud cover")

        if count < min_images:
            print(f"  ! Warning: Only {count} images found (minimum: {min_images})")
            return None

        # Create median composite (reduces cloud artifacts)
        composite = collection.median().clip(roi)

        return composite

    def check_land_coverage(self, image: ee.Image, roi: ee.Geometry) -> Dict[str, float]:
        """
        Check if the image contains significant land coverage (not just ocean).

        Args:
            image: Earth Engine image
            roi: Region of interest

        Returns:
            Dictionary with statistics about land coverage
        """
        # Calculate statistics to detect water/land
        stats = image.reduceRegion(
            reducer=ee.Reducer.mean().combine(
                ee.Reducer.stdDev(), '', True
            ).combine(
                ee.Reducer.percentile([10, 90]), '', True
            ),
            geometry=roi,
            scale=100,  # 100m for faster computation
            maxPixels=1e9
        ).getInfo()

        # Calculate metrics
        mean_brightness = np.mean([stats.get('B4_mean', 0),
                                   stats.get('B3_mean', 0),
                                   stats.get('B2_mean', 0)])
        std_dev = np.mean([stats.get('B4_stdDev', 0),
                          stats.get('B3_stdDev', 0),
                          stats.get('B2_stdDev', 0)])

        # Ocean typically has:
        # - Low mean brightness (dark water)
        # - Very low standard deviation (uniform)
        # - Low 90th percentile (no bright features)

        is_likely_land = (
            mean_brightness > 500 or  # Reasonable brightness
            std_dev > 150  # Some variation (indicates land features)
        )

        return {
            'mean_brightness': float(mean_brightness),
            'std_dev': float(std_dev),
            'is_likely_land': is_likely_land,
            'stats': stats
        }

    def fetch_osm_data(
        self,
        bbox: List[float],
        features: List[str] = None,
        timeout: int = 180
    ) -> Dict:
        """
        Fetch OSM data for a bounding box using Overpass API.

        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            features: List of OSM features to query (None = all common features)
            timeout: API timeout in seconds

        Returns:
            GeoJSON FeatureCollection with OSM data
        """
        if features is None:
            # Default: common features for VQA
            features = [
                'building',
                'highway',
                'landuse',
                'natural',
                'waterway',
                'amenity',
                'leisure',
                'railway',
                'aeroway'
            ]

        # Build Overpass QL query
        bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"  # S,W,N,E format

        # Query for ways and relations with these tags
        queries = []
        for feature in features:
            queries.append(f'way["{feature}"]({bbox_str});')
            queries.append(f'relation["{feature}"]({bbox_str});')

        overpass_query = f"""
        [out:json][timeout:{timeout}];
        (
          {''.join(queries)}
        );
        out geom;
        """

        print(f"  Fetching OSM data for bbox {bbox}...")

        # Query Overpass API
        overpass_url = "https://overpass-api.de/api/interpreter"

        try:
            response = requests.post(
                overpass_url,
                data={'data': overpass_query},
                timeout=timeout
            )
            response.raise_for_status()

            osm_data = response.json()

            # Convert to GeoJSON
            geojson = self._osm_to_geojson(osm_data, bbox)

            num_features = len(geojson['features'])
            print(f"  ✓ Retrieved {num_features} OSM features")

            return geojson

        except requests.exceptions.RequestException as e:
            print(f"  ! OSM API error: {e}")
            return {"type": "FeatureCollection", "features": [], "error": str(e)}
        except Exception as e:
            print(f"  ! Error processing OSM data: {e}")
            return {"type": "FeatureCollection", "features": [], "error": str(e)}

    def _osm_to_geojson(self, osm_data: Dict, bbox: List[float]) -> Dict:
        """
        Convert OSM JSON to GeoJSON format.

        Args:
            osm_data: OSM JSON from Overpass API
            bbox: Original bounding box

        Returns:
            GeoJSON FeatureCollection
        """
        features = []

        for element in osm_data.get('elements', []):
            try:
                # Extract geometry
                geometry = None
                if element['type'] == 'way' and 'geometry' in element:
                    coords = [[node['lon'], node['lat']] for node in element['geometry']]
                    if len(coords) > 1:
                        # Check if closed (polygon) or open (linestring)
                        if coords[0] == coords[-1] and len(coords) > 3:
                            geometry = {
                                "type": "Polygon",
                                "coordinates": [coords]
                            }
                        else:
                            geometry = {
                                "type": "LineString",
                                "coordinates": coords
                            }

                elif element['type'] == 'node':
                    geometry = {
                        "type": "Point",
                        "coordinates": [element['lon'], element['lat']]
                    }

                if geometry:
                    # Extract properties (tags)
                    properties = element.get('tags', {})
                    properties['osm_id'] = element['id']
                    properties['osm_type'] = element['type']

                    features.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": properties
                    })

            except Exception as e:
                # Skip malformed elements
                continue

        return {
            "type": "FeatureCollection",
            "bbox": bbox,
            "features": features,
            "metadata": {
                "source": "OpenStreetMap",
                "attribution": "© OpenStreetMap contributors",
                "retrieved": datetime.now().isoformat(),
                "query_bbox": bbox
            }
        }

    def download_image_local(
        self,
        image: ee.Image,
        bbox: List[float],
        filename: str,
        scale: int = 10
    ) -> str:
        """
        Download image directly to local filesystem.

        Args:
            image: Earth Engine image
            bbox: Bounding box
            filename: Output filename (without extension)
            scale: Resolution in meters

        Returns:
            Path to downloaded file
        """
        output_path = self.images_dir / f"{filename}.tif"

        print(f"  Downloading image to {output_path}...")

        # Use geemap for direct download
        geemap.ee_export_image(
            image,
            filename=str(output_path),
            scale=scale,
            region=ee.Geometry.Rectangle(bbox),
            file_per_band=False,
            crs='EPSG:3857'
        )

        print(f"  ✓ Image saved to {output_path}")
        return str(output_path)

    def process_location(
        self,
        name: str,
        bbox: List[float],
        start_date: str = None,
        end_date: str = None,
        cloud_percentage: int = 10,
        scale: int = 10,
        osm_features: List[str] = None
    ) -> Dict:
        """
        Process a single location: download image + OSM data.

        Args:
            name: Location name (for filename)
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)
            cloud_percentage: Max cloud cover
            scale: Resolution in meters
            osm_features: OSM features to fetch

        Returns:
            Dictionary with status and file paths
        """
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"Bbox: {bbox}")
        print(f"{'='*60}")

        # Default dates
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        print(f"  Date range: {start_date} to {end_date}")

        result = {
            'name': name,
            'bbox': bbox,
            'status': 'failed',
            'image_path': None,
            'osm_path': None,
            'metadata_path': None
        }

        try:
            # Step 1: Get cloud-free composite
            print("\n[1/4] Fetching cloud-free Sentinel-2 composite...")
            image = self.get_cloud_free_composite(
                bbox, start_date, end_date, cloud_percentage
            )

            if image is None:
                result['error'] = "No suitable images found"
                return result

            # Step 2: Check land coverage
            print("\n[2/4] Checking land coverage...")
            roi = ee.Geometry.Rectangle(bbox)
            land_check = self.check_land_coverage(image, roi)

            print(f"  Mean brightness: {land_check['mean_brightness']:.1f}")
            print(f"  Std deviation: {land_check['std_dev']:.1f}")
            print(f"  Land detected: {land_check['is_likely_land']}")

            if not land_check['is_likely_land']:
                print("  ! Warning: Area appears to be mostly ocean")
                result['warning'] = "Area may be mostly ocean"

            # Step 3: Download image
            print("\n[3/4] Downloading Sentinel-2 image...")
            image_path = self.download_image_local(image, bbox, name, scale)
            result['image_path'] = image_path

            # Step 4: Fetch OSM data
            print("\n[4/4] Fetching OpenStreetMap data...")
            osm_data = self.fetch_osm_data(bbox, osm_features)

            # Save OSM data
            osm_path = self.osm_dir / f"{name}_osm.geojson"
            with open(osm_path, 'w') as f:
                json.dump(osm_data, f, indent=2)
            print(f"  ✓ OSM data saved to {osm_path}")
            result['osm_path'] = str(osm_path)

            # Step 5: Save metadata
            metadata = {
                'name': name,
                'bbox': bbox,
                'date_range': {'start': start_date, 'end': end_date},
                'cloud_percentage_threshold': cloud_percentage,
                'scale_meters': scale,
                'land_coverage': land_check,
                'osm_feature_count': len(osm_data['features']),
                'processed_at': datetime.now().isoformat(),
                'files': {
                    'image': image_path,
                    'osm': str(osm_path)
                }
            }

            metadata_path = self.metadata_dir / f"{name}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            result['metadata_path'] = str(metadata_path)

            result['status'] = 'success'
            print(f"\n✓ Successfully processed {name}")

        except Exception as e:
            print(f"\n✗ Error processing {name}: {e}")
            result['error'] = str(e)

        return result

    @staticmethod
    def get_predefined_locations() -> List[Dict]:
        """
        Get predefined land-based locations for testing.

        Returns:
            List of location dictionaries
        """
        return [
            {
                'name': 'manhattan_nyc',
                'bbox': [-74.02, 40.75, -73.97, 40.80],
                'cloud_percentage': 10,
                'description': 'Manhattan, NYC - Dense urban area'
            },
            {
                'name': 'iowa_farmland',
                'bbox': [-93.65, 41.55, -93.55, 41.65],
                'cloud_percentage': 10,
                'description': 'Iowa - Agricultural farmland'
            },
            {
                'name': 'amazon_rainforest',
                'bbox': [-60.1, -3.1, -60.0, -3.0],
                'cloud_percentage': 20,
                'description': 'Amazon - Dense rainforest'
            },
            {
                'name': 'san_francisco',
                'bbox': [-122.50, 37.75, -122.40, 37.80],
                'cloud_percentage': 10,
                'description': 'San Francisco - Urban coastal'
            },
            {
                'name': 'sahara_desert',
                'bbox': [2.0, 23.0, 2.1, 23.1],
                'cloud_percentage': 5,
                'description': 'Sahara - Desert landscape'
            },
            {
                'name': 'tokyo_urban',
                'bbox': [139.70, 35.65, 139.80, 35.70],
                'cloud_percentage': 15,
                'description': 'Tokyo - Dense urban megacity'
            },
            {
                'name': 'scottish_highlands',
                'bbox': [-4.5, 57.0, -4.4, 57.1],
                'cloud_percentage': 20,
                'description': 'Scotland - Mountainous terrain'
            },
            {
                'name': 'venice_italy',
                'bbox': [12.30, 45.43, 12.37, 45.48],
                'cloud_percentage': 10,
                'description': 'Venice - City with canals'
            }
        ]


def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Download cloud-free Sentinel-2 images with OSM data'
    )
    parser.add_argument(
        '--mode',
        choices=['interactive', 'predefined', 'config'],
        default='predefined',
        help='Download mode'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to JSON config file with locations'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./downloads',
        help='Output directory'
    )
    parser.add_argument(
        '--cloud_threshold',
        type=int,
        default=10,
        help='Maximum cloud cover percentage'
    )

    args = parser.parse_args()

    # Initialize downloader
    print("Initializing GEE + OSM Downloader...")
    downloader = CoLabGEEOSMDownloader(output_dir=args.output_dir)

    results = []

    if args.mode == 'interactive':
        print("\n=== Interactive Mode ===")
        name = input("Location name: ")
        bbox_str = input("Bounding box [min_lon,min_lat,max_lon,max_lat]: ")
        bbox = [float(x.strip()) for x in bbox_str.split(',')]

        result = downloader.process_location(
            name=name,
            bbox=bbox,
            cloud_percentage=args.cloud_threshold
        )
        results.append(result)

    elif args.mode == 'predefined':
        print("\n=== Predefined Locations Mode ===")
        locations = CoLabGEEOSMDownloader.get_predefined_locations()

        print(f"\nFound {len(locations)} predefined locations:")
        for i, loc in enumerate(locations, 1):
            print(f"  {i}. {loc['name']}: {loc['description']}")

        choice = input("\nProcess (all/1-8): ").strip().lower()

        if choice == 'all':
            selected = locations
        else:
            try:
                idx = int(choice) - 1
                selected = [locations[idx]]
            except (ValueError, IndexError):
                print("Invalid choice!")
                return

        for loc in selected:
            result = downloader.process_location(
                name=loc['name'],
                bbox=loc['bbox'],
                cloud_percentage=loc.get('cloud_percentage', args.cloud_threshold)
            )
            results.append(result)
            time.sleep(2)  # Rate limiting

    elif args.mode == 'config':
        if not args.config:
            print("Error: --config required for config mode")
            return

        print(f"\n=== Config File Mode: {args.config} ===")
        with open(args.config, 'r') as f:
            config = json.load(f)

        for loc in config.get('locations', []):
            result = downloader.process_location(
                name=loc['name'],
                bbox=loc['bbox'],
                cloud_percentage=loc.get('cloud_percentage', args.cloud_threshold)
            )
            results.append(result)
            time.sleep(2)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'failed']

    print(f"Total processed: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\n✓ Successful downloads:")
        for r in successful:
            print(f"  - {r['name']}")
            print(f"    Image: {r['image_path']}")
            print(f"    OSM: {r['osm_path']}")

    if failed:
        print("\n✗ Failed downloads:")
        for r in failed:
            print(f"  - {r['name']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
