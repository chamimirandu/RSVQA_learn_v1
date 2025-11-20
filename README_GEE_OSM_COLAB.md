# Cloud-Free Sentinel-2 + OSM Downloader for Google Colab

Complete solution for downloading **cloud-free satellite imagery** with corresponding **OpenStreetMap data** for creating custom RSVQA datasets.

## 🎯 Features

✅ **Cloud-free Sentinel-2 RGB composites** from Google Earth Engine
✅ **Land area detection** - automatically filters out bare ocean areas
✅ **OSM data integration** - fetch OpenStreetMap features via Overpass API
✅ **Google Colab ready** - no local setup required
✅ **Batch processing** - download multiple locations efficiently
✅ **Complete metadata** - georeferencing, quality metrics, timestamps

## 🚀 Quick Start

### Option 1: Google Colab (Recommended)

1. Open the notebook: [`GEE_OSM_Downloader_Colab.ipynb`](./GEE_OSM_Downloader_Colab.ipynb)
2. Upload to Google Colab
3. Run all cells
4. Download your data!

### Option 2: Command Line

```bash
# Setup
pip install earthengine-api geemap

# Authenticate with GEE
earthengine authenticate

# Run the downloader
python colab_gee_osm_downloader.py --mode predefined
```

## 📋 Requirements

- **Google Earth Engine account** (free): https://earthengine.google.com/
- **Python 3.7+**
- **Packages**: `earthengine-api`, `geemap`, `requests`, `numpy`

## 🌍 Usage Examples

### Example 1: Download Manhattan with OSM Data

```python
from colab_gee_osm_downloader import CoLabGEEOSMDownloader

# Initialize
downloader = CoLabGEEOSMDownloader(output_dir="./downloads")

# Download Manhattan
result = downloader.process_location(
    name='manhattan_nyc',
    bbox=[-74.02, 40.75, -73.97, 40.80],  # [min_lon, min_lat, max_lon, max_lat]
    cloud_percentage=10,
    scale=10  # 10m resolution
)

print(f"Status: {result['status']}")
print(f"Image: {result['image_path']}")
print(f"OSM data: {result['osm_path']}")
```

### Example 2: Batch Download Multiple Locations

```python
locations = [
    {'name': 'paris', 'bbox': [2.30, 48.85, 2.37, 48.88], 'cloud_percentage': 10},
    {'name': 'tokyo', 'bbox': [139.70, 35.65, 139.80, 35.70], 'cloud_percentage': 15},
    {'name': 'sydney', 'bbox': [151.15, -33.92, 151.25, -33.85], 'cloud_percentage': 10}
]

for loc in locations:
    result = downloader.process_location(**loc)
```

### Example 3: Custom OSM Features

```python
# Download only buildings and roads
result = downloader.process_location(
    name='custom_location',
    bbox=[-122.5, 37.7, -122.4, 37.8],
    osm_features=['building', 'highway']  # Only these features
)
```

## 📂 Output Structure

```
downloads/
├── images/
│   ├── manhattan_nyc.tif          # Cloud-free Sentinel-2 GeoTIFF
│   ├── paris.tif
│   └── tokyo.tif
├── osm_data/
│   ├── manhattan_nyc_osm.geojson  # OSM features as GeoJSON
│   ├── paris_osm.geojson
│   └── tokyo_osm.geojson
└── metadata/
    ├── manhattan_nyc_metadata.json # Includes quality metrics, dates, etc.
    ├── paris_metadata.json
    └── tokyo_metadata.json
```

## 🗺️ Predefined Locations

The script includes 8 predefined land-based locations worldwide:

| Location | Type | Cloud Threshold |
|----------|------|-----------------|
| Manhattan, NYC | Dense urban | 10% |
| Iowa Farmland | Agricultural | 10% |
| Amazon Rainforest | Tropical forest | 20% |
| San Francisco | Urban coastal | 10% |
| Sahara Desert | Desert | 5% |
| Tokyo | Dense urban | 15% |
| Scottish Highlands | Mountainous | 20% |
| Venice, Italy | Urban with canals | 10% |

## 🎛️ Parameters

