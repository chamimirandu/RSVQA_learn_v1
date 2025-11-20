# Multi-Task Learning Guide: Combining Four VQA Experiments

This guide explains how to train individual models for each of your four question types, then combine them into a unified multi-task model.

---

## 🎯 Training Strategy Overview

### Phase 1: Individual Task Training (4 Separate Models)
Train specialized models for each task:
1. **Model 1**: Object Detection only
2. **Model 2**: Counting only
3. **Model 3**: Spatial Relationships only
4. **Model 4**: Attributes only

### Phase 2: Multi-Task Learning (1 Unified Model)
Combine all tasks into a single model that can handle all question types.

### Phase 3: Comparison & Analysis
Compare single-task vs multi-task performance.

---

## 📊 Phase 1: Individual Task Training

### Step 1.1: Filter Dataset by Question Type

Create task-specific datasets:

```python
#!/usr/bin/env python3
"""
filter_by_question_type.py
Create task-specific dataset files
"""
import json
import argparse
from pathlib import Path


def filter_dataset(images_json, questions_json, answers_json,
                   question_type, output_dir):
    """Filter dataset to include only specific question type"""

    # Load data
    with open(images_json) as f:
        images = json.load(f)
    with open(questions_json) as f:
        questions = json.load(f)
    with open(answers_json) as f:
        answers = json.load(f)

    # Filter questions by type
    filtered_questions = [q for q in questions['questions']
                         if q['type'] == question_type]
    filtered_q_ids = {q['id'] for q in filtered_questions}

    # Filter answers
    filtered_answers = [a for a in answers['answers']
                       if a['question_id'] in filtered_q_ids]

    # Filter images (only keep images with questions of this type)
    filtered_images = []
    for img in images['images']:
        img_q_ids = [qid for qid in img.get('questions_ids', [])
                     if qid in filtered_q_ids]
        if img_q_ids:
            img_copy = img.copy()
            img_copy['questions_ids'] = img_q_ids
            filtered_images.append(img_copy)

    # Save filtered data
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(output_path / f'{question_type}_images.json', 'w') as f:
        json.dump({'images': filtered_images}, f, indent=2)

    with open(output_path / f'{question_type}_questions.json', 'w') as f:
        json.dump({'questions': filtered_questions}, f, indent=2)

    with open(output_path / f'{question_type}_answers.json', 'w') as f:
        json.dump({'answers': filtered_answers}, f, indent=2)

    print(f"\nFiltered dataset for '{question_type}':")
    print(f"  Images: {len(filtered_images)}")
    print(f"  Questions: {len(filtered_questions)}")
    print(f"  Answers: {len(filtered_answers)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--images_json', required=True)
    parser.add_argument('--questions_json', required=True)
    parser.add_argument('--answers_json', required=True)
    parser.add_argument('--question_type', required=True,
                       choices=['presence', 'count', 'relation', 'attribute'])
    parser.add_argument('--output_dir', required=True)

    args = parser.parse_args()
    filter_dataset(args.images_json, args.questions_json, args.answers_json,
                   args.question_type, args.output_dir)
```

Run for each task:

```bash
# Create task-specific datasets for training
for qtype in presence count relation attribute; do
    python filter_by_question_type.py \
        --images_json dataset/splits/train_images.json \
        --questions_json dataset/splits/train_questions.json \
        --answers_json dataset/splits/train_answers.json \
        --question_type $qtype \
        --output_dir dataset/task_specific/train/$qtype
done

# Repeat for validation
for qtype in presence count relation attribute; do
    python filter_by_question_type.py \
        --images_json dataset/splits/val_images.json \
        --questions_json dataset/splits/val_questions.json \
        --answers_json dataset/splits/val_answers.json \
        --question_type $qtype \
        --output_dir dataset/task_specific/val/$qtype
done

# Repeat for test
for qtype in presence count relation attribute; do
    python filter_by_question_type.py \
        --images_json dataset/splits/test_images.json \
        --questions_json dataset/splits/test_questions.json \
        --answers_json dataset/splits/test_answers.json \
        --question_type $qtype \
        --output_dir dataset/task_specific/test/$qtype
done
```

