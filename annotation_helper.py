#!/usr/bin/env python3
"""
RSVQA Annotation Helper Script

This script provides utilities to help create questions and answers for your
custom RSVQA dataset. It supports the four main question types:
1. Object Detection ("Is there a X?")
2. Counting ("How many X?")
3. Spatial Relationships ("Is X near Y?")
4. Attributes ("What color is X?")

Usage:
    python annotation_helper.py --mode interactive
    python annotation_helper.py --mode batch --images_json images.json --output_dir ./annotations
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
import random


class QuestionGenerator:
    """Generate VQA questions for remote sensing imagery"""

    def __init__(self):
        # Define object vocabulary for Sentinel-2 imagery
        self.objects = [
            'building', 'road', 'highway', 'street', 'tree', 'forest',
            'water', 'river', 'lake', 'field', 'farmland', 'grass',
            'parking lot', 'vehicle', 'ship', 'airport', 'runway',
            'stadium', 'bridge', 'dam', 'solar panel', 'wind turbine',
            'factory', 'warehouse', 'residential area', 'urban area',
            'vegetation', 'crop', 'bare soil', 'construction site'
        ]

        # Define colors for attributes
        self.colors = [
            'green', 'dark green', 'light green',
            'blue', 'dark blue', 'light blue',
            'brown', 'gray', 'white', 'red',
            'yellow', 'tan', 'black'
        ]

        # Define spatial relationships
        self.spatial_relations = {
            'proximity': ['near', 'close to', 'adjacent to', 'next to', 'far from'],
            'directional': ['north of', 'south of', 'east of', 'west of',
                          'left of', 'right of', 'above', 'below']
        }

        # Define question templates
        self.templates = {
            'presence': [
                "Is there a {object}?",
                "Is a {object} present?",
                "Is there a {object} in the image?",
                "Can you see a {object}?"
            ],
            'count': [
                "How many {objects} are there?",
                "What is the number of {objects}?",
                "How many {objects} can you count?",
                "What is the amount of {objects}?"
            ],
            'relation': [
                "Is the {object1} {relation} the {object2}?",
                "Is there a {object1} {relation} a {object2}?"
            ],
            'attribute_color': [
                "What color is the {object}?",
                "What is the color of the {object}?"
            ],
            'attribute_type': [
                "What type of {category} is this?",
                "What kind of {category} is visible?",
                "What is the land use?"
            ]
        }

        # Define answer ranges for counting
        self.count_ranges = [
            ("0", 0, 0),
            ("between 1 and 5", 1, 5),
            ("between 5 and 10", 5, 10),
            ("between 10 and 50", 10, 50),
            ("between 50 and 100", 50, 100),
            ("more than 100", 100, float('inf'))
        ]

    def generate_presence_questions(self, objects_present):
        """
        Generate presence questions for detected objects

        Args:
            objects_present: List of objects present in the image

        Returns:
            List of (question, answer) tuples
        """
        questions = []

        # Positive examples
        for obj in objects_present:
            template = random.choice(self.templates['presence'])
            question = template.format(object=obj)
            questions.append((question, "yes", "presence"))

        # Negative examples (objects not present)
        objects_absent = [obj for obj in self.objects if obj not in objects_present]
        num_negative = min(len(objects_present), len(objects_absent))

        for obj in random.sample(objects_absent, num_negative):
            template = random.choice(self.templates['presence'])
            question = template.format(object=obj)
            questions.append((question, "no", "presence"))

        return questions

    def generate_count_questions(self, object_counts):
        """
        Generate counting questions for objects

        Args:
            object_counts: Dictionary mapping object name to count

        Returns:
            List of (question, answer) tuples
        """
        questions = []

        for obj, count in object_counts.items():
            template = random.choice(self.templates['count'])
            # Pluralize object name
            obj_plural = obj + 's' if not obj.endswith('s') else obj

            question = template.format(objects=obj_plural)

            # Convert count to range
            answer = self._count_to_range(count)

            questions.append((question, answer, "count"))

        return questions

    def _count_to_range(self, count):
        """Convert numeric count to range string"""
        for range_str, min_val, max_val in self.count_ranges:
            if min_val <= count <= max_val:
                return range_str
        return "more than 100"

    def generate_relation_questions(self, object_pairs, relations):
        """
        Generate spatial relationship questions

        Args:
            object_pairs: List of (object1, object2, relation_type, answer) tuples

        Returns:
            List of (question, answer) tuples
        """
        questions = []

        for obj1, obj2, relation, answer in object_pairs:
            template = random.choice(self.templates['relation'])
            question = template.format(
                object1=obj1,
                object2=obj2,
                relation=relation
            )
            questions.append((question, answer, "relation"))

        return questions

    def generate_attribute_questions(self, object_attributes):
        """
        Generate attribute questions (color, type, etc.)

        Args:
            object_attributes: List of (object, attribute_type, attribute_value) tuples

        Returns:
            List of (question, answer) tuples
        """
        questions = []

        for obj, attr_type, attr_value in object_attributes:
            if attr_type == 'color':
                template = random.choice(self.templates['attribute_color'])
                question = template.format(object=obj)
            else:
                template = random.choice(self.templates['attribute_type'])
                question = template.format(category=attr_type)

            questions.append((question, attr_value, "attribute"))

        return questions


class AnnotationManager:
    """Manage annotation JSON files"""

    def __init__(self, images_json_path, output_dir):
        self.images_json_path = images_json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data or create new
        self.images = self._load_json(images_json_path, {"images": []})
        self.questions = {"questions": []}
        self.answers = {"answers": []}

        self.question_id = 1
        self.answer_id = 1

    def _load_json(self, path, default):
        """Load JSON file or return default"""
        path = Path(path)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        return default

    def add_questions_for_image(self, image_id, questions_answers):
        """
        Add questions and answers for a specific image

        Args:
            image_id: ID of the image
            questions_answers: List of (question, answer, type) tuples
        """
        timestamp = int(datetime.now().timestamp())
        question_ids = []

        for question_text, answer_text, q_type in questions_answers:
            # Add answer
            answer_entry = {
                "id": self.answer_id,
                "date_added": timestamp,
                "question_id": self.question_id,
                "people_id": 1,
                "answer": answer_text,
                "active": True
            }
            self.answers["answers"].append(answer_entry)

            # Add question
            question_entry = {
                "id": self.question_id,
                "date_added": timestamp,
                "img_id": image_id,
                "people_id": 1,
                "type": q_type,
                "question": question_text,
                "answers_ids": [self.answer_id],
                "active": True
            }
            self.questions["questions"].append(question_entry)

            question_ids.append(self.question_id)

            self.question_id += 1
            self.answer_id += 1

        # Update image with question IDs
        for img in self.images["images"]:
            if img["id"] == image_id:
                img["questions_ids"].extend(question_ids)
                break

    def save(self):
        """Save all JSON files"""
        images_path = self.output_dir / "images.json"
        questions_path = self.output_dir / "questions.json"
        answers_path = self.output_dir / "answers.json"

        with open(images_path, 'w') as f:
            json.dump(self.images, f, indent=2)

        with open(questions_path, 'w') as f:
            json.dump(self.questions, f, indent=2)

        with open(answers_path, 'w') as f:
            json.dump(self.answers, f, indent=2)

        print(f"\nSaved annotations:")
        print(f"  Images: {images_path}")
        print(f"  Questions: {questions_path}")
        print(f"  Answers: {answers_path}")
        print(f"\nTotal: {len(self.questions['questions'])} questions for {len(self.images['images'])} images")


def interactive_mode():
    """Interactive annotation mode"""
    print("="*60)
    print("RSVQA Interactive Annotation Helper")
    print("="*60)

    generator = QuestionGenerator()

    print("\nAvailable objects:")
    for i, obj in enumerate(generator.objects, 1):
        print(f"  {i}. {obj}")

    # Get image info
    print("\n" + "="*60)
    image_id = int(input("Enter image ID: "))

    # Question type selection
    print("\nSelect question types to generate:")
    print("1. Object Detection (Is there a X?)")
    print("2. Counting (How many X?)")
    print("3. Spatial Relationships (Is X near Y?)")
    print("4. Attributes (What color is X?)")
    print("5. All types")

    choice = input("Enter choice (1-5): ")

    all_questions = []

    # Object detection
    if choice in ['1', '5']:
        print("\n--- Object Detection ---")
        present_objects = input("Enter objects present (comma-separated): ").strip().split(',')
        present_objects = [obj.strip() for obj in present_objects]
        questions = generator.generate_presence_questions(present_objects)
        all_questions.extend(questions)
        print(f"Generated {len(questions)} presence questions")

    # Counting
    if choice in ['2', '5']:
        print("\n--- Counting ---")
        num_objects = int(input("How many objects to count? "))
        object_counts = {}
        for i in range(num_objects):
            obj = input(f"  Object {i+1} name: ")
            count = int(input(f"  Count of {obj}: "))
            object_counts[obj] = count
        questions = generator.generate_count_questions(object_counts)
        all_questions.extend(questions)
        print(f"Generated {len(questions)} counting questions")

    # Spatial relationships
    if choice in ['3', '5']:
        print("\n--- Spatial Relationships ---")
        num_pairs = int(input("How many object pairs? "))
        object_pairs = []
        for i in range(num_pairs):
            obj1 = input(f"  Pair {i+1} - Object 1: ")
            obj2 = input(f"  Pair {i+1} - Object 2: ")
            relation = input(f"  Relation (e.g., 'near', 'north of'): ")
            answer = input(f"  Answer (yes/no): ")
            object_pairs.append((obj1, obj2, relation, answer))
        questions = generator.generate_relation_questions(object_pairs, None)
        all_questions.extend(questions)
        print(f"Generated {len(questions)} relation questions")

    # Attributes
    if choice in ['4', '5']:
        print("\n--- Attributes ---")
        num_attrs = int(input("How many attribute questions? "))
        object_attributes = []
        for i in range(num_attrs):
            obj = input(f"  Attribute {i+1} - Object: ")
            attr_type = input(f"  Attribute type (color/type): ")
            attr_value = input(f"  Attribute value: ")
            object_attributes.append((obj, attr_type, attr_value))
        questions = generator.generate_attribute_questions(object_attributes)
        all_questions.extend(questions)
        print(f"Generated {len(questions)} attribute questions")

    # Display generated questions
    print("\n" + "="*60)
    print("Generated Questions:")
    print("="*60)
    for i, (q, a, t) in enumerate(all_questions, 1):
        print(f"{i}. [{t}] Q: {q}")
        print(f"   A: {a}")

    # Save option
    save = input("\nSave these questions? (y/n): ")
    if save.lower() == 'y':
        images_json = input("Path to images.json: ")
        output_dir = input("Output directory: ")

        manager = AnnotationManager(images_json, output_dir)
        manager.add_questions_for_image(image_id, all_questions)
        manager.save()


def batch_mode(images_json, output_dir):
    """Batch processing mode - generate template questions for all images"""
    print("="*60)
    print("RSVQA Batch Annotation Helper")
    print("="*60)

    manager = AnnotationManager(images_json, output_dir)
    generator = QuestionGenerator()

    print(f"\nFound {len(manager.images['images'])} images")
    print("Generating template questions...")

    # Generate 2 template questions per image
    for img in manager.images['images']:
        image_id = img['id']

        # Generate basic presence question
        template_questions = [
            ("Is there a building?", "NEEDS_ANNOTATION", "presence"),
            ("How many buildings are there?", "NEEDS_ANNOTATION", "count")
        ]

        manager.add_questions_for_image(image_id, template_questions)

    manager.save()

    print("\nBatch processing complete!")
    print(f"Generated {len(manager.questions['questions'])} template questions")
    print("\nNext steps:")
    print("1. Open questions.json and answers.json")
    print("2. Replace 'NEEDS_ANNOTATION' with actual answers")
    print("3. Add more specific questions as needed")


def main():
    parser = argparse.ArgumentParser(
        description='RSVQA Annotation Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--mode', type=str, choices=['interactive', 'batch'],
                       default='interactive',
                       help='Annotation mode: interactive (one image at a time) or batch (all images)')
    parser.add_argument('--images_json', type=str,
                       help='Path to images.json file')
    parser.add_argument('--output_dir', type=str, default='./annotations',
                       help='Directory to save annotation files')

    args = parser.parse_args()

    if args.mode == 'interactive':
        interactive_mode()
    elif args.mode == 'batch':
        if not args.images_json:
            print("Error: --images_json required for batch mode")
            return
        batch_mode(args.images_json, args.output_dir)


if __name__ == '__main__':
    main()