### `process_location()` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Location name (used for filenames) |
| `bbox` | List[float] | Required | Bounding box [min_lon, min_lat, max_lon, max_lat] |
| `start_date` | str | 1 year ago | Start date (YYYY-MM-DD) |
| `end_date` | str | Today | End date (YYYY-MM-DD) |
| `cloud_percentage` | int | 10 | Maximum cloud cover (0-100%) |
| `scale` | int | 10 | Resolution in meters |
| `osm_features` | List[str] | All common | OSM features to fetch |

### Default OSM Features

When `osm_features=None`, the following features are fetched:
- `building` - All buildings
- `highway` - Roads and paths
- `landuse` - Land use classifications
- `natural` - Natural features (water, vegetation, etc.)
- `waterway` - Rivers, streams, canals
- `amenity` - Facilities (schools, hospitals, etc.)
- `leisure` - Parks, sports facilities
- `railway` - Train tracks and stations
- `aeroway` - Airports and runways

## 🔍 How It Works

### 1. Cloud-Free Image Compositing

```python
# Query Sentinel-2 Surface Reflectance
collection = (ee.ImageCollection('COPERNICUS/S2_SR')
             .filterBounds(roi)
             .filterDate(start_date, end_date)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_percentage)))

# Create median composite to reduce cloud artifacts
composite = collection.median()
```

### 2. Land/Ocean Detection

The script analyzes each image to detect land vs. ocean:

```python
land_check = downloader.check_land_coverage(image, roi)
# Returns: {'mean_brightness': float, 'std_dev': float, 'is_likely_land': bool}
```

**Detection Logic:**
- **Ocean areas**: Low brightness + Low variance (uniform dark water)
- **Land areas**: Higher brightness OR higher variance (diverse features)

### 3. OSM Data Fetching

Uses the Overpass API to query OpenStreetMap:

```python
osm_data = downloader.fetch_osm_data(bbox, features=['building', 'highway'])
# Returns: GeoJSON FeatureCollection
```

## 🎨 Visualization

### View Downloaded Image

```python
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt

with rasterio.open('downloads/images/manhattan_nyc.tif') as src:
    rgb = src.read([1, 2, 3])
    show(rgb, transform=src.transform)
```

### Analyze OSM Data

```python
import json
from collections import Counter

with open('downloads/osm_data/manhattan_nyc_osm.geojson') as f:
    osm = json.load(f)

print(f"Total features: {len(osm['features'])}")

# Count by type
types = [f['properties'].get('building', f['properties'].get('highway', 'other'))
         for f in osm['features']]
print(Counter(types).most_common(10))
```

## 🔧 Advanced Usage

### Custom Date Range

```python
result = downloader.process_location(
    name='seasonal_change',
    bbox=[-93.65, 41.55, -93.55, 41.65],
    start_date='2023-06-01',  # Summer
    end_date='2023-08-31',
    cloud_percentage=10
)
```

### Higher Cloud Tolerance (Tropical Regions)

```python
result = downloader.process_location(
    name='rainforest',
    bbox=[-60.1, -3.1, -60.0, -3.0],
    cloud_percentage=25,  # Higher tolerance for cloudy regions
    min_images=2  # Lower minimum requirement
)
```

### Command-Line Batch Processing

```json
// locations.json
{
  "locations": [
    {"name": "loc1", "bbox": [-74, 40, -73, 41], "cloud_percentage": 10},
    {"name": "loc2", "bbox": [2, 48, 3, 49], "cloud_percentage": 15}
  ]
}
```

```bash
python colab_gee_osm_downloader.py --mode config --config locations.json
```

## 🐛 Troubleshooting

### Issue: "Earth Engine initialization failed"

**Solution:**
```python
import ee
ee.Authenticate()  # Opens browser for authorization
ee.Initialize()
```

### Issue: "No suitable images found"

**Causes & Solutions:**
1. **High cloud cover** → Increase `cloud_percentage` (try 15-20%)
2. **Limited time range** → Expand date range to 2 years
3. **No Sentinel-2 coverage** → Check coverage at https://scihub.copernicus.eu/

### Issue: "OSM Overpass API timeout"

**Solutions:**
1. Reduce bounding box size (try 0.1° × 0.1°)
2. Specify fewer OSM features
3. Wait 2-3 minutes (rate limiting)
4. Use alternative Overpass servers