### Step 1.2: Modify Training Script for Single Task

Edit `VQA_model/train.py` to add a `--task` argument:

```python
# Add to argument parser
parser.add_argument('--task', type=str, default='all',
                   choices=['all', 'presence', 'count', 'relation', 'attribute'],
                   help='Specific task to train (default: all)')

# Modify data loading section
if args.task != 'all':
    # Load task-specific data
    path_to_img_ids = f'dataset/task_specific/train/{args.task}/{args.task}_images.json'
    path_to_questions = f'dataset/task_specific/train/{args.task}/{args.task}_questions.json'
    path_to_answers = f'dataset/task_specific/train/{args.task}/{args.task}_answers.json'

    path_to_img_ids_val = f'dataset/task_specific/val/{args.task}/{args.task}_images.json'
    path_to_questions_val = f'dataset/task_specific/val/{args.task}/{args.task}_questions.json'
    path_to_answers_val = f'dataset/task_specific/val/{args.task}/{args.task}_answers.json'
```

### Step 1.3: Train Individual Models

**Experiment 1: Object Detection (Presence)**

```bash
python VQA_model/train.py \
    --task presence \
    --exp_name exp1_object_detection \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001 \
    --save_dir models/exp1/

# Expected output:
# Epoch 150/150: Val Acc = 0.78, Best = 0.78
# Saved best model to: models/exp1/exp1_object_detection_best.pth
```

**Experiment 2: Counting**

```bash
python VQA_model/train.py \
    --task count \
    --exp_name exp2_counting \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001 \
    --save_dir models/exp2/

# Expected output:
# Epoch 150/150: Val Acc = 0.64, Best = 0.66
```

**Experiment 3: Spatial Relationships**

```bash
python VQA_model/train.py \
    --task relation \
    --exp_name exp3_spatial \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001 \
    --save_dir models/exp3/

# Expected output:
# Epoch 150/150: Val Acc = 0.59, Best = 0.61
```

**Experiment 4: Attributes**

```bash
python VQA_model/train.py \
    --task attribute \
    --exp_name exp4_attributes \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001 \
    --save_dir models/exp4/

# Expected output:
# Epoch 150/150: Val Acc = 0.71, Best = 0.72
```

### Step 1.4: Evaluate Individual Models

Create evaluation script:

```bash
# evaluate_single_task.sh
#!/bin/bash

for task in presence count relation attribute; do
    echo "Evaluating $task model..."
    python VQA_model/test.py \
        --model_path models/exp${task}/best_model.pth \
        --test_images dataset/task_specific/test/${task}/${task}_images.json \
        --test_questions dataset/task_specific/test/${task}/${task}_questions.json \
        --test_answers dataset/task_specific/test/${task}/${task}_answers.json \
        --output results/single_task/${task}_results.json
done
```

**Expected Results**:

| Task | Train Acc | Val Acc | Test Acc | Notes |
|------|-----------|---------|----------|-------|
| Object Detection | 0.85 | 0.78 | 0.75 | Binary classification, easier |
| Counting | 0.72 | 0.66 | 0.64 | Multi-class, harder |
| Spatial Relations | 0.68 | 0.61 | 0.59 | Most difficult |
| Attributes | 0.78 | 0.72 | 0.71 | Medium difficulty |

---

## 🔄 Phase 2: Multi-Task Learning

### Approach 1: Simple Multi-Task (Shared Encoder)

**Architecture**:
```
Input Image → ResNet-152 (shared) → Visual Features (2048-d)
Input Question → Skip-thoughts (shared) → Question Features (2400-d)
                                        ↓
                              Fusion Layer (shared)
                                        ↓
                              Fused Features (1200-d)
                                        ↓
                      Classification Head (shared, 100 classes)
```

**Training**:
```bash
python VQA_model/train.py \
    --task all \
    --exp_name exp5_multitask_simple \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001 \
    --save_dir models/exp5/
```

**Pros**:
- Simple to implement (already supported by existing code)
- Learns shared representations across tasks
- Single model deployment

