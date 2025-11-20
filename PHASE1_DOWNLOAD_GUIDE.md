# Phase 1: Downloading Cloud-Free Sentinel-2 Images

This guide walks you through downloading cloud-free Sentinel-2 imagery from Google Earth Engine for your custom RSVQA dataset.

---

## 📋 Overview

**Goal**: Download cloud-free Sentinel-2 RGB images for 5-10 diverse geographic locations

**Tools Provided**:
- `download_sentinel2_gee.py` - Python script (recommended)
- `download_sentinel2_gee.js` - JavaScript for GEE Code Editor
- `locations_example.json` - Example configuration
- `setup_gee.sh` - Setup script

---

## 🚀 Quick Start

### Step 1: Setup Google Earth Engine

```bash
# Run setup script
chmod +x setup_gee.sh
./setup_gee.sh
```

This will:
1. Install Earth Engine API and geemap
2. Authenticate with your Google account
3. Test the connection
4. Create necessary directories

**First time using GEE?**
- Sign up at: https://earthengine.google.com/signup/
- It's free for research and education

### Step 2: Choose Your Locations

**Option A: Edit the example config**
```bash
# Copy example
cp locations_example.json my_locations.json

# Edit with your locations
nano my_locations.json  # or use your favorite editor
```

**Option B: Use interactive mode**
```bash
python download_sentinel2_gee.py --interactive
```

**Option C: Use predefined locations**
```bash
python download_sentinel2_gee.py --predefined
```

### Step 3: Download Images

**Recommended: Export to Google Drive (best for large areas)**
```bash
python download_sentinel2_gee.py \
    --config my_locations.json \
    --export_method drive
```

Then:
1. Go to: https://code.earthengine.google.com/tasks
2. Click "RUN" for each export task
3. Wait 5-30 minutes for completion
4. Download from Google Drive folder: `RSVQA_Sentinel2`

**Alternative: Direct download (good for small areas)**
```bash
python download_sentinel2_gee.py \
    --config my_locations.json \
    --export_method local \
    --output_dir ./downloads
```

---

## 📍 Selecting Good Locations

### Recommended Diversity

Select 5-10 locations covering:

| Category | Example Locations | Purpose |
|----------|------------------|---------|
| **Urban** | NYC, LA, Chicago | Buildings, roads, infrastructure |
| **Agricultural** | Iowa, Central Valley | Farmland, crops, irrigation |
| **Forest** | Amazon, Pacific Northwest | Dense vegetation |
| **Desert** | Arizona, Nevada | Arid land, minimal vegetation |
| **Coastal** | San Francisco, Florida | Water, beaches, ports |
| **Mixed** | Phoenix, Seattle | Urban + natural |

### Geographic Diversity Tips

1. **Latitude variety**: Mix of north/south locations
2. **Climate variety**: Temperate, tropical, arid, coastal
3. **Land use variety**: Urban, rural, natural, agricultural
4. **Feature variety**: Buildings, water, vegetation, roads

### Bounding Box Guidelines

**Size recommendations**:
- 0.1° × 0.1° = ~11km × 11km (recommended starting size)
- Larger areas = more tiles but longer download
- Smaller areas = fewer tiles but limited diversity

**How to find coordinates**:

1. **Google Maps**: Right-click → "What's here?" → Copy coordinates
2. **Google Earth**: File → New → Polygon → Draw box → Copy coordinates
3. **GeoJSON.io**: Draw rectangle → Copy coordinates

**Example**: For a 0.1° × 0.1° box around NYC:
```json
{
  "name": "newyork",
  "bbox": [-74.05, 40.7, -73.95, 40.8]
}
```
Format: `[lon_min, lat_min, lon_max, lat_max]`

---

## 🌤️ Cloud Filtering Strategy

### Cloud Percentage Thresholds

| Location Type | Recommended Threshold | Reasoning |
|--------------|----------------------|-----------|
| **Desert/Arid** | 5% | Very low cloud cover year-round |
| **Urban/Temperate** | 10% | Moderate cloud cover |
| **Tropical/Rainforest** | 15-20% | High cloud cover, need flexibility |
| **Coastal** | 10-15% | Variable cloud cover |
| **Mountainous** | 10-15% | Topographic clouds |

### Date Range Selection

**Northern Hemisphere**:
- **Best months**: June - September (summer)
- **Avoid**: December - February (short days, snow)

**Southern Hemisphere**:
- **Best months**: December - March (summer)
- **Avoid**: June - August (short days)

**Tropical regions**:
- **Dry season**: Best (varies by location)
- **Wet season**: Higher cloud cover

**Example date ranges**:
```json
"start_date": "2023-06-01",
"end_date": "2023-09-30"
```

---

## 🔧 Advanced Configuration

### locations.json Format

```json
{
  "locations": [
    {
      "name": "unique_location_name",
      "description": "Human-readable description",
      "bbox": [lon_min, lat_min, lon_max, lat_max],
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD",
      "cloud_percentage": 10,
      "notes": "Optional notes"
    }
  ],
  "configuration": {
    "export_scale": 10,
    "export_crs": "EPSG:3857"
  }
}
```

### Using the JavaScript Version

If you prefer the GEE Code Editor:

1. Open: https://code.earthengine.google.com/
2. Copy contents of `download_sentinel2_gee.js`
3. Modify the `LOCATIONS` array:
```javascript
var LOCATIONS = [
  {
    name: 'my_location',
    bbox: [-74.05, 40.7, -73.95, 40.8],
    description: 'Description',
    maxCloud: 10  // Optional, overrides default
  }
];
```
4. Click "Run"
5. Check "Tasks" tab
6. Click "RUN" for each export

---

## ✅ Quality Checks

The script automatically checks:

