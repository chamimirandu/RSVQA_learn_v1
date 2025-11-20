# RSVQA Custom Dataset Annotation Guide

## Overview
This guide provides step-by-step instructions for annotating Sentinel-2 imagery for four types of visual question answering tasks.

---

## 1. OBJECT DETECTION: "Is there a X?"

### Question Format
- "Is there a [object]?"
- "Is a [object] present?"
- "Is there a [object] in the image?"
- "Can you see a [object]?"

### Answer Format
- **Binary**: `"yes"` or `"no"`

### Annotation Steps

1. **Identify Objects in Image**
   - Manual visual inspection of 256×256 Sentinel-2 patch
   - Use high-resolution imagery (Google Earth) as reference if needed
   - List all visible object classes

2. **Object Classes to Consider**
   ```
   - Buildings (residential, commercial, industrial)
   - Roads (highway, primary, secondary, residential)
   - Water bodies (river, lake, reservoir, pond)
   - Vegetation (forest, trees, grass, farmland)
   - Urban features (parking lot, airport, stadium)
   - Industrial (factory, warehouse, solar farm, wind turbine)
   ```

3. **Create Balanced Questions**
   - Generate 50% positive ("yes") questions
   - Generate 50% negative ("no") questions
   - For each image, create 5-10 presence questions

4. **JSON Structure**
   ```json
   {
     "id": 1,
     "img_id": 1,
     "type": "presence",
     "question": "Is there a building?",
     "answers_ids": [1],
     "active": true
   }
   ```

### Annotation Best Practices
- ✅ Object must be clearly visible in Sentinel-2 resolution
- ✅ Consider partial objects (≥30% visible → "yes")
- ✅ Multiple instances of same object → "yes"
- ❌ Don't guess based on context alone
- ❌ Don't include objects smaller than 2-3 pixels

---

## 2. COUNTING: "How many X?"

### Question Format
- "How many [objects] are there?"
- "What is the number of [objects]?"
- "How many [objects] can you count?"
- "What is the amount of [objects]?"

### Answer Format (Discretized Ranges)
For Sentinel-2 (256×256), use ranges:
- `"0"` - No objects
- `"between 1 and 5"`
- `"between 5 and 10"`
- `"between 10 and 50"`
- `"between 50 and 100"`
- `"more than 100"`

**OR** Use exact counts for small numbers:
- `"0"`, `"1"`, `"2"`, `"3"`, ..., `"10"`, then ranges

### Annotation Steps

1. **Count Visible Objects**
   - Manual count for <20 objects
   - Estimate for 20-100 objects (use grid overlay)
   - Estimate ranges for >100 objects

2. **Countable Object Classes**
   ```
   Easy to count:
   - Buildings
   - Large vehicles
   - Trees (isolated)
   - Wind turbines
   - Solar panels (groups)
   - Ships/boats

   Hard to count (avoid or use ranges):
   - Small vegetation patches
   - Individual cars in parking lots
   - Pixels in land cover
   ```

3. **Counting Guidelines**
   - Count only fully + partially visible objects (≥50% visible)
   - For dense clusters, estimate by sampling small area × total area
   - When uncertain, use wider range category

4. **JSON Structure**
   ```json
   {
     "id": 2,
     "img_id": 1,
     "type": "count",
     "question": "How many buildings are there?",
     "answers_ids": [2],
     "active": true
   }
   ```
   ```json
   {
     "id": 2,
     "answer": "between 10 and 50",
     "question_id": 2
   }
   ```

### Annotation Best Practices
- ✅ Use consistent counting rules across all images
- ✅ Document counting methodology in notes
- ✅ Create range categories appropriate for image scale
- ❌ Don't mix exact counts with ranges inconsistently
- ❌ Don't count objects <2 pixels in size

---

## 3. SPATIAL RELATIONSHIPS: "Is X near Y?"

### Question Format
- "Is [object1] near [object2]?"
- "Is [object1] next to [object2]?"
- "Is [object1] adjacent to [object2]?"
- "Is [object1] close to [object2]?"
- "Is [object1] far from [object2]?"

**Directional variants:**
- "Is [object1] north/south/east/west of [object2]?"
- "Is [object1] above/below [object2]?"
- "Is [object1] to the left/right of [object2]?"

**Distance variants:**
- "What is the distance between [object1] and [object2]?"

### Answer Format
- **Binary**: `"yes"` or `"no"` for relationship questions
- **Distance**: `"close"`, `"near"`, `"far"` (qualitative)
- **Distance**: `"less than 50m"`, `"between 50m and 100m"`, etc. (quantitative)

### Annotation Steps

1. **Define Spatial Thresholds**
   For 256×256 Sentinel-2 at 10m resolution (2560m × 2560m area):
   ```
   - "near/adjacent": 0-50m (0-5 pixels)
   - "close": 50-200m (5-20 pixels)
   - "far": >200m (>20 pixels)

   Directional (using image center as reference):
   - "north": upper half of image
   - "south": lower half
   - "east": right half
   - "west": left half
   ```

