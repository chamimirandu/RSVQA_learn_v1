# Complete Workflow for Creating Custom RSVQA Dataset with Sentinel-2

This guide provides a step-by-step workflow for creating your custom RSVQA dataset with Sentinel-2 data from Google Earth Engine, focusing on your four experimental tasks.

---

## 📋 Overview

**Your Goal**: Create a custom RSVQA dataset with Sentinel-2 imagery for four VQA tasks:
1. Object detection ("Is there a X?")
2. Counting ("How many X?")
3. Spatial relationships ("Is X near Y?")
4. Attributes ("What color is X?")

**Key Parameters**:
- Image source: Sentinel-2 from Google Earth Engine
- Patch size: **256×256 pixels**
- Format: 3-channel RGB GeoTIFF
- Multiple geographic locations for training diversity

---

## 🎯 Phase 1: Data Collection from Google Earth Engine

### Step 1.1: Define Your Geographic Locations

Select diverse locations for your training dataset. Consider:

```
Recommended diversity:
- 5-10 different geographic regions
- Mix of urban, rural, coastal, agricultural areas
- Different seasons/dates for temporal diversity
- Different climates/biomes

Example locations:
1. New York City (urban)
2. Iowa farmland (agricultural)
3. Amazon rainforest (vegetation)
4. California coast (coastal)
5. Arizona desert (arid)
```

### Step 1.2: Download Sentinel-2 from GEE

**Option A: Using Earth Engine Code Editor**

```javascript
// Earth Engine script for downloading Sentinel-2
var roi = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max]);

var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(roi)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
  .map(function(image) {
    return image.clip(roi).select(['B4', 'B3', 'B2']); // RGB
  })
  .median(); // Median composite to remove clouds

// Visualize
Map.centerObject(roi, 12);
Map.addLayer(sentinel2, {min: 0, max: 3000}, 'Sentinel-2 RGB');

// Export
Export.image.toDrive({
  image: sentinel2.visualize({min: 0, max: 3000}),
  description: 'location1_sentinel2',
  scale: 10,
  region: roi,
  crs: 'EPSG:3857',
  fileFormat: 'GeoTIFF',
  maxPixels: 1e9
});
```

**Option B: Using Python API (geemap)**

```python
import ee
import geemap

ee.Initialize()

# Define region of interest
roi = ee.Geometry.Rectangle([-74.05, 40.7, -73.95, 40.8])  # NYC example

# Get Sentinel-2 composite
s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(roi) \
    .filterDate('2023-01-01', '2023-12-31') \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
    .select(['B4', 'B3', 'B2']) \
    .median() \
    .clip(roi)

# Export
geemap.ee_export_image(s2,
                       filename='location1_sentinel2.tif',
                       scale=10,
                       region=roi,
                       crs='EPSG:3857')
```

### Step 1.3: Download for Multiple Locations

Create a batch download script:

```python
# locations.py
locations = {
    'newyork': [-74.05, 40.7, -73.95, 40.8],
    'iowa': [-93.6, 41.5, -93.5, 41.6],
    'amazon': [-60.0, -3.0, -59.9, -2.9],
    'california_coast': [-122.5, 37.7, -122.4, 37.8],
    'arizona': [-111.0, 33.4, -110.9, 33.5]
}

for name, bbox in locations.items():
    roi = ee.Geometry.Rectangle(bbox)
    # ... download code from above
    print(f"Downloaded {name}")
```

**Expected Output**:
```
downloads/
├── newyork_sentinel2.tif
├── iowa_sentinel2.tif
├── amazon_sentinel2.tif
├── california_coast_sentinel2.tif
└── arizona_sentinel2.tif
```

---

## 🔧 Phase 2: Data Preprocessing

### Step 2.1: Install Required Dependencies

```bash
pip install rasterio numpy pillow tqdm scikit-image
```

### Step 2.2: Tile Images into 256×256 Patches

Use the provided script:

```bash
python prepare_sentinel2_data.py \
    --input_dir ./downloads \
    --output_dir ./dataset \
    --patch_size 256
```

