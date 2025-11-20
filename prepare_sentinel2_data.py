#!/usr/bin/env python3
"""
Sentinel-2 Data Preparation Script for Custom RSVQA Dataset

This script helps prepare Sentinel-2 imagery downloaded from Google Earth Engine
for RSVQA training. It handles:
1. Image tiling (256x256 patches)
2. Quality filtering
3. Coordinate tracking
4. JSON file generation template

Usage:
    python prepare_sentinel2_data.py --input_dir /path/to/sentinel2 --output_dir /path/to/output

Requirements:
    pip install rasterio numpy pillow tqdm
"""

import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np
import rasterio
from rasterio.windows import Window
from tqdm import tqdm


class Sentinel2Preprocessor:
    """Preprocessor for Sentinel-2 imagery for RSVQA"""

    def __init__(self, patch_size=256, min_mean=30, max_mean=225):
        """
        Args:
            patch_size: Size of image patches (default: 256 for Sentinel-2)
            min_mean: Minimum mean pixel value (default: 30)
            max_mean: Maximum mean pixel value (default: 225)
        """
        self.patch_size = patch_size
        self.min_mean = min_mean
        self.max_mean = max_mean

    def check_image_quality(self, img_array):
        """
        Check if image meets quality criteria

        Args:
            img_array: numpy array of shape (channels, height, width)

        Returns:
            bool: True if image passes quality checks
        """
        # Check dimensions
        if img_array.shape[1] != self.patch_size or img_array.shape[2] != self.patch_size:
            return False

        # Check mean pixel value
        mean_value = np.mean(img_array)
        if mean_value < self.min_mean or mean_value > self.max_mean:
            return False

        # Check for NaN or invalid values
        if np.any(np.isnan(img_array)) or np.any(np.isinf(img_array)):
            return False

        return True

    def tile_image(self, input_path, output_dir, image_id_start=1):
        """
        Tile a large Sentinel-2 image into 256x256 patches

        Args:
            input_path: Path to input GeoTIFF
            output_dir: Directory to save tiles
            image_id_start: Starting ID for tiles

        Returns:
            list: List of dictionaries with tile metadata
        """
        tiles_metadata = []
        tile_id = image_id_start

        with rasterio.open(input_path) as src:
            # Get image dimensions
            width = src.width
            height = src.height

            # Calculate number of tiles
            n_cols = width // self.patch_size
            n_rows = height // self.patch_size

            print(f"Processing {input_path}")
            print(f"Image size: {width}x{height}")
            print(f"Creating {n_cols * n_rows} tiles...")

            # Create tiles with sliding window
            for row in tqdm(range(n_rows), desc="Rows"):
                for col in range(n_cols):
                    # Calculate window
                    x_offset = col * self.patch_size
                    y_offset = row * self.patch_size

                    # Read window
                    window = Window(x_offset, y_offset, self.patch_size, self.patch_size)
                    tile_data = src.read(window=window)

                    # Check quality
                    if not self.check_image_quality(tile_data):
                        continue

                    # Get geographic coordinates of upper-left corner
                    transform = src.window_transform(window)
                    upperleft_x, upperleft_y = transform * (0, 0)

                    # Generate output filename
                    base_name = Path(input_path).stem
                    tile_filename = f"{base_name}_tile_{tile_id:05d}.tif"
                    tile_path = os.path.join(output_dir, tile_filename)

                    # Save tile with georeferencing
                    profile = src.profile.copy()
                    profile.update({
                        'height': self.patch_size,
                        'width': self.patch_size,
                        'transform': transform,
                        'dtype': 'uint8',
                        'count': 3  # RGB only
                    })

                    with rasterio.open(tile_path, 'w', **profile) as dst:
                        # Ensure uint8 format
                        if tile_data.dtype != np.uint8:
                            # Normalize to 0-255 if needed
                            tile_data = np.clip(tile_data, 0, 255).astype(np.uint8)
                        dst.write(tile_data)

                    # Store metadata
                    tile_metadata = {
                        'id': tile_id,
                        'filename': tile_filename,
                        'original_name': base_name,
                        'upperleft_map_x': float(upperleft_x),
                        'upperleft_map_y': float(upperleft_y),
                        'res_x': float(src.res[0]),
                        'res_y': float(src.res[1]),
                        'crs': str(src.crs),
                        'row': row,
                        'col': col
                    }
                    tiles_metadata.append(tile_metadata)

                    tile_id += 1

        print(f"Created {len(tiles_metadata)} valid tiles")
        return tiles_metadata

    def create_images_json(self, tiles_metadata, output_path):
        """
        Create images.json file for RSVQA

        Args:
            tiles_metadata: List of tile metadata dictionaries
            output_path: Path to save images.json
        """
        timestamp = int(datetime.now().timestamp())

        images_data = {
            "images": []
        }

        for tile in tiles_metadata:
            image_entry = {
                "id": tile['id'],
                "date_added": timestamp,
                "original_name": tile['filename'],
                "sensor": "Sentinel-2",
                "upperleft_map_x": tile['upperleft_map_x'],
                "upperleft_map_y": tile['upperleft_map_y'],
                "res_x": tile['res_x'],
                "res_y": tile['res_y'],
                "people_id": 1,
                "type": "Multispectral",
                "questions_ids": [],  # To be filled during annotation
                "active": True
            }
            images_data["images"].append(image_entry)

        with open(output_path, 'w') as f:
            json.dump(images_data, f, indent=2)

        print(f"Saved images.json to {output_path}")

    def create_annotation_templates(self, output_dir):
        """
        Create template JSON files for annotation

        Args:
            output_dir: Directory to save template files
        """
        # Questions template
        questions_template = {
            "questions": [
                {
                    "id": 1,
                    "date_added": int(datetime.now().timestamp()),
                    "img_id": 1,
                    "people_id": 1,
                    "type": "presence",
                    "question": "Is there a building?",
                    "answers_ids": [1],
                    "active": True
                },
                {
                    "id": 2,
                    "date_added": int(datetime.now().timestamp()),
                    "img_id": 1,
                    "people_id": 1,
                    "type": "count",
                    "question": "How many buildings are there?",
                    "answers_ids": [2],
                    "active": True
                }
            ]
        }

        # Answers template
        answers_template = {
            "answers": [
                {
                    "id": 1,
                    "date_added": int(datetime.now().timestamp()),
                    "question_id": 1,
                    "people_id": 1,
                    "answer": "yes",
                    "active": True
                },
                {
                    "id": 2,
                    "date_added": int(datetime.now().timestamp()),
                    "question_id": 2,
                    "people_id": 1,
                    "answer": "between 10 and 50",
                    "active": True
                }
            ]
        }

        # Save templates
        questions_path = os.path.join(output_dir, "questions_template.json")
        answers_path = os.path.join(output_dir, "answers_template.json")

        with open(questions_path, 'w') as f:
            json.dump(questions_template, f, indent=2)

        with open(answers_path, 'w') as f:
            json.dump(answers_template, f, indent=2)

        print(f"Created annotation templates in {output_dir}")