2. **Identify Object Pairs**
   - Select prominent objects in image
   - Create pairs with clear spatial relationships
   - Include both positive and negative examples

3. **Relationship Types to Annotate**
   ```
   Proximity:
   - Building near road
   - Trees near water
   - Parking lot adjacent to building

   Directional:
   - Forest north of city
   - River east of highway
   - Building left of road

   Containment:
   - Trees inside park
   - Car in parking lot
   - Building in residential area
   ```

4. **JSON Structure**
   ```json
   {
     "id": 3,
     "img_id": 1,
     "type": "relation",
     "question": "Is the building near the road?",
     "answers_ids": [3],
     "active": true
   }
   ```

### Annotation Best Practices
- ✅ **IMPORTANT**: Mark questions as non-augmentable if they use directional terms (left/right/north/south)
- ✅ Use consistent distance thresholds across dataset
- ✅ Consider edge-to-edge distance (not center-to-center)
- ✅ Document threshold definitions in dataset metadata
- ❌ Don't use directional questions if image can be rotated during augmentation
- ❌ Don't compare objects not visible in same image

### **Special Note on Data Augmentation**
From `VQALoader.py:70-78`, the model applies random rotations/flips during training. **You must mark spatial relationship questions appropriately:**

```python
# In images.json, add metadata:
{
  "id": 1,
  "questions_ids": [1, 2, 3],
  "augmentable_questions": [1, 2],  # Only non-directional questions
  "non_augmentable_questions": [3]  # Directional questions excluded from rotation
}
```

---

## 4. ATTRIBUTES: "What color is X?"

### Question Format
- "What color is the [object]?"
- "What is the color of the [object]?"
- "What type of [object] is this?"
- "What is the land use?"
- "What material is the [object]?"

### Answer Format
**Color answers:**
- `"red"`, `"blue"`, `"green"`, `"yellow"`, `"white"`, `"gray"`, `"brown"`, `"black"`
- Composite: `"dark green"`, `"light blue"`, `"reddish brown"`

**Type answers:**
- Land use: `"residential"`, `"commercial"`, `"industrial"`, `"agricultural"`, `"forest"`, `"water"`
- Building type: `"house"`, `"apartment"`, `"warehouse"`, `"factory"`, `"office"`
- Road type: `"highway"`, `"street"`, `"path"`, `"dirt road"`

### Annotation Steps

1. **Identify Prominent Objects**
   - Select objects large enough for color determination at 10m resolution
   - Buildings, roads, water bodies, large vegetation areas

2. **Color Annotation Guidelines**

   **Sentinel-2 RGB Color Interpretation:**
   ```
   Urban/Built:
   - Residential buildings: gray, white, brown, red roofs
   - Commercial buildings: white, gray, metallic
   - Roads: dark gray, black, light gray (concrete)
   - Parking lots: gray, black

   Natural:
   - Healthy vegetation: dark green, green
   - Dry vegetation: yellow, brown, tan
   - Water: blue, dark blue, blue-green
   - Soil: brown, reddish brown, tan
   - Sand: light tan, white, yellow

   Industrial:
   - Factories: gray, white, metallic
   - Solar panels: dark blue, black
   - Greenhouses: white, transparent
   ```

3. **Create Attribute Questions**
   ```
   Color:
   - "What color is the roof?"
   - "What is the color of the water?"
   - "What color is the vegetation?"

   Type:
   - "What type of land use is visible?"
   - "What kind of building is this?"
   - "What type of road is present?"

   Material:
   - "What material is the roof?" (metal, tile, asphalt)
   - "What is the road surface?" (asphalt, concrete, dirt)
   ```

4. **JSON Structure**
   ```json
   {
     "id": 4,
     "img_id": 1,
     "type": "attribute",
     "question": "What color is the building roof?",
     "answers_ids": [4],
     "active": true
   }
   ```
   ```json
   {
     "id": 4,
     "answer": "red",
     "question_id": 4
   }
   ```

### Annotation Best Practices
- ✅ Use dominant color if object has multiple colors
- ✅ Consider spectral characteristics of Sentinel-2 (not true RGB)
- ✅ Create color vocabularies appropriate for satellite imagery
- ✅ Use type/category questions when color is ambiguous
- ❌ Don't use too fine-grained color distinctions
- ❌ Don't ask about colors of objects <5×5 pixels

---

## Annotation Workflow

### **Step 1: Image Preparation**
```bash
# Download Sentinel-2 from GEE
# Tile into 256×256 patches
# Reproject to EPSG:3857
# Filter by quality (mean pixel 30-225)
```

### **Step 2: Create JSON Files**