**What this does**:
1. Reads all GeoTIFF files in `downloads/`
2. Tiles each image into 256×256 patches
3. Filters patches by quality (mean pixel value 30-225)
4. Saves tiles to `dataset/images/`
5. Creates `images.json` with metadata
6. Generates annotation templates

**Expected Output**:
```
dataset/
├── images/
│   ├── newyork_sentinel2_tile_00001.tif
│   ├── newyork_sentinel2_tile_00002.tif
│   ├── ...
│   ├── iowa_sentinel2_tile_00001.tif
│   └── ...
├── images.json
├── questions_template.json
├── answers_template.json
└── tiles_metadata.csv
```

### Step 2.3: Verify Data Quality

```python
# Quick verification script
import rasterio
import numpy as np
from pathlib import Path

tiles_dir = Path('dataset/images')
for tile in list(tiles_dir.glob('*.tif'))[:10]:
    with rasterio.open(tile) as src:
        data = src.read()
        print(f"{tile.name}: shape={data.shape}, mean={np.mean(data):.1f}, min={np.min(data)}, max={np.max(data)}")
```

Expected output:
```
newyork_sentinel2_tile_00001.tif: shape=(3, 256, 256), mean=120.3, min=15, max=245
iowa_sentinel2_tile_00002.tif: shape=(3, 256, 256), mean=95.7, min=20, max=230
...
```

---

## ✏️ Phase 3: Annotation

### Step 3.1: Understand Annotation Requirements

Refer to `ANNOTATION_GUIDE.md` for detailed instructions on each question type.

**Recommended annotation volume per experiment**:

| Experiment | Min Images | Min Questions | Recommended Questions |
|-----------|-----------|--------------|---------------------|
| Object Detection | 1,000 | 10,000 | 50,000+ |
| Counting | 500 | 5,000 | 25,000+ |
| Spatial Relations | 500 | 5,000 | 20,000+ |
| Attributes | 500 | 5,000 | 20,000+ |

### Step 3.2: Choose Annotation Strategy

**Strategy A: Fully Manual Annotation**
- Best for: Small datasets (<1000 images)
- Tools: QGIS + text editor + spreadsheet
- Time: ~2-5 min per image × 5-10 questions = 10-50 min per image

**Strategy B: Semi-Automated with OSM**
- Best for: Medium datasets (1000-5000 images)
- Use existing `AutomaticDB/process.py` pipeline
- Requires: PostgreSQL + PostGIS + OSM data
- Time: Setup (1-2 days) + manual review (1 min per image)

**Strategy C: Hybrid Approach** (RECOMMENDED)
- Use annotation helper for templates
- Manual refinement and validation
- Best balance of speed and quality

### Step 3.3: Annotate Using Helper Script

**Interactive mode** (one image at a time):

```bash
python annotation_helper.py --mode interactive
```

Follow the prompts:
```
Enter image ID: 1
Select question types: 5 (all types)
Enter objects present: building, road, tree, water
How many objects to count? 2
  Object 1 name: building
  Count of building: 15
  Object 2 name: tree
  Count of tree: 45
...
```

**Batch mode** (generate templates for all images):

```bash
python annotation_helper.py \
    --mode batch \
    --images_json dataset/images.json \
    --output_dir dataset/annotations
```

Then manually edit `questions.json` and `answers.json` to replace placeholders.

### Step 3.4: Annotation Best Practices

**Object Detection**:
```json
Positive example:
Q: "Is there a building?"
A: "yes"
(Visible buildings in image)

Negative example:
Q: "Is there a lake?"
A: "no"
(No lakes visible)

Balance: 50% yes, 50% no
```

**Counting**:
```json
Exact for small numbers:
Q: "How many airports are there?"
A: "1"

Ranges for larger numbers:
Q: "How many buildings are there?"
A: "between 10 and 50"

Use consistent counting rules
```

**Spatial Relationships**:
```json
Proximity:
Q: "Is the building near the road?"
A: "yes"
(Building within 50m of road)

Directional:
Q: "Is the forest north of the city?"
A: "yes"
(Forest in upper half of image)

⚠️ Mark directional questions as non-augmentable!
```

