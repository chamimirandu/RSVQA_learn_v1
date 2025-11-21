# Custom Location Download - Quick Start Guide

This guide will help you download Sentinel-2 imagery for all 21 custom locations.

## What's Included

The download will fetch imagery for these diverse locations:
- **Coastal**: California coast, Florida coast, Venice lagoon, Great Barrier Reef
- **Urban**: Chicago, Tokyo, Dubai, San Francisco
- **Desert**: Arizona, Sahara, Atacama
- **Mountains**: Yellowstone, Scottish Highlands, Rocky Mountains
- **Special**: Grand Canyon, Patagonian glaciers, Greenland ice sheet, and more

## Step-by-Step Instructions

### 1. Setup Environment

First, install required packages and authenticate with Google Earth Engine:

```bash
bash setup_download_environment.sh
```

This will:
- Install `earthengine-api`, `geemap`, and other dependencies
- Check if you're authenticated with Google Earth Engine

### 2. Authenticate (if needed)

If the setup script says you need to authenticate, run:

```bash
earthengine authenticate
```

This will:
1. Open a browser window
2. Ask you to sign in with your Google account
3. Provide an authentication code to paste back

**Note:** You'll need a Google Earth Engine account. Sign up at: https://earthengine.google.com/signup/

### 3. Download All Locations

Once authenticated, run:

```bash
python3 download_custom_locations.py
```

The script will:
- Download all 21 custom locations (excluding 3 example locations)
- Save images to `custom_imagery/` directory
- Create a download log with results
- Show progress and quality assessment for each location

### 4. Monitor Progress

The downloader will show:
- Current location being processed
- Number of images found
- Download progress
- Quality assessment (brightness, missing data, etc.)

Example output:
```
[5/21] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 california_coast
   San Francisco Bay Area - California
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📡 Searching for imagery...
     Found 43 images
     ✓ Composite created
  💾 Downloading...
  ✓ Saved to: custom_imagery/california_coast.tif
  📊 Quality: mean=89.2, black=2.3%
     ✓ Quality looks good
```

## Troubleshooting

### "Missing required package"
Run the setup script:
```bash
bash setup_download_environment.sh
```

### "Failed to initialize Google Earth Engine"
Authenticate with:
```bash
earthengine authenticate
```

### "No images found"
The script will automatically:
- Retry with higher cloud threshold (20%)
- Expand the date range
- Skip if still no images available

### Resume Failed Downloads
The script automatically skips already-downloaded locations. Just re-run it:
```bash
python3 download_custom_locations.py
```

## Output

After completion, you'll have:
- **Images**: `custom_imagery/*.tif` - One GeoTIFF file per location
- **Log**: `custom_imagery/download_log.json` - Detailed download results

## What's Different from Old Script?

This new script:
- ✅ Automatically checks and installs dependencies
- ✅ Clearer error messages
- ✅ Simpler to use (no command-line arguments needed)
- ✅ Automatic resume capability
- ✅ Better progress tracking
- ✅ Quality assessment built-in

## Need Help?

If you encounter errors:
1. Check that you're in the repository root directory
2. Ensure you have a Google Earth Engine account
3. Verify authentication: `earthengine authenticate`
4. Check the log file: `custom_imagery/download_log.json`

## Time Estimate

- Setup: ~2 minutes
- Authentication (first time): ~2 minutes
- Downloads: ~30-60 minutes (depending on network speed)
  - Each location takes 1-3 minutes
  - 21 locations total

## Next Steps

After downloading:
1. Check image quality in `custom_imagery/` directory
2. Review `download_log.json` for any failures
3. Re-run script to retry any failed downloads
4. Use images for your VQA model training!

---

**Pro Tip:** The script pauses 2 seconds between downloads to respect Google Earth Engine rate limits. This is normal!
