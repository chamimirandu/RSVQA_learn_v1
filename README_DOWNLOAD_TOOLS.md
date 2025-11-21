# Download Tools for Cloud-Free Sentinel-2 Imagery

Comprehensive toolkit for downloading cloud-free Sentinel-2 satellite imagery for RSVQA dataset creation.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install earthengine-api geemap

# 2. Authenticate
earthengine authenticate

# 3. Download remaining 5 locations (if you already have 3)
python batch_download_locations.py --all

# OR download a single location to test
python download_california_coast.py
```

## 📁 Available Scripts

### Batch Download Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `batch_download_locations.py` | Download multiple locations with advanced cloud filtering | `python batch_download_locations.py --all` |
| `check_downloads.py` | Check which locations are downloaded and get recommendations | `python check_downloads.py` |

### Individual Location Scripts (Quick-Start)

| Script | Location | Features |
|--------|----------|----------|
| `download_california_coast.py` | San Francisco Bay Area | Urban coastal, low clouds (5%) |
| `download_arizona_desert.py` | Arizona Desert | Arid terrain, minimal clouds (5%) |
| `download_florida_coast.py` | Florida Coast | Tropical coastal, winter dates (15%) |
| `download_chicago_urban.py` | Chicago Metro | Urban + lake, moderate clouds (10%) |
| `download_yellowstone.py` | Yellowstone NP | Natural park, summer only (10%) |

## ☁️ Cloud Filtering Features

All scripts use **3-layer cloud filtering**:

1. **Metadata Filtering** - Pre-filter by `CLOUDY_PIXEL_PERCENTAGE`
2. **SCL Masking** - Per-pixel cloud detection and masking
3. **Median Compositing** - Statistical removal of remaining clouds

**Result:** Completely cloud-free imagery!

## 📍 Available Locations

### Basic Set (8 locations) - `locations_example.json`
- New York Manhattan (urban)
- Iowa Farmland (agricultural)
- Amazon Rainforest (tropical forest)
- California Coast (coastal urban)
- Arizona Desert (arid)
- Florida Coast (tropical coastal)
- Chicago Urban (metropolitan)
- Yellowstone (natural park)

### Extended Set (24 locations) - `locations_extended.json`
Includes all basic locations PLUS:
- Sahara Desert (Algeria)
- Scottish Highlands (UK)
- Tokyo Metropolitan (Japan)
- Great Barrier Reef (Australia)
- Greenland Ice Sheet
- Nile Delta (Egypt)
- Venice Lagoon (Italy)
- Palm Oil Plantation (Malaysia)
- Dubai Urban (UAE)
- Rocky Mountains (Colorado)
- Patagonia Glaciers (Argentina)
- Bangladesh Delta
- Atacama Desert (Chile)
- Wind Farms (Netherlands)
- Congo Rainforest (DRC)
- Grand Canyon (Arizona)

## 💡 Usage Examples

### Download all remaining locations
```bash
python batch_download_locations.py --all
```

### Download specific locations
```bash
python batch_download_locations.py --locations california_coast arizona_desert chicago_urban
```

### Use extended location set
```bash
python batch_download_locations.py \
  --config locations_extended.json \
  --locations tokyo_metropolitan sahara_desert great_barrier_reef
```

### Override cloud threshold
```bash
# More permissive (20% clouds)
python batch_download_locations.py --all --max-cloud 20

# Stricter (5% clouds)
python batch_download_locations.py --all --max-cloud 5
```

### Skip already downloaded locations
```bash
python batch_download_locations.py --all --skip-existing
```

### Check download status
```bash
python check_downloads.py
```

## 📊 Expected Outputs

```
downloads/
├── california_coast.tif      (80-120 MB)
├── arizona_desert.tif         (60-90 MB)
├── florida_coast.tif          (90-130 MB)
├── chicago_urban.tif          (70-110 MB)
├── yellowstone.tif            (85-115 MB)
└── download_log.json          (download summary)
```

## 🔍 Quality Assessment

Each download is automatically assessed for:
- **Brightness:** Mean pixel value (30-225 is good)
- **Contrast:** Standard deviation (>10 is good)
- **Missing data:** Black pixels (<20% is acceptable)

## 🌍 Location Selection Strategy

### For Training VQA Models

- **Minimum:** 8 locations
- **Recommended:** 12-15 locations
- **Optimal:** 15-20 locations

### Ensure Diversity In

1. **Land cover:** urban, agriculture, forest, desert, water
2. **Geography:** multiple continents, latitudes
3. **Climate:** tropical, temperate, arid, polar
4. **Features:** natural, built, water bodies, terrain

## 🛠️ Troubleshooting

### "No images found"
→ Increase cloud threshold: `--max-cloud 20`
→ Or use extended config with optimized date ranges

### "Very dark image" warning
→ Expected for water-dominated areas (coastal regions)
→ Verify coordinates aren't in open ocean

### Download very slow
→ Download one location at a time
→ Check network connection
→ GEE server may be under high load

### Authentication failed
```bash
earthengine authenticate
```

## 📖 Documentation

- **DOWNLOAD_GUIDE.md** - Comprehensive guide with cloud filtering details
- **PHASE1_DOWNLOAD_GUIDE.md** - Original download guide
- **README_GEE_OSM_COLAB.md** - Google Colab version
- **locations_example.json** - 8 basic locations config
- **locations_extended.json** - 24 diverse locations config

## 🔄 Next Steps After Download

1. **Verify downloads:**
   ```bash
   python check_downloads.py
   ```

2. **Preprocess images:**
   ```bash
   python prepare_sentinel2_data.py
   ```

3. **Generate VQA annotations:**
   ```bash
   python annotation_helper.py
   ```

4. **Train model:**
   ```bash
   cd VQA_model
   python train.py
   ```

## 🎯 Key Features

✓ **Automated cloud filtering** - 3-layer approach ensures cloud-free images
✓ **Quality assessment** - Automatic checks for brightness, contrast, missing data
✓ **Retry logic** - Automatically relaxes parameters if download fails
✓ **Progress tracking** - Detailed logs and status reports
✓ **Flexible configuration** - JSON-based location definitions
✓ **24 pre-defined locations** - Covering diverse biomes and terrains
✓ **Batch processing** - Download multiple locations in one command
✓ **Resume capability** - Skip already downloaded locations

## 📝 Cloud Threshold Recommendations

| Climate Type | Threshold | Example Locations |
|--------------|-----------|-------------------|
| Desert | 3-5% | Arizona, Sahara, Atacama |
| Temperate | 10% | NYC, Chicago, Tokyo |
| Mediterranean | 5-10% | California, Dubai |
| Tropical | 15-20% | Amazon, Congo, Florida |
| Coastal | 10-15% | Varies by season |
| Mountain | 10-15% | Highlands, Rockies |

---

**Ready to download cloud-free imagery!** ☁️→☀️

For detailed information, see **DOWNLOAD_GUIDE.md**