**Attributes**:
```json
Color:
Q: "What color is the vegetation?"
A: "dark green"

Type:
Q: "What type of land use is visible?"
A: "residential"

Use Sentinel-2 appropriate colors
```

### Step 3.5: Quality Control Checklist

After annotation, verify:

- [ ] All questions have clear, answerable questions
- [ ] Answer distributions are balanced (not 90% "yes")
- [ ] No typos or formatting errors
- [ ] All image IDs referenced exist
- [ ] Question types are correctly labeled
- [ ] Spatial questions avoid ambiguity
- [ ] Count ranges are appropriate for image scale

---

## 📊 Phase 4: Dataset Splitting

### Step 4.1: Create Train/Val/Test Splits

**IMPORTANT**: Split by location, not random images!

```bash
python create_dataset_splits.py \
    --images_json dataset/images.json \
    --questions_json dataset/questions.json \
    --answers_json dataset/answers.json \
    --output_dir dataset/splits \
    --train_ratio 0.7 \
    --val_ratio 0.15 \
    --test_ratio 0.15 \
    --seed 42
```

**Example output**:
```
Found 5 unique locations:
  newyork_sentinel2: 234 images
  iowa_sentinel2: 189 images
  amazon_sentinel2: 156 images
  california_coast_sentinel2: 201 images
  arizona_sentinel2: 178 images

Split Statistics:
Train: 3 locations, 579 images
Val:   1 location, 201 images
Test:  1 location, 178 images
```

### Step 4.2: Hold Out Specific Test Locations

For evaluating geographic generalization:

```bash
python create_dataset_splits.py \
    --images_json dataset/images.json \
    --questions_json dataset/questions.json \
    --answers_json dataset/answers.json \
    --output_dir dataset/splits \
    --held_out_locations arizona_sentinel2 california_coast_sentinel2
```

This ensures Arizona and California are ONLY in test set (never seen during training).

### Step 4.3: Verify Split Quality

Check balance across splits:

```python
import json

splits = ['train', 'val', 'test']
for split in splits:
    with open(f'dataset/splits/{split}_questions.json') as f:
        questions = json.load(f)['questions']

    types = {}
    for q in questions:
        t = q['type']
        types[t] = types.get(t, 0) + 1

    print(f"\n{split.upper()}:")
    for t, count in types.items():
        print(f"  {t}: {count}")
```

Expected balanced distribution:
```
TRAIN:
  presence: 12500
  count: 6200
  relation: 4100
  attribute: 4800

VAL:
  presence: 2700
  count: 1350
  relation: 890
  attribute: 1040

TEST:
  presence: 2800
  count: 1400
  relation: 920
  attribute: 1080
```

---

## 🚀 Phase 5: Training

### Step 5.1: Prepare Training Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Install skip-thoughts
git clone https://github.com/Cadene/skip-thoughts.torch.git
cd skip-thoughts.torch/pytorch
python setup.py install
cd ../../..

# Download seq2vec.py
wget https://raw.githubusercontent.com/Cadene/vqa.pytorch/master/vqa/models/seq2vec.py \
     -O VQA_model/models/seq2vec.py
```

### Step 5.2: Update Configuration

Edit `AutomaticDB/config.py`:

```python
# Update paths to your split files
path_to_imgs = '/path/to/dataset/images/'
path_to_img_ids = '/path/to/dataset/splits/train_images.json'
path_to_questions = '/path/to/dataset/splits/train_questions.json'
path_to_answers = '/path/to/dataset/splits/train_answers.json'

# Validation paths
path_to_img_ids_val = '/path/to/dataset/splits/val_images.json'
path_to_questions_val = '/path/to/dataset/splits/val_questions.json'
path_to_answers_val = '/path/to/dataset/splits/val_answers.json'

# Test paths
path_to_img_ids_test = '/path/to/dataset/splits/test_images.json'
path_to_questions_test = '/path/to/dataset/splits/test_questions.json'
path_to_answers_test = '/path/to/dataset/splits/test_answers.json'
```

### Step 5.3: Run Training for Each Experiment

**Experiment 1: Object Detection (Presence Questions)**

```bash
python VQA_model/train.py \
    --exp_name experiment1_object_detection \
    --question_types presence \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001