### 1. Image Availability
```
✓ Found 45 images matching criteria
```
If 0 images found:
- Expand date range
- Increase cloud percentage
- Check bounding box coordinates

### 2. Brightness
```
✓ Good brightness range
Mean pixel value: 120.5
```
Warnings:
- Mean < 30: Very dark (possibly water/shadows)
- Mean > 225: Very bright (possibly clouds/snow)

### 3. Contrast
```
✓ Good contrast
Std deviation: 45.2
```
Warnings:
- Std < 10: Low contrast (uniform area, possibly ocean)

### 4. Visual Preview
For JavaScript version, you can view images on the map before downloading.

---

## 📊 Expected Results

### Download Summary

After running the script:

```
================================================================================
DOWNLOAD SUMMARY
================================================================================

Successful: 5/5
  ✓ newyork_manhattan
    Task ID: ABCD1234...
    Quality: mean=120.3, std=45.1

  ✓ iowa_farmland
    Task ID: EFGH5678...
    Quality: mean=95.7, std=38.2

  ...

Next Steps:
1. Check export status at: https://code.earthengine.google.com/tasks
2. Wait for tasks to complete (usually 5-30 minutes)
3. Download from Google Drive folder: RSVQA_Sentinel2
4. Run preprocessing: python prepare_sentinel2_data.py
```

### Expected File Sizes

For a 0.1° × 0.1° area (~11km × 11km):
- File size: ~50-150 MB per location (GeoTIFF)
- After tiling to 256×256: ~200-500 patches per location

Total for 5 locations: ~250-750 MB raw, ~1000-2500 tiles

---

## 🚨 Troubleshooting

### Problem: "earthengine authenticate" fails

**Solution**:
```bash
# Try manual authentication
python3 -c "import ee; ee.Authenticate()"
```
Follow the browser prompts.

### Problem: No images found for location

**Solutions**:
1. Check coordinates (lat/lon order, sign)
2. Expand date range to full year
3. Increase cloud percentage to 20-30%
4. Try different months

**Test query**:
```python
import ee
ee.Initialize()

roi = ee.Geometry.Rectangle([-74.05, 40.7, -73.95, 40.8])
collection = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(roi) \
    .filterDate('2023-01-01', '2023-12-31')

print("Total images:", collection.size().getInfo())
```

### Problem: Images too dark/bright

**Solutions**:
1. Check time of year (avoid winter at high latitudes)
2. Try different months
3. Visualize in GEE Code Editor first
4. Adjust visualization parameters in script

### Problem: Download very slow or fails

**Solutions**:
1. Use `export_method='drive'` instead of `local`
2. Reduce area size (smaller bounding box)
3. Check internet connection
4. Try during off-peak hours

### Problem: Export task fails in GEE

**Common causes**:
1. Area too large → Reduce bbox size
2. Timeout → Split into smaller areas
3. Memory limit → Use smaller scale (e.g., 20m instead of 10m)

---

## 📈 Performance Optimization

### For Many Locations (>10)

**Option 1: Batch processing**
```bash
# Split locations into groups
python download_sentinel2_gee.py --config locations_1_5.json
# Wait for completion
python download_sentinel2_gee.py --config locations_6_10.json
```

**Option 2: Parallel exports**
All exports run in parallel on GEE servers. You can start hundreds of export tasks simultaneously.

### For Large Areas

**Option 1: Use coarser resolution**
```json
"export_scale": 20  // 20m instead of 10m
```

**Option 2: Split into tiles**
Instead of one large bbox, create multiple smaller adjacent boxes.

---

## 📝 Download Checklist

Before proceeding to Phase 2:

- [ ] GEE account created and authenticated
- [ ] Earth Engine packages installed
- [ ] Selected 5-10 diverse locations
- [ ] Verified coordinates using Google Maps/Earth
- [ ] Chosen appropriate date ranges (summer months)
- [ ] Set cloud thresholds (5-20% depending on location)
- [ ] Started download/export tasks
- [ ] All tasks completed successfully
- [ ] Downloaded files to local machine
- [ ] Verified file sizes and quality
- [ ] Organized files in `downloads/` directory

---

## 🎯 Success Criteria

You're ready for Phase 2 when you have:

- ✅ 5-10 GeoTIFF files (one per location)
- ✅ Each file is 50-200 MB
- ✅ Geographic diversity (urban, rural, coastal, etc.)
- ✅ Good quality metrics (mean 30-225, std >10)
- ✅ Cloud-free (visual inspection)
- ✅ Files in correct format (3-band RGB, EPSG:3857)

---

## 📚 Next Steps

Once downloads are complete:

```bash
# Move to Phase 2: Preprocessing
python prepare_sentinel2_data.py \
    --input_dir ./downloads \
    --output_dir ./dataset \
    --patch_size 256

# See: CUSTOM_DATASET_WORKFLOW.md - Phase 2
```

---

## 📞 Additional Resources

**Google Earth Engine**:
- Sign up: https://earthengine.google.com/signup/
- Documentation: https://developers.google.com/earth-engine
- Code Editor: https://code.earthengine.google.com/

**Sentinel-2**:
- Dataset catalog: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
- User guide: https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi

**Finding Locations**:
- Google Maps: https://www.google.com/maps
- Google Earth: https://earth.google.com/
- GeoJSON.io: https://geojson.io/ (draw and get coordinates)

**Earth Engine Community**:
- Forum: https://groups.google.com/g/google-earth-engine-developers
- Stack Overflow: Tag `google-earth-engine`

---

## 🎉 You're Ready!

Start downloading your cloud-free Sentinel-2 images and build your custom RSVQA dataset!

```bash
# Quick start command
python download_sentinel2_gee.py --predefined --export_method drive
```

**Good luck! 🛰️**