**Cons**:
- May underperform on individual tasks
- Task interference possible

### Approach 2: Multi-Task with Task-Specific Heads

**Architecture**:
```
Input Image → ResNet-152 (shared) → Visual Features
Input Question → Skip-thoughts (shared) → Question Features
                                        ↓
                              Fusion Layer (shared)
                                        ↓
                              Fused Features (1200-d)
                                        ↓
                        ┌────────────────┴────────────────┐
                        ↓                ↓                ↓
              Head 1 (presence)  Head 2 (count)  Head 3 (relation)  Head 4 (attribute)
                   (2 classes)      (20 classes)    (2 classes)         (30 classes)
```

**Implementation**:

```python
# VQA_model/models/multitask_model.py
import torch
import torch.nn as nn
from .model import VQAModel


class MultiTaskVQAModel(nn.Module):
    """Multi-task VQA model with task-specific heads"""

    def __init__(self, visual_out=2048, question_out=2400, fusion_in=1200,
                 num_classes_per_task={'presence': 2, 'count': 20,
                                       'relation': 2, 'attribute': 30}):
        super().__init__()

        # Shared visual encoder (ResNet-152)
        self.visual_encoder = ...  # From original model

        # Shared question encoder (Skip-thoughts)
        self.question_encoder = ...  # From original model

        # Shared fusion layer
        self.visual_proj = nn.Sequential(
            nn.Linear(visual_out, fusion_in),
            nn.Tanh()
        )
        self.question_proj = nn.Sequential(
            nn.Linear(question_out, fusion_in),
            nn.Tanh()
        )

        # Task-specific heads
        self.task_heads = nn.ModuleDict({
            'presence': self._make_classifier(fusion_in, num_classes_per_task['presence']),
            'count': self._make_classifier(fusion_in, num_classes_per_task['count']),
            'relation': self._make_classifier(fusion_in, num_classes_per_task['relation']),
            'attribute': self._make_classifier(fusion_in, num_classes_per_task['attribute'])
        })

    def _make_classifier(self, in_features, num_classes):
        return nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, 256),
            nn.Tanh(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )

    def forward(self, image, question, task_type):
        # Shared encoding
        visual_feats = self.visual_encoder(image)
        question_feats = self.question_encoder(question)

        # Shared fusion
        v_proj = self.visual_proj(visual_feats)
        q_proj = self.question_proj(question_feats)
        fused = torch.mul(v_proj, q_proj)
        fused = torch.tanh(fused)

        # Task-specific classification
        output = self.task_heads[task_type](fused)
        return output
```

**Training**:

```python
# Modified training loop
for batch in train_loader:
    images, questions, answers, task_types = batch

    # Group by task type
    task_batches = defaultdict(list)
    for i, task in enumerate(task_types):
        task_batches[task].append(i)

    total_loss = 0
    for task, indices in task_batches.items():
        task_images = images[indices]
        task_questions = questions[indices]
        task_answers = answers[indices]

        outputs = model(task_images, task_questions, task)
        loss = criterion(outputs, task_answers)
        total_loss += loss

    # Backward pass with combined loss
    optimizer.zero_grad()
    total_loss.backward()
    optimizer.step()
```

### Approach 3: Progressive Multi-Task (Curriculum Learning)

Train tasks in order of difficulty:

```bash
# Stage 1: Train on easiest task (object detection)
python VQA_model/train.py \
    --task presence \
    --epochs 50 \
    --save_dir models/progressive/stage1

# Stage 2: Add counting (fine-tune on both)
python VQA_model/train.py \
    --task presence,count \
    --init_from models/progressive/stage1/best_model.pth \
    --epochs 50 \
    --save_dir models/progressive/stage2

# Stage 3: Add attributes
python VQA_model/train.py \
    --task presence,count,attribute \
    --init_from models/progressive/stage2/best_model.pth \
    --epochs 50 \
    --save_dir models/progressive/stage3

# Stage 4: Add spatial relations (hardest)
python VQA_model/train.py \
    --task all \
    --init_from models/progressive/stage3/best_model.pth \
    --epochs 50 \
    --save_dir models/progressive/stage4
```