**images.json template:**
```json
{
  "images": [
    {
      "id": 1,
      "date_added": 1700000000,
      "original_name": "location1_tile001.tif",
      "sensor": "Sentinel-2",
      "upperleft_map_x": 1234567.89,
      "upperleft_map_y": 9876543.21,
      "res_x": 10.0,
      "res_y": 10.0,
      "people_id": 1,
      "type": "Multispectral",
      "questions_ids": [1, 2, 3, 4, 5],
      "active": true
    }
  ]
}
```

**questions.json template:**
```json
{
  "questions": [
    {
      "id": 1,
      "date_added": 1700000000,
      "img_id": 1,
      "people_id": 1,
      "type": "presence",
      "question": "Is there a building?",
      "answers_ids": [1],
      "active": true
    },
    {
      "id": 2,
      "img_id": 1,
      "people_id": 1,
      "type": "count",
      "question": "How many buildings are there?",
      "answers_ids": [2],
      "active": true
    }
  ]
}
```

**answers.json template:**
```json
{
  "answers": [
    {
      "id": 1,
      "date_added": 1700000000,
      "question_id": 1,
      "people_id": 1,
      "answer": "yes",
      "active": true
    },
    {
      "id": 2,
      "date_added": 1700000000,
      "question_id": 2,
      "people_id": 1,
      "answer": "between 10 and 50",
      "active": true
    }
  ]
}
```

### **Step 3: Train/Val/Test Split**

Split at the **tile level** (not patch level) to ensure geographic diversity:

```python
# Example split ratios:
Train: 70% of tiles (diverse locations)
Validation: 15% of tiles (different geographic areas from train)
Test: 15% of tiles (held-out geographic regions)

# Create separate JSON files:
- train_images.json, train_questions.json, train_answers.json
- val_images.json, val_questions.json, val_answers.json
- test_images.json, test_questions.json, test_answers.json
```

---

## Recommended Number of Samples

For each experiment type, aim for:

| Question Type | Min Questions | Recommended | Images |
|--------------|---------------|-------------|--------|
| **Object Detection** | 10,000 | 50,000+ | 1,000+ |
| **Counting** | 5,000 | 25,000+ | 500+ |
| **Spatial Relations** | 5,000 | 20,000+ | 500+ |
| **Attributes** | 5,000 | 20,000+ | 500+ |

**Per image:** Generate 5-15 questions to ensure diversity

---

## Quality Control Checklist

- [ ] All images are 256×256 pixels, 3-channel RGB
- [ ] Mean pixel values are 30-225
- [ ] All questions have clear, unambiguous answers
- [ ] Balanced positive/negative examples for binary questions
- [ ] Consistent annotation rules applied across all images
- [ ] Train/val/test sets have no geographic overlap
- [ ] All JSON files validate against schema
- [ ] Question vocabulary limited to reasonable size (<5000 unique words)
- [ ] Answer vocabulary limited to most common answers (<100 unique answers)
- [ ] Directional questions marked as non-augmentable

---

## Tools & Resources

### Annotation Tools
1. **QGIS** - View Sentinel-2 imagery with coordinates
2. **LabelImg** - Bounding box annotation (if needed for object detection)
3. **Custom scripts** - Use provided `AutomaticDB/ConstructQuestions.py` as template
4. **OpenStreetMap** - Verify ground truth features

### Reference Data
- Google Earth Engine (Sentinel-2 download)
- OpenStreetMap (building/road footprints)
- High-resolution imagery (validation)

### Python Libraries
```bash
pip install rasterio numpy pillow tqdm
```

---

## Automation Recommendations

### Semi-Automatic Annotation Pipeline

1. **Extract OSM features** (if available for your regions)
   ```python
   # Use process.py methods:
   # - getData() for OSM intersection
   # - checkImage() for quality control
   ```

2. **Generate initial questions** automatically
   ```python
   # Use ConstructQuestions.py as template
   # Adapt for your object classes
   ```

3. **Manual review and refinement**
   - Verify automatically generated annotations
   - Add complex spatial relationships manually
   - Add attribute questions manually

4. **Quality validation**
   ```python
   # Check for:
   # - Duplicate questions
   # - Imbalanced answer distributions
   # - Vocabulary coverage
   ```

---

## Next Steps

1. **Download Sentinel-2 patches** from GEE for your geographic locations
2. **Preprocess images** (tile, reproject, quality filter)
3. **Start with one question type** (e.g., object detection) for 100 images
4. **Test annotation workflow** and refine procedures
5. **Scale up annotation** to full dataset
6. **Train initial model** to validate dataset quality
7. **Iterate** based on model performance

---

## Contact & Support

For questions about this annotation guide or the RSVQA framework, refer to:
- Original paper: Lobry et al. (2020) - IEEE TGRS
- Repository: https://github.com/syvlo/RSVQA
- Dataset specification: `AutomaticDB/DataSpecification.md`

---

**Good luck with your annotation! 🛰️**
