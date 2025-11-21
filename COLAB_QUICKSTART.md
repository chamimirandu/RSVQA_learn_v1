# Running RSVQA Scripts in Google Colab

This guide shows you how to run the RSVQA Python scripts in Google Colab.

---

## 🚀 Quick Start (3 Steps)

### Method 1: Use the Pre-Built Notebook (Recommended)

1. **Open Google Colab**: https://colab.research.google.com/
2. **Upload the notebook**: `GEE_OSM_Downloader_Colab.ipynb`
3. **Run all cells**: Click Runtime → Run all

That's it! The notebook includes everything pre-configured.

---

## 🔧 Method 2: Run Scripts in a New Colab Notebook

If you want to run individual scripts, follow these steps:

### Step 1: Setup in Colab

Create a new Colab notebook and run these cells:

```python
# Cell 1: Clone the repository
!git clone https://github.com/chamimirandu/RSVQA_learn_v1.git
%cd RSVQA_learn_v1
!ls -la
```

```python
# Cell 2: Install dependencies
!pip install earthengine-api geemap rasterio geopandas osmnx --quiet
print("✓ Packages installed!")
```

```python
# Cell 3: Authenticate with Google Earth Engine
import ee

try:
    ee.Initialize()
    print("✓ Already authenticated!")
except:
    print("Authenticating...")
    ee.Authenticate()
    ee.Initialize()
    print("✓ Authentication successful!")
```

---

### Step 2: Run Download Scripts

**Option A: Download with OSM data (Full pipeline)**

```python
# Download cloud-free Sentinel-2 + OSM data
from colab_gee_osm_downloader import CoLabGEEOSMDownloader
import json

# Initialize downloader
downloader = CoLabGEEOSMDownloader(output_dir="./downloads")

# Download Manhattan as example
result = downloader.process_location(
    name='manhattan_test',
    bbox=[-74.02, 40.75, -73.97, 40.80],  # [min_lon, min_lat, max_lon, max_lat]
    cloud_percentage=10,
    scale=10  # 10m resolution
)

print("\nResult:")
print(json.dumps(result, indent=2))
```

**Option B: Just Sentinel-2 images**

```python
# If you just need satellite images
!python download_sentinel2_gee.py --interactive
```

Or use predefined locations:

```python
!python batch_download_locations.py
```

---

### Step 3: Process and Prepare Data

**Tile images into patches:**

```python
!python prepare_sentinel2_data.py \
    --input_dir ./downloads/images \
    --output_dir ./dataset/tiles \
    --patch_size 256
```

**Create dataset splits:**

```python
!python create_dataset_splits.py \
    --data_dir ./dataset/tiles \
    --output_dir ./dataset/splits \
    --train_ratio 0.7 \
    --val_ratio 0.15 \
    --test_ratio 0.15
```

---

## 📍 Downloading Multiple Locations

### Example: Batch Download 5 Diverse Locations

