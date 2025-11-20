# Quick Start Guide for Custom RSVQA Dataset Creation

This is your quick reference for creating a custom RSVQA dataset with Sentinel-2 imagery.

---

## 📚 Documentation Files Created

| File | Purpose |
|------|---------|
| **CUSTOM_DATASET_WORKFLOW.md** | Complete end-to-end workflow (START HERE!) |
| **ANNOTATION_GUIDE.md** | Detailed annotation instructions for all 4 question types |
| **MULTITASK_TRAINING_GUIDE.md** | Training individual vs combined models |
| **QUICK_START.md** | This file - quick reference |

---

## 🛠️ Tools & Scripts Created

| Script | Purpose | Usage |
|--------|---------|-------|
| **prepare_sentinel2_data.py** | Tile Sentinel-2 images to 256×256 | `python prepare_sentinel2_data.py --input_dir ./downloads --output_dir ./dataset` |
| **annotation_helper.py** | Semi-automated question generation | `python annotation_helper.py --mode interactive` |
| **create_dataset_splits.py** | Create train/val/test splits by location | `python create_dataset_splits.py --images_json images.json --questions_json questions.json --answers_json answers.json --output_dir ./splits` |

---

## ⚡ Quick Workflow (TL;DR)

### 1. Download Sentinel-2 from GEE
```javascript
// In Google Earth Engine Code Editor
var roi = ee.Geometry.Rectangle([lon_min, lat_min, lon_max, lat_max]);
var s2 = ee.ImageCollection('COPERNICUS/S2_SR')
  .filterBounds(roi)
  .filterDate('2023-01-01', '2023-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
  .select(['B4', 'B3', 'B2'])
  .median();

Export.image.toDrive({
  image: s2.visualize({min: 0, max: 3000}),
  scale: 10,
  region: roi,
  crs: 'EPSG:3857'
});
```

### 2. Tile Images
```bash
python prepare_sentinel2_data.py \
    --input_dir ./sentinel2_downloads \
    --output_dir ./dataset \
    --patch_size 256
```

### 3. Annotate
```bash
# Interactive annotation
python annotation_helper.py --mode interactive

# Or batch generate templates
python annotation_helper.py \
    --mode batch \
    --images_json dataset/images.json \
    --output_dir dataset/annotations
```

### 4. Create Splits
```bash
python create_dataset_splits.py \
    --images_json dataset/images.json \
    --questions_json dataset/questions.json \
    --answers_json dataset/answers.json \
    --output_dir dataset/splits \
    --train_ratio 0.7 \
    --val_ratio 0.15 \
    --test_ratio 0.15
```

### 5. Train Models

**Individual task training:**
```bash
# Experiment 1: Object Detection
python VQA_model/train.py --task presence --exp_name exp1_detection

# Experiment 2: Counting
python VQA_model/train.py --task count --exp_name exp2_counting

# Experiment 3: Spatial Relations
python VQA_model/train.py --task relation --exp_name exp3_spatial

# Experiment 4: Attributes
python VQA_model/train.py --task attribute --exp_name exp4_attributes
```

**Multi-task training:**
```bash
# Experiment 5: Combined
python VQA_model/train.py --task all --exp_name exp5_multitask
```

---

## 📊 Key Parameters

### Image Specifications
- **Source**: Sentinel-2 from Google Earth Engine
- **Patch size**: 256×256 pixels
- **Format**: 3-channel RGB GeoTIFF (uint8, 0-255)
- **Coordinate system**: EPSG:3857
- **Quality filter**: Mean pixel value 30-225

### Question Types (4 Experiments)
1. **Object Detection** (`presence`): "Is there a X?" → "yes"/"no"
2. **Counting** (`count`): "How many X?" → "between 10 and 50"
3. **Spatial Relations** (`relation`): "Is X near Y?" → "yes"/"no"
4. **Attributes** (`attribute`): "What color is X?" → "green"

### Dataset Size Recommendations
- **Minimum**: 1,000 images, 10,000 questions
- **Recommended**: 2,000+ images, 50,000+ questions
- **Per image**: 5-15 questions
- **Geographic diversity**: 5-10 different locations

### Training Parameters
- **Batch size**: 70
- **Learning rate**: 0.00001
- **Epochs**: 150
- **Optimizer**: Adam
- **Image normalization**: ImageNet statistics

---

## 🎯 Four Question Types - Quick Reference