```

**Experiment 2: Counting**

```bash
python VQA_model/train.py \
    --exp_name experiment2_counting \
    --question_types count \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001
```

**Experiment 3: Spatial Relationships**

```bash
python VQA_model/train.py \
    --exp_name experiment3_spatial_relations \
    --question_types relation \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001
```

**Experiment 4: Attributes**

```bash
python VQA_model/train.py \
    --exp_name experiment4_attributes \
    --question_types attribute \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001
```

### Step 5.4: Monitor Training

Training will output:

```
Epoch 1/150
Train Loss: 3.452, Train Acc: 0.423
Val Loss: 3.201, Val Acc: 0.456

Accuracy by question type:
  presence: 0.512
  count: 0.387
  relation: 0.341
  attribute: 0.429

Best validation accuracy: 0.456 (saved to models/experiment1_best.pth)
```

Track metrics:
- Overall accuracy
- Per-question-type accuracy
- Training/validation loss curves
- Overfitting indicators

### Step 5.5: Combine Experiments (Multi-Task Learning)

After individual experiments, train a unified model:

```bash
python VQA_model/train.py \
    --exp_name experiment5_multitask \
    --question_types presence count relation attribute \
    --epochs 150 \
    --batch_size 70 \
    --lr 0.00001
```

Compare performance:
```
Single-task results:
  Object detection: 0.78
  Counting: 0.64
  Spatial: 0.59
  Attributes: 0.71

Multi-task result:
  Overall: 0.69
  Object detection: 0.75 (-0.03)
  Counting: 0.66 (+0.02)
  Spatial: 0.61 (+0.02)
  Attributes: 0.68 (-0.03)
```

---

## 📈 Phase 6: Evaluation

### Step 6.1: Evaluate on Test Set

```bash
python VQA_model/test.py \
    --model_path models/experiment5_multitask_best.pth \
    --test_images dataset/splits/test_images.json \
    --test_questions dataset/splits/test_questions.json \
    --test_answers dataset/splits/test_answers.json \
    --output results/test_results.json
```

### Step 6.2: Analyze Results

Key metrics to report:

1. **Overall Accuracy**
```
Test Accuracy: 0.672
```

2. **Per-Question-Type Accuracy**
```
Object Detection (Is there X?): 0.743
Counting (How many X?): 0.651
Spatial Relations (Is X near Y?): 0.598
Attributes (What color is X?): 0.694
```

3. **Per-Location Performance** (generalization)
```
Training locations (seen):
  newyork: 0.712
  iowa: 0.698
  amazon: 0.654

Test locations (unseen):
  arizona: 0.623
  california_coast: 0.641
```

4. **Confusion Matrices**

For binary questions (presence, spatial):
```
Predicted:     Yes    No
Actual: Yes    845    123
        No     97     935
```

For counting:
```
              0    1-5   5-10  10-50  50-100  >100
0            89     12      2      1       0     0
1-5           8    134     23      5       0     0
5-10          2     18    156     34       2     0
10-50         0      3     28    234      45     3
50-100        0      0      1     42     189    21
>100          0      0      0      2      38   167
```

### Step 6.3: Error Analysis

Identify failure modes:

```python
# Analyze errors
import json

with open('results/test_results.json') as f:
    results = json.load(f)

errors = [r for r in results if r['predicted'] != r['ground_truth']]

# Group by question type
error_types = {}
for err in errors:
    q_type = err['question_type']
    error_types[q_type] = error_types.get(q_type, 0) + 1

print("Errors by type:")
for t, count in sorted(error_types.items()):
    print(f"  {t}: {count}")