```python
from colab_gee_osm_downloader import CoLabGEEOSMDownloader
import time

downloader = CoLabGEEOSMDownloader(output_dir="./downloads")

# Define your locations
locations = [
    {
        'name': 'manhattan_nyc',
        'bbox': [-74.02, 40.75, -73.97, 40.80],
        'cloud_percentage': 10,
        'description': 'Urban - Manhattan'
    },
    {
        'name': 'iowa_farmland',
        'bbox': [-93.65, 41.55, -93.55, 41.65],
        'cloud_percentage': 10,
        'description': 'Agricultural - Iowa'
    },
    {
        'name': 'arizona_desert',
        'bbox': [-111.75, 33.45, -111.65, 33.55],
        'cloud_percentage': 5,
        'description': 'Desert - Arizona'
    },
    {
        'name': 'san_francisco_bay',
        'bbox': [-122.45, 37.75, -122.35, 37.85],
        'cloud_percentage': 10,
        'description': 'Coastal - San Francisco'
    },
    {
        'name': 'amazon_rainforest',
        'bbox': [-60.1, -3.1, -60.0, -3.0],
        'cloud_percentage': 20,
        'description': 'Rainforest - Amazon'
    }
]

# Download all locations
results = []
for loc in locations:
    print(f"\n{'='*60}")
    print(f"Processing: {loc['name']}")
    print(f"Description: {loc['description']}")
    print(f"{'='*60}")

    result = downloader.process_location(
        name=loc['name'],
        bbox=loc['bbox'],
        cloud_percentage=loc['cloud_percentage'],
        scale=10
    )

    results.append(result)
    print(f"Status: {result['status']}")

    # Respect API rate limits
    time.sleep(3)

# Summary
print("\n" + "="*60)
print("DOWNLOAD SUMMARY")
print("="*60)
successful = [r for r in results if r['status'] == 'success']
print(f"Total: {len(results)}")
print(f"Successful: {len(successful)}")
print(f"Failed: {len(results) - len(successful)}")
```

---

## 📊 Visualizing Results in Colab

### View Satellite Image

```python
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np

# Install visualization packages
!pip install rasterio matplotlib --quiet

# Load and display image
with rasterio.open('downloads/images/manhattan_test.tif') as src:
    rgb = src.read([1, 2, 3])  # RGB bands
    rgb = np.transpose(rgb, (1, 2, 0))
    rgb_norm = np.clip(rgb / 3000 * 255, 0, 255).astype(np.uint8)

    plt.figure(figsize=(12, 12))
    plt.imshow(rgb_norm)
    plt.title('Cloud-Free Sentinel-2 Image', fontsize=16)
    plt.axis('off')
    plt.show()
```

### View OSM Data

```python
import json
from collections import Counter

# Load OSM GeoJSON
with open('downloads/osm_data/manhattan_test_osm.geojson', 'r') as f:
    osm_data = json.load(f)

print(f"Total OSM features: {len(osm_data['features'])}")

# Count feature types
feature_types = []
for feature in osm_data['features']:
    props = feature['properties']
    for key in ['building', 'highway', 'landuse', 'natural', 'amenity']:
        if key in props:
            feature_types.append(f"{key}={props[key]}")
            break

counts = Counter(feature_types)
print("\nTop 10 OSM features:")
for feature, count in counts.most_common(10):
    print(f"  {feature}: {count}")
```

---

## 💾 Download Results from Colab

After processing, download your data:

```python
# Zip all results
!zip -r my_rsvqa_data.zip downloads/

# Download to your computer
from google.colab import files
files.download('my_rsvqa_data.zip')
```

---

## 🎯 Complete Workflow Example

Here's a complete notebook workflow from download to dataset creation:

```python
# === CELL 1: Setup ===
!git clone https://github.com/chamimirandu/RSVQA_learn_v1.git
%cd RSVQA_learn_v1
!pip install earthengine-api geemap rasterio geopandas osmnx --quiet

# === CELL 2: Authenticate GEE ===
import ee
ee.Authenticate()
ee.Initialize()

# === CELL 3: Download Data ===
from colab_gee_osm_downloader import CoLabGEEOSMDownloader

downloader = CoLabGEEOSMDownloader(output_dir="./downloads")

result = downloader.process_location(
    name='my_area',
    bbox=[-122.5, 37.7, -122.4, 37.8],  # Your coordinates
    cloud_percentage=10,
    scale=10
)

print(f"Download status: {result['status']}")

# === CELL 4: Verify Downloads ===
!ls -lh downloads/images/
!ls -lh downloads/osm_data/

# === CELL 5: Tile Images ===
!python prepare_sentinel2_data.py \
    --input_dir ./downloads/images \
    --output_dir ./dataset/tiles \
    --patch_size 256

# === CELL 6: Create Splits ===
!python create_dataset_splits.py \
    --data_dir ./dataset/tiles \
    --output_dir ./dataset/splits

# === CELL 7: Download Results ===
!zip -r dataset.zip dataset/
from google.colab import files
files.download('dataset.zip')
```