### 1. Object Detection
```json
Question: "Is there a building?"
Answer: "yes" or "no"
Balance: 50% positive, 50% negative
```

### 2. Counting
```json
Question: "How many buildings are there?"
Answer: "between 10 and 50" (use ranges)
Ranges: 0, 1-5, 5-10, 10-50, 50-100, >100
```

### 3. Spatial Relationships
```json
Question: "Is the building near the road?"
Answer: "yes" or "no"
Thresholds:
  - "near": 0-50m (0-5 pixels)
  - "close": 50-200m (5-20 pixels)
  - "far": >200m (>20 pixels)

⚠️ Mark directional questions (left/right/north/south) as non-augmentable!
```

### 4. Attributes
```json
Question: "What color is the vegetation?"
Answer: "dark green"
Common colors: green, dark green, blue, gray, brown, white, red

Question: "What type of land use is visible?"
Answer: "residential"
Common types: residential, commercial, industrial, agricultural, forest, water
```

---

## 🚨 Common Pitfalls to Avoid

1. **DON'T** randomly split images - split by geographic location!
2. **DON'T** rotate/flip images with directional questions (left/right/north/south)
3. **DON'T** create imbalanced answer distributions (e.g., 90% "yes")
4. **DON'T** use very dark or very bright tiles (mean <30 or >225)
5. **DON'T** forget to validate splits before training
6. **DON'T** mix true RGB with false color composites
7. **DON'T** use inconsistent counting rules across images

---

## ✅ Success Checklist

Before training:
- [ ] Downloaded Sentinel-2 for ≥5 diverse locations
- [ ] Tiled images to 256×256 patches
- [ ] Quality filtered tiles (mean 30-225)
- [ ] Created ≥10,000 questions across 4 types
- [ ] Balanced answer distributions checked
- [ ] Train/val/test split by location (70/15/15)
- [ ] No geographic overlap between splits
- [ ] Annotation quality spot-checked
- [ ] JSON files validated

After training:
- [ ] Single-task models trained for all 4 tasks
- [ ] Multi-task model trained
- [ ] Test accuracy >60% for multi-task
- [ ] Per-task accuracy >55%
- [ ] Comparison analysis completed
- [ ] Results documented

---

## 📖 Where to Go Next

1. **First time?** → Read `CUSTOM_DATASET_WORKFLOW.md` (complete guide)
2. **Ready to annotate?** → Read `ANNOTATION_GUIDE.md` (detailed instructions)
3. **Training models?** → Read `MULTITASK_TRAINING_GUIDE.md` (experiments)
4. **Quick lookup?** → Stay here!

---

## 🆘 Troubleshooting

### Low quality tiles rejected
```bash
# Adjust thresholds in prepare_sentinel2_data.py
preprocessor = Sentinel2Preprocessor(min_mean=20, max_mean=235)
```

### Imbalanced questions
```bash
# Add more questions of underrepresented types
python annotation_helper.py --mode interactive
# Focus on missing types
```

### Model not converging
```bash
# Try lower learning rate
python VQA_model/train.py --lr 0.000001

# Or increase batch size
python VQA_model/train.py --batch_size 100
```

### Poor spatial relationship accuracy
- Check distance thresholds are consistent
- Verify directional questions aren't being rotated
- Add more training examples

---

## 📞 Support

- **Original RSVQA**: https://github.com/syvlo/RSVQA
- **Paper**: Lobry et al. (2020) - IEEE TGRS
- **Google Earth Engine**: https://earthengine.google.com
- **Sentinel-2 Docs**: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR

---

## 🎯 Estimated Timeline

| Phase | Duration | Parallelizable? |
|-------|----------|----------------|
| Download data (5 locations) | 1-2 days | Yes |
| Tile & preprocess | 2-4 hours | Yes |
| Annotate (1000 images) | 5-10 days | Yes |
| Create splits | 30 min | No |
| Train single-task (×4) | 1-2 days | No |
| Train multi-task | 8-16 hours | No |
| Evaluate & analyze | 1-2 days | No |
| **Total** | **2-3 weeks** | |

With 3-4 annotators working in parallel: **1-2 weeks total**

---

## 🎉 Ready to Start?

1. Open `CUSTOM_DATASET_WORKFLOW.md`
2. Start with Phase 1: Data Collection
3. Follow step-by-step instructions
4. Use scripts provided in this repository
5. Refer back to this Quick Start as needed

**Good luck with your custom RSVQA dataset! 🛰️**
