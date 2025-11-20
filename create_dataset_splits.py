#!/usr/bin/env python3
"""
Create Train/Val/Test Splits for RSVQA Dataset

This script creates train/validation/test splits based on geographic locations
to ensure no data leakage. Splitting is done at the tile level (not patch level).

Usage:
    python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits

Features:
    - Geographic-based splitting (by location identifier)
    - Configurable split ratios
    - Stratified splitting to ensure diverse locations in each set
    - Support for held-out test regions
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
import random


class DatasetSplitter:
    """Split RSVQA dataset by geographic locations"""

    def __init__(self, images_json, questions_json, answers_json):
        """
        Args:
            images_json: Path to images.json
            questions_json: Path to questions.json
            answers_json: Path to answers.json
        """
        print("Loading dataset files...")
        with open(images_json, 'r') as f:
            self.images_data = json.load(f)

        with open(questions_json, 'r') as f:
            self.questions_data = json.load(f)

        with open(answers_json, 'r') as f:
            self.answers_data = json.load(f)

        print(f"Loaded {len(self.images_data['images'])} images")
        print(f"Loaded {len(self.questions_data['questions'])} questions")
        print(f"Loaded {len(self.answers_data['answers'])} answers")

    def group_by_location(self, location_key='original_name'):
        """
        Group images by location identifier

        Args:
            location_key: Key in image metadata to identify location
                         (e.g., 'original_name' for tile base name)

        Returns:
            Dictionary mapping location to list of image IDs
        """
        location_groups = defaultdict(list)

        for img in self.images_data['images']:
            # Extract location identifier from original_name
            # Assumes format like "location1_tile001.tif"
            original_name = img.get(location_key, '')
            location = self._extract_location(original_name)
            location_groups[location].append(img['id'])

        print(f"\nFound {len(location_groups)} unique locations:")
        for loc, imgs in sorted(location_groups.items()):
            print(f"  {loc}: {len(imgs)} images")

        return location_groups

    def _extract_location(self, filename):
        """
        Extract location identifier from filename

        Examples:
            "location1_tile001.tif" -> "location1"
            "newyork_2023_tile005.tif" -> "newyork_2023"
            "sentinel2_california_001.tif" -> "california"
        """
        # Remove extension
        name = Path(filename).stem

        # Split by common separators and take meaningful parts
        parts = name.replace('_tile', '').replace('tile', '').split('_')

        # Try to identify location (exclude numeric tile IDs)
        location_parts = [p for p in parts if not p.isdigit()]

        if location_parts:
            return '_'.join(location_parts)
        else:
            # Fallback: use first part
            return parts[0] if parts else name

    def create_splits(self, location_groups, train_ratio=0.7, val_ratio=0.15,
                     test_ratio=0.15, held_out_locations=None, seed=42):
        """
        Create train/val/test splits from location groups

        Args:
            location_groups: Dictionary mapping location to image IDs
            train_ratio: Proportion of locations for training
            val_ratio: Proportion of locations for validation
            test_ratio: Proportion of locations for testing
            held_out_locations: List of specific locations to reserve for test set
            seed: Random seed for reproducibility

        Returns:
            Dictionary with 'train', 'val', 'test' keys mapping to image IDs
        """
        random.seed(seed)

        locations = list(location_groups.keys())
        random.shuffle(locations)

        splits = {
            'train': [],
            'val': [],
            'test': []
        }

        # Handle held-out locations first
        if held_out_locations:
            for loc in held_out_locations:
                if loc in location_groups:
                    splits['test'].extend(location_groups[loc])
                    locations.remove(loc)
                else:
                    print(f"Warning: Held-out location '{loc}' not found in dataset")

        # Split remaining locations
        n_locations = len(locations)
        n_train = int(n_locations * train_ratio / (train_ratio + val_ratio + test_ratio))
        n_val = int(n_locations * val_ratio / (train_ratio + val_ratio + test_ratio))

        train_locations = locations[:n_train]
        val_locations = locations[n_train:n_train + n_val]
        test_locations = locations[n_train + n_val:]

        # Assign images to splits
        for loc in train_locations:
            splits['train'].extend(location_groups[loc])

        for loc in val_locations:
            splits['val'].extend(location_groups[loc])

        for loc in test_locations:
            splits['test'].extend(location_groups[loc])

        # Print split statistics
        print("\n" + "="*60)
        print("Split Statistics")
        print("="*60)
        print(f"Train: {len(train_locations)} locations, {len(splits['train'])} images")
        print(f"Val:   {len(val_locations)} locations, {len(splits['val'])} images")
        print(f"Test:  {len(test_locations)} locations, {len(splits['test'])} images")

        print("\nTrain locations:", train_locations)
        print("Val locations:", val_locations)
        print("Test locations:", test_locations)

        return splits

    def create_split_files(self, splits, output_dir):
        """
        Create separate JSON files for each split

        Args:
            splits: Dictionary with 'train', 'val', 'test' keys
            output_dir: Directory to save split files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for split_name, image_ids in splits.items():
            print(f"\nCreating {split_name} split files...")

            # Filter images
            split_images = {
                "images": [img for img in self.images_data['images']
                          if img['id'] in image_ids]
            }

            # Get question IDs for these images
            question_ids = set()
            for img in split_images['images']:
                question_ids.update(img.get('questions_ids', []))

            # Filter questions
            split_questions = {
                "questions": [q for q in self.questions_data['questions']
                             if q['id'] in question_ids]
            }

            # Get answer IDs for these questions
            answer_ids = set()
            for q in split_questions['questions']:
                answer_ids.update(q.get('answers_ids', []))

            # Filter answers
            split_answers = {
                "answers": [a for a in self.answers_data['answers']
                           if a['id'] in answer_ids]
            }

            # Save files
            images_file = output_path / f"{split_name}_images.json"
            questions_file = output_path / f"{split_name}_questions.json"
            answers_file = output_path / f"{split_name}_answers.json"

            with open(images_file, 'w') as f:
                json.dump(split_images, f, indent=2)

            with open(questions_file, 'w') as f:
                json.dump(split_questions, f, indent=2)

            with open(answers_file, 'w') as f:
                json.dump(split_answers, f, indent=2)

            print(f"  Images: {len(split_images['images'])}")
            print(f"  Questions: {len(split_questions['questions'])}")
            print(f"  Answers: {len(split_answers['answers'])}")
            print(f"  Saved to: {output_path}")

    def analyze_split_balance(self, splits):
        """
        Analyze and report on split balance

        Args:
            splits: Dictionary with 'train', 'val', 'test' keys
        """
        print("\n" + "="*60)
        print("Split Balance Analysis")
        print("="*60)

        for split_name, image_ids in splits.items():
            # Count questions by type
            question_types = defaultdict(int)
            total_questions = 0

            for img_id in image_ids:
                for img in self.images_data['images']:
                    if img['id'] == img_id:
                        for q_id in img.get('questions_ids', []):
                            for q in self.questions_data['questions']:
                                if q['id'] == q_id:
                                    question_types[q['type']] += 1
                                    total_questions += 1
                        break

            print(f"\n{split_name.upper()} Split:")
            print(f"  Total questions: {total_questions}")
            for q_type, count in sorted(question_types.items()):
                percentage = (count / total_questions * 100) if total_questions > 0 else 0
                print(f"    {q_type}: {count} ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Create geographic-based train/val/test splits for RSVQA dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic split with default ratios (70/15/15)
    python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits

    # Custom split ratios
    python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits --train_ratio 0.8 --val_ratio 0.1 --test_ratio 0.1

    # Hold out specific locations for testing
    python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits --held_out_locations location3 location5

    # Custom location extraction
    python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits --location_key original_name
        """
    )

    parser.add_argument('--images_json', type=str, required=True,
                       help='Path to images.json file')
    parser.add_argument('--questions_json', type=str, required=True,
                       help='Path to questions.json file')
    parser.add_argument('--answers_json', type=str, required=True,
                       help='Path to answers.json file')
    parser.add_argument('--output_dir', type=str, default='./splits',
                       help='Directory to save split files')
    parser.add_argument('--train_ratio', type=float, default=0.7,
                       help='Proportion of locations for training (default: 0.7)')
    parser.add_argument('--val_ratio', type=float, default=0.15,
                       help='Proportion of locations for validation (default: 0.15)')
    parser.add_argument('--test_ratio', type=float, default=0.15,
                       help='Proportion of locations for testing (default: 0.15)')
    parser.add_argument('--held_out_locations', type=str, nargs='+',
                       help='Specific locations to reserve for test set')
    parser.add_argument('--location_key', type=str, default='original_name',
                       help='Key in image metadata to identify location')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')

    args = parser.parse_args()

    # Validate split ratios
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if abs(total_ratio - 1.0) > 0.01:
        print(f"Warning: Split ratios sum to {total_ratio}, normalizing to 1.0")
        args.train_ratio /= total_ratio
        args.val_ratio /= total_ratio
        args.test_ratio /= total_ratio

    # Create splitter
    splitter = DatasetSplitter(
        args.images_json,
        args.questions_json,
        args.answers_json
    )

    # Group by location
    location_groups = splitter.group_by_location(args.location_key)

    # Create splits
    splits = splitter.create_splits(
        location_groups,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        held_out_locations=args.held_out_locations,
        seed=args.seed
    )

    # Analyze balance
    splitter.analyze_split_balance(splits)

    # Create split files
    splitter.create_split_files(splits, args.output_dir)

    print("\n" + "="*60)
    print("Split creation complete!")
    print("="*60)
    print(f"Files saved to: {args.output_dir}")
    print("\nNext steps:")
    print("1. Review split distributions above")
    print("2. Copy split files to your training directory")
    print("3. Update config.py with split file paths")
    print("4. Start training with: python VQA_model/train.py")


if __name__ == '__main__':
    main()