---

## 🔍 Finding Your Own Coordinates

Use these tools to find bounding boxes:

1. **BoundingBox Tool**: https://boundingbox.klokantech.com/
   - Draw a box on the map
   - Copy coordinates in CSV format: `min_lon,min_lat,max_lon,max_lat`

2. **Google Maps**:
   - Right-click → "What's here?"
   - Get lat/lon for corners

3. **GeoJSON.io**: https://geojson.io/
   - Draw rectangle
   - Copy coordinates from JSON

**Example**: For San Francisco Bay Area:
```python
bbox = [-122.5, 37.7, -122.4, 37.8]  # [min_lon, min_lat, max_lon, max_lat]
```

---

## 🚨 Troubleshooting in Colab

### Issue: GEE Authentication Fails

```python
# Force re-authentication
import ee
ee.Authenticate(force=True)
ee.Initialize()
```

### Issue: Out of Memory

```python
# Use smaller patch size or fewer locations
!python prepare_sentinel2_data.py \
    --input_dir ./downloads/images \
    --output_dir ./dataset/tiles \
    --patch_size 128  # Smaller patches
```

### Issue: Download Timeout

```python
# Process locations one at a time
# Add delays between requests
import time
time.sleep(5)  # Wait 5 seconds between downloads
```

### Issue: Module Not Found

```python
# Reinstall packages
!pip uninstall -y earthengine-api geemap
!pip install earthengine-api geemap --upgrade
```

---

## 📚 What Each Script Does

| Script | Purpose | Use in Colab |
|--------|---------|--------------|
| `colab_gee_osm_downloader.py` | Download Sentinel-2 + OSM data | ✅ Best for Colab |
| `download_sentinel2_gee.py` | Download only Sentinel-2 | ✅ Works in Colab |
| `batch_download_locations.py` | Download predefined locations | ✅ Works in Colab |
| `prepare_sentinel2_data.py` | Tile images into patches | ✅ Works in Colab |
| `create_dataset_splits.py` | Create train/val/test splits | ✅ Works in Colab |
| `annotation_helper.py` | Generate questions from OSM | ✅ Works in Colab |
| `train.py` | Train VQA model | ⚠️ Needs GPU runtime |

---

## 🎓 Recommended Workflow for Beginners

1. **Start with the notebook**: `GEE_OSM_Downloader_Colab.ipynb`
2. **Download 1-2 test locations** to understand the process
3. **Verify the downloads** look correct
4. **Scale up** to 5-10 diverse locations
5. **Process and create dataset**
6. **Train model** (use GPU runtime)

---

## 💡 Pro Tips

1. **Enable GPU**: Runtime → Change runtime type → GPU (for model training)
2. **Mount Google Drive**: Save downloads to Drive to avoid losing data
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
3. **Use smaller areas first**: Test with 0.05° × 0.05° boxes before larger areas
4. **Check free disk space**:
   ```python
   !df -h
   ```
5. **Save metadata**: Always review the `*_metadata.json` files

---

## 📞 Need Help?

Check these guides in the repository:
- `PHASE1_DOWNLOAD_GUIDE.md` - Detailed download instructions
- `ANNOTATION_GUIDE.md` - Creating questions
- `MULTITASK_TRAINING_GUIDE.md` - Training models
- `README.md` - Project overview

---

## ✅ Quick Verification Checklist

Before moving to next steps:

- [ ] GEE authenticated successfully
- [ ] Downloaded at least 1 location
- [ ] Image files exist in `downloads/images/`
- [ ] OSM data exists in `downloads/osm_data/`
- [ ] Metadata files look correct
- [ ] Images visualize correctly
- [ ] No error messages in outputs

---

Happy coding! 🛰️🚀