```

Common error patterns:
- **Object detection**: Confusion with similar classes (e.g., "tree" vs "forest")
- **Counting**: Underestimation for dense objects
- **Spatial**: Boundary cases (objects exactly at threshold distance)
- **Attributes**: Confusion between similar colors (e.g., "green" vs "dark green")

---

## 📝 Phase 7: Iteration and Improvement

### Iteration 1: Data Augmentation

If performance is low, add:
- More diverse geographic locations
- More examples of underrepresented classes
- More complex questions

### Iteration 2: Model Improvements

Try:
- Different visual backbones (ResNet-101, EfficientNet)
- Attention mechanisms
- Multi-scale feature fusion
- Curriculum learning (easy → hard questions)

### Iteration 3: Question Refinement

Based on errors:
- Rephrase ambiguous questions
- Add more negative examples
- Balance answer distributions
- Add more spatial relationship examples

---

## 📊 Expected Timeline

| Phase | Time Estimate | Parallelizable? |
|-------|--------------|----------------|
| Data Collection (GEE download) | 1-2 days | Yes (per location) |
| Preprocessing (tiling) | 2-4 hours | Yes (per location) |
| Annotation (1000 images, 10 Q/image) | 5-10 days | Yes (multiple annotators) |
| Dataset Splitting | 30 minutes | No |
| Training Experiment 1 | 6-12 hours | No |
| Training Experiment 2 | 6-12 hours | No |
| Training Experiment 3 | 6-12 hours | No |
| Training Experiment 4 | 6-12 hours | No |
| Training Multi-task | 8-16 hours | No |
| Evaluation & Analysis | 1-2 days | No |
| **Total** | **2-3 weeks** | |

With parallel annotation (3-4 people): **1-2 weeks**

---

## 🎯 Success Criteria

Your dataset is ready for publication/use when:

- [ ] ≥1000 images from ≥5 diverse locations
- [ ] ≥10,000 total questions
- [ ] Balanced question type distribution (20-30% each)
- [ ] Balanced answer distribution (not >70% single answer)
- [ ] Clear train/val/test splits by location
- [ ] Test set accuracy >60% for multi-task model
- [ ] Per-question-type accuracy >55%
- [ ] Documented annotation guidelines
- [ ] Quality control passed (random sample review)

---

## 🛠️ Troubleshooting

### Issue: Too many low-quality tiles rejected

**Solution**: Adjust quality thresholds in `prepare_sentinel2_data.py`:
```python
preprocessor = Sentinel2Preprocessor(
    patch_size=256,
    min_mean=20,  # Lower threshold
    max_mean=235   # Higher threshold
)
```

### Issue: Imbalanced question types

**Solution**: Manually add underrepresented questions using annotation helper:
```bash
python annotation_helper.py --mode interactive
# Focus on underrepresented types
```

### Issue: Poor spatial relationship accuracy

**Possible causes**:
1. Ambiguous distance thresholds → Document clear thresholds
2. Data augmentation rotating directional questions → Mark as non-augmentable
3. Inconsistent annotation → Re-annotate with stricter guidelines

### Issue: Model not converging

**Solutions**:
1. Check data loading: Verify images load correctly
2. Reduce learning rate: Try 0.000001
3. Increase batch size: Try 100
4. Check question encoding: Ensure vocabulary covers all words

---

## 📚 Additional Resources

**Files Created**:
- `ANNOTATION_GUIDE.md` - Detailed annotation instructions
- `prepare_sentinel2_data.py` - Data preprocessing script
- `annotation_helper.py` - Semi-automated annotation
- `create_dataset_splits.py` - Geographic splitting
- This workflow guide

**Original RSVQA Resources**:
- Paper: Lobry et al. (2020) IEEE TGRS
- Dataset specification: `AutomaticDB/DataSpecification.md`
- Original code: `AutomaticDB/` and `VQA_model/`

**External Resources**:
- Google Earth Engine: https://earthengine.google.com
- Sentinel-2 documentation: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
- OpenStreetMap: https://www.openstreetmap.org (for ground truth verification)

---

## 🎉 Next Steps

1. **Start with Phase 1**: Download Sentinel-2 data for 2-3 locations
2. **Test preprocessing**: Run `prepare_sentinel2_data.py` on one location
3. **Pilot annotation**: Annotate 50 images to refine workflow
4. **Scale up**: Once workflow is smooth, scale to full dataset
5. **Train baseline**: Train on small subset first (10% of data)
6. **Iterate**: Based on results, improve data and model

**Good luck with your RSVQA dataset creation! 🛰️**

For questions or issues, refer to:
- Original repository: https://github.com/syvlo/RSVQA
- This workflow guide
- Individual script documentation
