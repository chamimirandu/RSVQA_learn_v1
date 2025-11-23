# Getting Started with RSVQA System

This guide will help you build a simple RSVQA (Remote Sensing Visual Question Answering) system using your Google Earth Engine data.

## Overview

The RSVQA system has two main components:
1. **AutomaticDB**: Automatically generates question-answer pairs from satellite images using OpenStreetMap (OSM) data
2. **VQA_model**: Trains and runs the VQA model to answer questions about remote sensing images

## Quick Start Options

You have **two approaches** to build your RSVQA system:

### Option A: Simple Approach (Recommended for Beginners)
Use pre-existing RSVQA datasets to train the model without setting up the database pipeline.

### Option B: Full Pipeline
Generate your own question-answer pairs from your GEE images using OSM data.

---

## Option A: Simple Approach (Recommended)

### Step 1: Environment Setup

```bash
# Create a conda environment
conda create --name rsvqa python=3.7
conda activate rsvqa

# Install dependencies
pip install -r requirements.txt

# Install PyTorch (adjust CUDA version as needed)
pip install torch torchvision

# Install skip-thoughts for text encoding
git clone https://github.com/Cadene/skip-thoughts.torch.git
cd skip-thoughts.torch/pytorch
python setup.py install
cd ../..
```

### Step 2: Download seq2vec.py

Download the required `seq2vec.py` file:
```bash
cd VQA_model/models/
wget https://raw.githubusercontent.com/Cadene/vqa.pytorch/master/vqa/models/seq2vec.py
cd ../..
```

### Step 3: Prepare Your GEE Data

Organize your Google Earth Engine images:
```bash
# Create data directory
mkdir -p data/images
mkdir -p data/questions

# Place your GEE images in data/images/
# Images should be in common formats (TIFF, JPEG, PNG)
```

### Step 4: Create Question-Answer Pairs Manually

For a simple system, create a JSON file with questions and answers:

**data/questions/qa_pairs.json**:
```json
[
    {
        "image": "image_001.tif",
        "question": "What is the dominant land cover type?",
        "answer": "forest",
        "question_type": "area"
    },
    {
        "image": "image_001.tif",
        "question": "Is there water present?",
        "answer": "yes",
        "question_type": "presence"
    }
]
```

### Step 5: Train the Model

Modify `VQA_model/train.py` to point to your data and run:
```bash
cd VQA_model
python train.py
```

---

## Option B: Full Pipeline with Automatic QA Generation

This approach automatically generates questions from your images using OSM data.

### Prerequisites
- PostgreSQL database
- PostGIS extension
- OSM data for your region of interest
- Imposm3 for importing OSM data

### Step 1: Set Up PostgreSQL Database

```bash
# Install PostgreSQL and PostGIS
sudo apt-get install postgresql postgresql-contrib postgis

# Create database user
createuser --no-superuser --no-createrole --createdb rsvqa_user

# Create database
createdb -E UTF-8 -O rsvqa_user rsvqa_db

# Enable extensions
psql rsvqa_db -c "CREATE EXTENSION postgis;"
psql rsvqa_db -c "CREATE EXTENSION hstore;"
```

### Step 2: Import OSM Data

1. Download OSM data for your region from http://download.geofabrik.de/

2. Install Imposm3:
```bash
# Install dependencies
sudo apt-get install leveldb

# Install Imposm3 (using Go)
export GOPATH="$HOME/go"
export PATH="$GOPATH/bin:$PATH"
go get github.com/omniscale/imposm3
go install github.com/omniscale/imposm3/cmd/imposm
```

3. Import OSM data to PostgreSQL (see `AutomaticDB/README_PostgreSQL_steps.txt`)

### Step 3: Configure Database Connection

Edit `AutomaticDB/vqa_database.ini`:
```ini
[postgresql]
host=localhost
database=rsvqa_db
user=rsvqa_user
password=your_password

[sentinel_portal]
user=your_sentinel_user
password=your_sentinel_password
```

### Step 4: Prepare GEE Images

Place your Google Earth Engine images in a directory and update the path in `AutomaticDB/process.py` (line 233).

Your images should:
- Be georeferenced (contain spatial information)
- Be in a format readable by rasterio (GeoTIFF recommended)
- Cover areas where you have OSM data

### Step 5: Generate Question-Answer Pairs

```bash
cd AutomaticDB
python process.py
```

This will:
- Read your satellite images
- Intersect them with OSM features (roads, buildings, water bodies, etc.)
- Automatically generate question-answer pairs
- Save the dataset for training

### Step 6: Train the VQA Model

```bash
cd ../VQA_model
python train.py
```

---

## Understanding Your GEE Data

Before proceeding, check your GEE data:

1. **Format**: What format are your images? (GeoTIFF, PNG, JPEG?)
2. **Georeferencing**: Do they have spatial coordinates?
3. **Coverage**: What geographic area do they cover?
4. **Resolution**: What is the spatial resolution?
5. **Bands**: How many spectral bands? (RGB, multispectral?)

Run this to check your data:
```bash
# If you have GeoTIFF files
python -c "
import rasterio
from glob import glob

images = glob('data/images/*.tif')
for img in images[:3]:  # Check first 3 images
    with rasterio.open(img) as src:
        print(f'\n{img}:')
        print(f'  Shape: {src.shape}')
        print(f'  Bands: {src.count}')
        print(f'  CRS: {src.crs}')
        print(f'  Bounds: {src.bounds}')
"
```

---

## Next Steps

1. **Start with Option A** if you're new to RSVQA or want quick results
2. **Move to Option B** when you want to scale up and automatically generate large datasets
3. Check the papers in the repository for detailed methodology:
   - `Lobry et al. - 2020 - RSVQA Visual Question Answering for Remote Sensing Data.pdf`

## Common Questions

**Q: What kinds of questions can the system answer?**
A: The system can answer:
- Presence questions (Is there a road? → yes/no)
- Count questions (How many buildings? → number)
- Area questions (What is the main land cover? → forest/urban/water)
- Comparison questions (Is there more forest or water? → forest)

**Q: How much data do I need?**
A: For initial experimentation, start with 100-500 image-question pairs. For robust performance, 10,000+ pairs are recommended.

**Q: Can I use multispectral satellite data?**
A: Yes! The model can work with multispectral data, but you may need to modify the image preprocessing in the model code.

---

## Troubleshooting

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your images are properly formatted and georeferenced
3. Ensure database connections are configured correctly (for Option B)
4. Review the original papers for detailed specifications

## Resources

- Original paper: Lobry et al., "RSVQA: Visual Question Answering for Remote Sensing Data", IEEE TGRS 2020
- Skip-thoughts: https://github.com/Cadene/skip-thoughts.torch
- VQA baseline: https://github.com/Cadene/vqa.pytorch
