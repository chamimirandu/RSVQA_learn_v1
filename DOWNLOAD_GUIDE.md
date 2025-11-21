# Comprehensive Download Guide for RSVQA Custom Datasets

This guide explains how to download cloud-free Sentinel-2 imagery for creating custom RSVQA datasets.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Cloud Filtering Explained](#cloud-filtering-explained)
3. [Download Methods](#download-methods)
4. [Location Selection Strategy](#location-selection-strategy)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites
```bash
# Install required packages
pip install earthengine-api geemap

# Authenticate with Google Earth Engine
earthengine authenticate
```

### Method 1: Download Remaining 5 Locations (Simplest)

If you've already downloaded the three example locations (New York, Iowa, Amazon), download the remaining 5:

```bash
python batch_download_locations.py --all
```

This will download:
- California Coast (San Francisco Bay)
- Arizona Desert
- Florida Coast
- Chicago Urban
- Yellowstone National Park

**Expected time:** 30-90 minutes total
**Expected output:** 5 GeoTIFF files in `downloads/` directory

---

### Method 2: Download Individual Locations

For more control, download locations one at a time:

```bash
# California Coast (low cloud area)
python download_california_coast.py

# Arizona Desert (very clear skies)
python download_arizona_desert.py

# Florida Coast (tropical, winter months)
python download_florida_coast.py

# Chicago Urban Area
python download_chicago_urban.py

# Yellowstone National Park (summer only)
python download_yellowstone.py
```

**Advantage:** Better error handling for individual locations

---

### Method 3: Custom Location Selection

Download specific locations from the extended catalog:

```bash
# Download specific locations
python batch_download_locations.py \
  --config locations_extended.json \
  --locations tokyo_metropolitan sahara_desert venice_lagoon

# Download all except certain locations
python batch_download_locations.py \
  --config locations_extended.json \
  --all \
  --exclude newyork_manhattan iowa_farmland amazon_rainforest
```

---

## Cloud Filtering Explained

### Why Cloud Filtering Matters

Clouds are the primary obstacle in optical satellite imagery. Our scripts use a **three-layer filtering strategy** to ensure cloud-free images:

### Layer 1: Metadata Filtering
```python
.filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_percentage))
```

- Filters images **before download** based on ESA's cloud assessment
- Each Sentinel-2 image has a metadata field: `CLOUDY_PIXEL_PERCENTAGE`
- We only select images below the threshold (e.g., 10%)
- **Example:** If threshold is 10%, only images with <10% clouds are considered

### Layer 2: SCL Cloud Masking
```python
def mask_clouds(image):
    scl = image.select('SCL')
    # Mask: cloud shadows (3), medium clouds (8), high clouds (9), cirrus (10)
    cloud_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(cloud_mask)
```

- Uses **Scene Classification Layer (SCL)** - a per-pixel cloud classification
- Removes pixels classified as:
  - Cloud shadows (SCL value 3)
  - Medium probability clouds (8)
  - High probability clouds (9)
  - Thin cirrus (10)
- Applied to **every image** in the collection

### Layer 3: Median Compositing
```python
composite = collection.median().clip(roi)
```

- Combines multiple cloud-masked images using **median** statistics
- For each pixel, takes the median value across all dates
- **Effect:** Any remaining cloud pixels (outliers) are automatically eliminated
- **Result:** Seamless, cloud-free composite image

### Visual Example of the Process

```
Original Collection (June-September):
├─ June 5:  [20% clouds] ❌ Filtered out by Layer 1
├─ June 15: [8% clouds]  ✓ Passes Layer 1
│            └─> Layer 2: Masks cloud pixels
│            └─> Contributes to median composite
├─ July 3:  [5% clouds]  ✓ Passes Layer 1
│            └─> Layer 2: Masks cloud pixels
│            └─> Contributes to median composite
├─ July 20: [12% clouds] ❌ Filtered out by Layer 1
├─ Aug 8:   [6% clouds]  ✓ Passes Layer 1
│            └─> Layer 2: Masks cloud pixels
│            └─> Contributes to median composite
└─ Sep 1:   [3% clouds]  ✓ Passes Layer 1
             └─> Layer 2: Masks cloud pixels
             └─> Contributes to median composite

Final Output: Median composite of 4 cloud-free images
```

---

## Cloud Threshold Guidelines by Location Type

| Location Type | Threshold | Reasoning | Examples |
|---------------|-----------|-----------|----------|
| **Desert/Arid** | 3-5% | Year-round clear skies | Arizona, Sahara, Atacama |
| **Temperate Urban** | 10% | Moderate seasonal clouds | New York, Chicago, Tokyo |
| **Mediterranean** | 5-10% | Dry summers, wet winters | California Coast, Dubai |
| **Tropical** | 15-20% | Persistent cloud cover | Amazon, Congo, Florida (summer) |
| **Coastal** | 10-15% | Variable by season | Florida (winter: 15%), SF Bay (5%) |
| **Mountain** | 10-15% | Orographic clouds | Scottish Highlands, Rocky Mountains |
| **Polar/Ice** | 10-15% | Variable conditions | Greenland Ice Sheet |

---

## Download Methods Comparison

| Method | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Batch Script** | Download 5+ locations | Fast, automated, progress tracking | Less customization per location |
| **Individual Scripts** | Learning, testing, single locations | Simple, focused, easy to debug | Manual for multiple locations |
| **Custom Config** | Research project, specific regions | Full control, reproducible | Requires editing JSON |

---

## Location Selection Strategy

### For Training a Good VQA Model

**Minimum Recommended:** 8 locations
**Optimal:** 12-15 locations

### Essential Diversity Dimensions

1. **Land Cover Types**
   - Urban (dense, sparse, coastal)
   - Agricultural (cropland, plantation)
   - Forest (tropical, temperate)
   - Desert/arid
   - Water bodies

2. **Geographic Diversity**
   - Different continents
   - Varying latitudes
   - Coastal vs. inland
   - Flat vs. mountainous

3. **Climate Zones**
   - Tropical
   - Temperate
   - Arid
   - Polar/Alpine

### Pre-Made Location Sets

#### Basic Set (8 locations - 2-3 hours total download)
```bash
# Already defined in locations_example.json
python batch_download_locations.py --all
```
**Includes:** NYC, Iowa, Amazon, SF Bay, Arizona, Florida, Chicago, Yellowstone

#### Global Set (12 locations - 4-6 hours total download)
```bash
python batch_download_locations.py \
  --config locations_extended.json \
  --locations newyork_manhattan tokyo_metropolitan sahara_desert \
               amazon_rainforest great_barrier_reef greenland_ice_sheet \
               nile_delta scottish_highlands iowa_farmland \
               venice_lagoon dubai_urban rocky_mountains
```
**Coverage:** All continents, diverse climates

#### Environmental Monitoring Set (10 locations)
```bash
python batch_download_locations.py \
  --config locations_extended.json \
  --locations amazon_rainforest congo_rainforest palm_oil_plantation \
               greenland_ice_sheet patagonia_glaciers great_barrier_reef \
               nile_delta bangladesh_delta windmills_netherlands grand_canyon
```
**Focus:** Climate change, deforestation, glaciers, agriculture

---

## Advanced Options

### Override Cloud Threshold Globally

```bash
# Use 20% cloud threshold for all locations (more permissive)
python batch_download_locations.py --all --max-cloud 20

# Use 5% cloud threshold (stricter, may fail for some locations)
python batch_download_locations.py --all --max-cloud 5
```

### Skip Already Downloaded Locations

```bash
# Resume interrupted batch download
python batch_download_locations.py --all --skip-existing
```

### Custom Output Directory

```bash
python batch_download_locations.py --all --output-dir my_custom_folder
```

---

## Quality Assessment

After each download, the script automatically checks:

### Brightness Analysis
```
Mean pixel value: 120.5
✓ Good brightness range (30-225)
```
- **< 30:** Very dark (ocean, shadows, missing data)
- **30-225:** Good range ✓
- **> 225:** Very bright (clouds, snow, ice)

### Contrast Analysis
```
Std deviation: 45.2
✓ Good contrast
```
- **< 10:** Low contrast (uniform ocean, desert)
- **> 10:** Good variation ✓

### Missing Data
```
Black pixels: 2.3%
✓ Minimal missing data
```
- **< 20%:** Acceptable
- **> 20%:** High missing data (may indicate poor coverage)

---

## Troubleshooting

### Problem: "No images found matching criteria"

**Causes:**
1. Cloud threshold too strict for the region
2. Date range doesn't have clear imagery
3. Wrong coordinates

**Solutions:**

```bash
# 1. Increase cloud threshold
python batch_download_locations.py --locations florida_coast --max-cloud 25

# 2. Edit locations JSON to expand date range
# Change "end_date" from "2023-09-30" to "2023-12-31"

# 3. Verify coordinates at https://geojson.io
```

### Problem: "Very dark image" warning

**Likely cause:** Ocean or water-dominated area

**Solutions:**
- Expected for coastal areas with lots of water
- Verify the location has land features
- Check coordinates aren't in open ocean

### Problem: Download very slow

**Causes:**
- Large region of interest
- Google Earth Engine server load
- Network speed

**Solutions:**
```bash
# Download one location at a time
python download_california_coast.py

# Use smaller bbox (edit JSON):
# Change from 0.1° × 0.1° to 0.05° × 0.05°
"bbox": [-122.45, 37.75, -122.40, 37.80]  # Half the size
```

### Problem: Authentication failed

```bash
# Re-authenticate
earthengine authenticate

# Verify authentication
python -c "import ee; ee.Initialize(); print('✓ Success')"
```

---

## Understanding Output Files

### File Naming
```
downloads/
├── newyork_manhattan.tif
├── iowa_farmland.tif
├── california_coast.tif
└── download_log.json
```

### File Sizes
- **Typical:** 50-150 MB per location
- **Factors affecting size:**
  - Bbox size (0.1° × 0.1° is standard)
  - Presence of water (compresses well)
  - Terrain complexity

### Download Log
```json
{
  "timestamp": "2023-10-15T14:30:00",
  "total": 5,
  "successful": 5,
  "failed": 0,
  "locations": [
    {
      "name": "california_coast",
      "status": "success",
      "quality": "good"
    }
  ]
}
```

---

## Next Steps After Download

1. **Verify Images**
   ```bash
   # View with QGIS or other GIS software
   # Or use Python:
   python -c "from PIL import Image; Image.open('downloads/california_coast.tif').show()"
   ```

2. **Preprocess for Training**
   ```bash
   # Tile into 256×256 patches
   python prepare_sentinel2_data.py
   ```

3. **Generate Annotations**
   ```bash
   # Create VQA questions
   python annotation_helper.py
   ```

---

## Tips for Success

1. **Start small:** Download 3-5 locations first to test your workflow
2. **Verify quality:** Check each downloaded image before moving to preprocessing
3. **Note seasonal patterns:** Tropical areas need higher cloud thresholds
4. **Save your config:** Keep a record of which locations worked well
5. **Monitor progress:** The batch script provides detailed logging

---

## Additional Resources

- [Sentinel-2 Mission](https://sentinel.esa.int/web/sentinel/missions/sentinel-2)
- [Google Earth Engine Docs](https://developers.google.com/earth-engine)
- [RSVQA Paper](https://arxiv.org/abs/1703.00851)
- Check `PHASE1_DOWNLOAD_GUIDE.md` for original guide
- Check `locations_extended.json` for all 24 available locations

---

## Support

If you encounter issues:
1. Check `download_log.json` for detailed error messages
2. Verify Earth Engine authentication: `earthengine authenticate`
3. Test with a single known-good location first
4. Check that your coordinates are valid at [geojson.io](https://geojson.io)

---

**Happy downloading! Cloud-free imagery awaits!** ☁️→☀️