---

## 📊 Phase 3: Comparison & Analysis

### Step 3.1: Evaluate All Models

```python
#!/usr/bin/env python3
"""
compare_models.py
Compare single-task vs multi-task performance
"""
import json
import numpy as np
from pathlib import Path


def evaluate_model(results_file):
    """Calculate accuracy from results file"""
    with open(results_file) as f:
        results = json.load(f)

    correct = sum(1 for r in results if r['predicted'] == r['ground_truth'])
    total = len(results)
    accuracy = correct / total if total > 0 else 0

    return accuracy, total


def main():
    # Evaluate single-task models
    single_task_results = {}
    for task in ['presence', 'count', 'relation', 'attribute']:
        acc, n = evaluate_model(f'results/single_task/{task}_results.json')
        single_task_results[task] = {'accuracy': acc, 'n_samples': n}

    # Evaluate multi-task model
    multitask_results = {}
    results_file = 'results/multitask/all_results.json'
    with open(results_file) as f:
        all_results = json.load(f)

    # Group by task
    for task in ['presence', 'count', 'relation', 'attribute']:
        task_results = [r for r in all_results if r['task_type'] == task]
        correct = sum(1 for r in task_results if r['predicted'] == r['ground_truth'])
        total = len(task_results)
        acc = correct / total if total > 0 else 0
        multitask_results[task] = {'accuracy': acc, 'n_samples': total}

    # Print comparison table
    print("\n" + "="*80)
    print("SINGLE-TASK vs MULTI-TASK COMPARISON")
    print("="*80)
    print(f"{'Task':<20} {'Single-Task':<15} {'Multi-Task':<15} {'Difference':<15}")
    print("-"*80)

    for task in ['presence', 'count', 'relation', 'attribute']:
        single_acc = single_task_results[task]['accuracy']
        multi_acc = multitask_results[task]['accuracy']
        diff = multi_acc - single_acc

        print(f"{task:<20} {single_acc:>6.3f} ({single_task_results[task]['n_samples']:>5}) "
              f"{multi_acc:>6.3f} ({multitask_results[task]['n_samples']:>5}) "
              f"{diff:>+6.3f}")

    # Overall averages
    single_avg = np.mean([r['accuracy'] for r in single_task_results.values()])
    multi_avg = np.mean([r['accuracy'] for r in multitask_results.values()])

    print("-"*80)
    print(f"{'AVERAGE':<20} {single_avg:>6.3f}        {multi_avg:>6.3f}        {multi_avg - single_avg:>+6.3f}")
    print("="*80)


if __name__ == '__main__':
    main()
```

**Expected Output**:

```
================================================================================
SINGLE-TASK vs MULTI-TASK COMPARISON
================================================================================
Task                 Single-Task     Multi-Task      Difference
--------------------------------------------------------------------------------
presence             0.750 ( 2800)  0.732 ( 2800)  -0.018
count                0.640 ( 1400)  0.658 ( 1400)  +0.018
relation             0.590 (  920)  0.612 (  920)  +0.022
attribute            0.710 ( 1080)  0.695 ( 1080)  -0.015
--------------------------------------------------------------------------------
AVERAGE              0.673           0.674           +0.002
================================================================================
```

### Step 3.2: Statistical Significance Testing

```python
from scipy import stats

def paired_t_test(single_results, multi_results):
    """Test if difference is statistically significant"""

    # Per-sample comparison
    differences = []
    for i in range(len(single_results)):
        single_correct = single_results[i]['predicted'] == single_results[i]['ground_truth']
        multi_correct = multi_results[i]['predicted'] == multi_results[i]['ground_truth']
        differences.append(int(multi_correct) - int(single_correct))

    t_stat, p_value = stats.ttest_rel(differences, [0]*len(differences))

    print(f"\nPaired t-test results:")
    print(f"  t-statistic: {t_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Significant at α=0.05: {'Yes' if p_value < 0.05 else 'No'}")
```

