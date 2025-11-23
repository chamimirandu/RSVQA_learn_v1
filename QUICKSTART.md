# RSVQA Quick Start Guide

## I have GEE data - what do I do now?

Follow these steps to get started quickly:

### Step 1: Inspect Your Data (5 minutes)

First, place your Google Earth Engine images in the `data/images/` directory:

```bash
# Copy your GEE images to the data directory
cp /path/to/your/gee/images/*.tif data/images/

# Inspect your images
python inspect_gee_data.py
```

This will show you:
- How many images you have
- Image dimensions and bands
- Whether they're georeferenced
- Data types and value ranges

### Step 2: Choose Your Approach

Based on your images and goals, choose one:

#### 🟢 **Option A: Simple Start (Recommended)**

**Best for:**
- Quick experimentation
- Learning RSVQA concepts
- Small-scale projects (< 1000 images)
- No database setup needed

**Steps:**
1. Manually create question-answer pairs
2. Train the VQA model
3. Start answering questions!

**Time:** 1-2 hours to get started

---

#### 🔵 **Option B: Full Pipeline**

**Best for:**
- Large-scale projects (1000+ images)
- Automatic QA pair generation
- Production systems
- Research projects

**Steps:**
1. Set up PostgreSQL database
2. Import OpenStreetMap data
3. Automatically generate QA pairs
4. Train the VQA model

**Time:** 4-8 hours for full setup

---

### Step 3: Set Up Environment (30 minutes)

```bash
# Run the setup script
./setup_environment.sh

# OR manually install dependencies
pip install -r requirements.txt
pip install torch torchvision
pip install rasterio psycopg2-binary shapely  # For Option B
```

### Step 4A: Simple Approach - Create QA Pairs

1. Look at the example template:
```bash
cat data/questions/example_qa_template.json
```

2. Create your own QA pairs for your images:
```json
[
    {
        "image_id": "my_gee_image_001",
        "image_filename": "my_gee_image_001.tif",
        "question": "Is there vegetation in the image?",
        "answer": "yes",
        "question_type": "presence",
        "answer_type": "binary"
    }
]
```

3. Save as `data/questions/my_qa_pairs.json`

### Step 4B: Full Pipeline - Automatic Generation

See `GETTING_STARTED.md` → Option B for detailed instructions.

### Step 5: Train the Model

```bash
cd VQA_model

# Make sure you have seq2vec.py
ls models/seq2vec.py

# If not, download it:
cd models
wget https://raw.githubusercontent.com/Cadene/vqa.pytorch/master/vqa/models/seq2vec.py
cd ..

# Train the model
python train.py --data_path ../data/questions/my_qa_pairs.json
```

## Common Question Types for Remote Sensing

Your RSVQA system can answer questions like:

**Presence Questions:**
- "Is there water in the image?"
- "Are there buildings visible?"
- "Is there a road present?"

**Count Questions:**
- "How many buildings are there?"
- "How many roads intersect?"

**Area/Coverage Questions:**
- "What is the dominant land cover type?"
- "What percentage is urban?"
- "Is this primarily forest or agriculture?"

**Comparison Questions:**
- "Is there more water or land?"
- "Are there more buildings in the north or south?"

## Tips for GEE Data

1. **Image Format:**
   - GeoTIFF (.tif) is best for georeferenced data
   - JPEG/PNG work but lose spatial information

2. **Image Size:**
   - 256x256 to 512x512 pixels is ideal for training
   - Larger images may need to be tiled

3. **Bands:**
   - RGB (3 bands) works out of the box
   - For multispectral (>3 bands), you may need to modify the model

4. **Preprocessing:**
   - Normalize pixel values to [0, 1] or [-1, 1]
   - Consider histogram equalization for better visualization

## Directory Structure

```
RSVQA_learn_v1/
├── data/
│   ├── images/           ← Put your GEE images here
│   ├── questions/        ← QA pairs go here
│   └── models/           ← Trained models saved here
├── AutomaticDB/          ← Automatic QA generation
├── VQA_model/            ← Model training and inference
├── GETTING_STARTED.md    ← Detailed guide
├── QUICKSTART.md         ← This file
└── inspect_gee_data.py   ← Data inspection tool
```

## Troubleshooting

**"No images found"**
- Check that images are in `data/images/`
- Verify file extensions (.tif, .jpg, .png)

**"Module not found"**
- Activate conda environment: `conda activate rsvqa`
- Install missing package: `pip install <package_name>`

**"CUDA out of memory"**
- Reduce batch size in training
- Use smaller images
- Train on CPU (slower but works)

**"Can't read GeoTIFF"**
- Install rasterio: `pip install rasterio`
- Check that file is not corrupted

## Need More Help?

1. Read `GETTING_STARTED.md` for detailed instructions
2. Check the research papers in the repository
3. Review the original code documentation

## What's Next?

After training your model:
1. Test it on new images
2. Evaluate accuracy on a test set
3. Fine-tune hyperparameters
4. Scale up your dataset
5. Deploy as a web service

Good luck building your RSVQA system! 🚀🛰️