def process_directory(input_dir, output_dir, patch_size=256):
    """
    Process all GeoTIFF files in a directory

    Args:
        input_dir: Directory containing Sentinel-2 GeoTIFFs
        output_dir: Directory to save processed tiles
        patch_size: Size of tiles (default: 256)
    """
    # Create output directories
    tiles_dir = os.path.join(output_dir, 'images')
    os.makedirs(tiles_dir, exist_ok=True)

    # Initialize preprocessor
    preprocessor = Sentinel2Preprocessor(patch_size=patch_size)

    # Find all GeoTIFF files
    input_path = Path(input_dir)
    geotiff_files = list(input_path.glob('*.tif')) + list(input_path.glob('*.tiff'))

    if not geotiff_files:
        print(f"No GeoTIFF files found in {input_dir}")
        return

    print(f"Found {len(geotiff_files)} GeoTIFF files")

    # Process each file
    all_tiles_metadata = []
    tile_id = 1

    for geotiff_path in geotiff_files:
        tiles_metadata = preprocessor.tile_image(
            str(geotiff_path),
            tiles_dir,
            image_id_start=tile_id
        )
        all_tiles_metadata.extend(tiles_metadata)
        tile_id += len(tiles_metadata)

    # Create JSON files
    images_json_path = os.path.join(output_dir, 'images.json')
    preprocessor.create_images_json(all_tiles_metadata, images_json_path)

    # Create annotation templates
    preprocessor.create_annotation_templates(output_dir)

    # Save metadata CSV for reference
    metadata_csv_path = os.path.join(output_dir, 'tiles_metadata.csv')
    with open(metadata_csv_path, 'w') as f:
        f.write('tile_id,filename,original_name,upperleft_x,upperleft_y,res_x,res_y,crs,row,col\n')
        for tile in all_tiles_metadata:
            f.write(f"{tile['id']},{tile['filename']},{tile['original_name']},"
                   f"{tile['upperleft_map_x']},{tile['upperleft_map_y']},"
                   f"{tile['res_x']},{tile['res_y']},{tile['crs']},"
                   f"{tile['row']},{tile['col']}\n")

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"{'='*60}")
    print(f"Total tiles created: {len(all_tiles_metadata)}")
    print(f"Output directory: {output_dir}")
    print(f"\nNext steps:")
    print(f"1. Review tiles in: {tiles_dir}")
    print(f"2. Start annotation using: {images_json_path}")
    print(f"3. Refer to ANNOTATION_GUIDE.md for detailed instructions")


def main():
    parser = argparse.ArgumentParser(
        description='Prepare Sentinel-2 imagery for RSVQA training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Process all GeoTIFFs in a directory
    python prepare_sentinel2_data.py --input_dir ./sentinel2_downloads --output_dir ./dataset

    # Use custom patch size (though 256 is recommended for Sentinel-2)
    python prepare_sentinel2_data.py --input_dir ./data --output_dir ./output --patch_size 256

For detailed annotation instructions, see ANNOTATION_GUIDE.md
        """
    )

    parser.add_argument('--input_dir', type=str, required=True,
                       help='Directory containing Sentinel-2 GeoTIFF files')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Directory to save processed tiles and JSON files')
    parser.add_argument('--patch_size', type=int, default=256,
                       help='Size of image patches (default: 256 for Sentinel-2)')

    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory does not exist: {args.input_dir}")
        return

    # Process
    process_directory(args.input_dir, args.output_dir, args.patch_size)


if __name__ == '__main__':
    main()