### Step 3.3: Analyze Task Interactions

Which tasks benefit from multi-task learning?

```python
# Analyze correlation between tasks
import pandas as pd

def analyze_task_correlations(results_file):
    """Analyze which tasks help each other"""

    with open(results_file) as f:
        results = json.load(f)

    # Create confusion matrix between tasks
    task_performance = {
        'presence': [],
        'count': [],
        'relation': [],
        'attribute': []
    }

    for r in results:
        task = r['task_type']
        correct = r['predicted'] == r['ground_truth']
        task_performance[task].append(int(correct))

    # Calculate correlations
    df = pd.DataFrame(task_performance)
    correlations = df.corr()

    print("\nTask Performance Correlations:")
    print(correlations)

    print("\nInsights:")
    print("- High correlation: Tasks benefit from shared learning")
    print("- Low/negative correlation: Tasks may interfere")
```

**Expected Insights**:

```
Task Performance Correlations:
              presence  count  relation  attribute
presence         1.00   0.34      0.28       0.42
count            0.34   1.00      0.19       0.31
relation         0.28   0.19      1.00       0.25
attribute        0.42   0.31      0.25       1.00

Insights:
- Presence & Attribute highly correlated (0.42): Both benefit from object recognition
- Relation has low correlation with others: Most independent task
- Count moderately correlated: Benefits from but doesn't strongly help others
```

---

## 🎯 Recommendations

Based on typical results:

### When to Use Single-Task Models:
- **High accuracy requirement** for specific task (e.g., deployment focused on counting only)
- **Limited training data** for some tasks
- **Task-specific deployment** (e.g., different models on different servers)

### When to Use Multi-Task Models:
- **Deployment efficiency** matters (one model for all tasks)
- **Balanced performance** across tasks desired
- **Sufficient training data** for all tasks
- **Resource-constrained deployment** (mobile, edge devices)

### Best Approach:
**Hybrid Strategy**:
1. Train single-task models first (baseline performance)
2. Train multi-task with task-specific heads (Approach 2)
3. Use ensemble: Average predictions from both

```python
# Ensemble prediction
def ensemble_predict(image, question, task_type):
    # Single-task model
    single_output = single_task_models[task_type](image, question)

    # Multi-task model
    multi_output = multitask_model(image, question, task_type)

    # Average probabilities
    ensemble_output = (single_output + multi_output) / 2

    return ensemble_output.argmax()
```

**Expected Improvement**: +2-5% over best individual model

---

## 📝 Experiment Log Template

Keep track of all experiments:

```markdown
# Experiment Log

## Experiment 1: Object Detection (Single-Task)
- **Date**: 2024-01-15
- **Model**: ResNet-152 + Skip-thoughts
- **Dataset**: 2,800 presence questions
- **Hyperparameters**:
  - Epochs: 150
  - Batch size: 70
  - Learning rate: 0.00001
- **Results**:
  - Train accuracy: 0.850
  - Val accuracy: 0.780
  - Test accuracy: 0.750
- **Notes**: Good performance, slight overfitting after epoch 100

## Experiment 2: Counting (Single-Task)
...

## Experiment 5: Multi-Task (All Tasks)
- **Date**: 2024-01-20
- **Model**: ResNet-152 + Skip-thoughts + Task-specific heads
- **Dataset**: 6,200 questions (all types)
- **Results**:
  - Presence: 0.732 (-1.8% vs single-task)
  - Count: 0.658 (+1.8% vs single-task)
  - Relation: 0.612 (+2.2% vs single-task)
  - Attribute: 0.695 (-1.5% vs single-task)
  - Average: 0.674 (+0.1% vs single-task average)
- **Conclusion**: Multi-task helps count/relation, slightly hurts presence/attribute
```

---

## 🚀 Next Steps

1. **Run all five experiments** (4 single-task + 1 multi-task)
2. **Analyze results** using comparison scripts
3. **Choose best approach** based on your deployment needs
4. **Fine-tune** with hyperparameter search
5. **Document findings** for publication/report

Good luck with your multi-task VQA experiments! 🎉