### Issue: "Warning: Area appears to be mostly ocean"

**Explanation:**
- This is informational, not an error
- Image will still be downloaded
- Check metadata for land coverage metrics

## 📊 Quality Metrics

Each download includes quality metrics in the metadata:

```json
{
  "land_coverage": {
    "mean_brightness": 1234.5,
    "std_dev": 567.8,
    "is_likely_land": true,
    "stats": {
      "B4_mean": 1200,
      "B4_stdDev": 550,
      "B4_p10": 800,
      "B4_p90": 1800
    }
  },
  "osm_feature_count": 1523
}
```

## 🎓 Integration with RSVQA Workflow

This downloader is **Phase 1** of the complete RSVQA dataset creation workflow:

```
Phase 1: Download (this tool)
    ↓
Phase 2: Tile into 256×256 patches (prepare_sentinel2_data.py)
    ↓
Phase 3: Generate questions from OSM (annotation_helper.py)
    ↓
Phase 4: Create train/val/test splits (create_dataset_splits.py)
    ↓
Phase 5: Train VQA models (VQA_model/train.py)
```

See [`CUSTOM_DATASET_WORKFLOW.md`](./CUSTOM_DATASET_WORKFLOW.md) for the complete pipeline.

## 📝 Citation

If you use this tool in your research, please cite:

```bibtex
@article{lobry2020rsvqa,
  title={RSVQA: Visual Question Answering for Remote Sensing Data},
  author={Lobry, Sylvain and Marcos, Diego and Murray, Jesse and Tuia, Devis},
  journal={IEEE Transactions on Geoscience and Remote Sensing},
  year={2020}
}
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] Add support for other satellite sources (Landsat, Planet)
- [ ] Implement automatic cloud shadow masking
- [ ] Add water body detection (lakes, rivers)
- [ ] Support for temporal composites (seasonal changes)
- [ ] Integration with other OSM APIs (Nominatim, Photon)

## 📜 License

This project extends the original RSVQA codebase. See the main repository README for license information.

## 🔗 Resources

- **Google Earth Engine**: https://earthengine.google.com/
- **Sentinel-2 Documentation**: https://sentinel.esa.int/web/sentinel/missions/sentinel-2
- **OpenStreetMap**: https://www.openstreetmap.org/
- **Overpass API**: https://overpass-api.de/
- **Original RSVQA Paper**: https://ieeexplore.ieee.org/document/9088993

## 💡 Tips for Best Results

1. **Cloud Coverage**: Start with 10%, increase if no results
2. **Bounding Box**: Keep under 0.2° × 0.2° for reasonable file sizes
3. **Date Range**: Use 1-2 years for best cloud-free composite
4. **Resolution**: 10m is standard; use 20m for larger areas
5. **OSM Features**: Be selective to reduce download time
6. **Rate Limiting**: Wait 2-3 seconds between requests
7. **Coastal Areas**: Expect "ocean warning" (normal behavior)
8. **Tropical Regions**: Use 15-25% cloud threshold

## ❓ FAQ

**Q: Can I download Sentinel-1 SAR data?**
A: Currently only Sentinel-2 optical. SAR support coming soon.

**Q: How large can my bounding box be?**
A: Recommend < 0.2° × 0.2° (~400km² at equator). Larger areas may timeout.

**Q: Can I use this for commercial purposes?**
A: Sentinel-2 data is free and open. OSM requires attribution. Check specific licenses.

**Q: Why is my rainforest image still cloudy?**
A: Rainforests have persistent clouds. Use higher threshold (20-25%) and longer date ranges (2 years).

**Q: Can I download historical imagery?**
A: Yes! Sentinel-2 data available from 2015-present. Specify custom date ranges.

**Q: How do I get coordinates for my area?**
A: Use https://boundingbox.klokantech.com/ or Google Earth.

---

**Need help?** Open an issue on GitHub or check the documentation:
- `PHASE1_DOWNLOAD_GUIDE.md` - Detailed download guide
- `CUSTOM_DATASET_WORKFLOW.md` - Complete workflow
- `QUICK_START.md` - Quick reference

**Happy downloading! 🛰️🗺️**
