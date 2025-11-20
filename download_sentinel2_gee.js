/*
 * Download Cloud-Free Sentinel-2 Imagery - Google Earth Engine Code Editor
 *
 * This script downloads cloud-free Sentinel-2 RGB composites for multiple locations.
 *
 * HOW TO USE:
 * 1. Open Google Earth Engine Code Editor: https://code.earthengine.google.com/
 * 2. Copy-paste this entire script
 * 3. Modify the LOCATIONS configuration below
 * 4. Click "Run"
 * 5. Check the "Tasks" tab to start exports
 *
 * FEATURES:
 * - Automatic cloud filtering
 * - Median composite (removes clouds)
 * - Quality assessment
 * - Multiple locations support
 * - Visual preview on map
 */

// ============================================================================
// CONFIGURATION - MODIFY THIS SECTION
// ============================================================================

var CONFIG = {
  // Date range for imagery
  START_DATE: '2023-06-01',
  END_DATE: '2023-09-30',

  // Cloud filtering
  MAX_CLOUD_PERCENTAGE: 10,  // Maximum cloud percentage (0-100)

  // Export settings
  EXPORT_SCALE: 10,  // Resolution in meters (10m for Sentinel-2)
  EXPORT_CRS: 'EPSG:3857',  // Coordinate system (Web Mercator)
  EXPORT_FOLDER: 'RSVQA_Sentinel2',  // Google Drive folder

  // Visualization parameters
  VIS_MIN: 0,
  VIS_MAX: 3000,
  VIS_GAMMA: 1.4
};

// Define your locations here
// Format: [lon_min, lat_min, lon_max, lat_max]
var LOCATIONS = [
  {
    name: 'newyork_manhattan',
    bbox: [-74.05, 40.7, -73.95, 40.8],
    description: 'New York City - Manhattan'
  },
  {
    name: 'iowa_farmland',
    bbox: [-93.65, 41.55, -93.55, 41.65],
    description: 'Iowa agricultural area'
  },
  {
    name: 'amazon_rainforest',
    bbox: [-60.1, -3.1, -60.0, -3.0],
    description: 'Amazon rainforest',
    maxCloud: 15  // Higher cloud threshold for tropical areas
  },
  {
    name: 'california_coast',
    bbox: [-122.5, 37.7, -122.4, 37.8],
    description: 'San Francisco Bay Area'
  },
  {
    name: 'arizona_desert',
    bbox: [-111.1, 33.4, -111.0, 33.5],
    description: 'Arizona desert',
    maxCloud: 5  // Lower cloud threshold for desert
  }
];

// ============================================================================
// FUNCTIONS
// ============================================================================

/**
 * Get cloud-free Sentinel-2 composite
 */
function getCloudFreeComposite(roi, startDate, endDate, maxCloudPct) {
  // Load Sentinel-2 Surface Reflectance collection
  var collection = ee.ImageCollection('COPERNICUS/S2_SR')
    .filterBounds(roi)
    .filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', maxCloudPct))
    .select(['B4', 'B3', 'B2']);  // RGB bands

  // Count available images
  var count = collection.size();
  print('  Images found:', count);

  // Create median composite (removes clouds)
  var composite = collection.median().clip(roi);

  return composite;
}

/**
 * Assess image quality
 */
function assessQuality(image, roi, locationName) {
  var stats = image.reduceRegion({
    reducer: ee.Reducer.mean().combine({
      reducer2: ee.Reducer.stdDev(),
      sharedInputs: true
    }),
    geometry: roi,
    scale: 30,
    maxPixels: 1e9
  });

  print('  Quality Assessment for ' + locationName + ':');
  print('    Mean (B4):', stats.get('B4_mean'));
  print('    StdDev (B4):', stats.get('B4_stdDev'));

  // Quality checks
  var mean = ee.Number(stats.get('B4_mean')).getInfo();
  var std = ee.Number(stats.get('B4_stdDev')).getInfo();

  if (mean < 100) {
    print('    ⚠ Warning: Dark image (mean < 100)');
  } else if (mean > 2500) {
    print('    ⚠ Warning: Bright image (mean > 2500)');
  } else {
    print('    ✓ Good brightness');
  }

  if (std < 50) {
    print('    ⚠ Warning: Low contrast (std < 50)');
  } else {
    print('    ✓ Good contrast');
  }
}

/**
 * Visualize image on map
 */
function visualizeOnMap(image, roi, locationName) {
  var visParams = {
    min: CONFIG.VIS_MIN,
    max: CONFIG.VIS_MAX,
    gamma: CONFIG.VIS_GAMMA
  };

  Map.addLayer(image, visParams, locationName);
  Map.addLayer(roi, {color: 'red'}, locationName + ' - ROI', false);
}

/**
 * Export image to Google Drive
 */
function exportToDrive(image, roi, locationName) {
  // Visualize for export (scale to 0-255)
  var exportImage = image.visualize({
    min: CONFIG.VIS_MIN,
    max: CONFIG.VIS_MAX,
    gamma: CONFIG.VIS_GAMMA
  });

  Export.image.toDrive({
    image: exportImage,
    description: locationName + '_sentinel2',
    folder: CONFIG.EXPORT_FOLDER,
    scale: CONFIG.EXPORT_SCALE,
    region: roi,
    crs: CONFIG.EXPORT_CRS,
    fileFormat: 'GeoTIFF',
    maxPixels: 1e9,
    formatOptions: {
      cloudOptimized: true
    }
  });

  print('  ✓ Export task created: ' + locationName);
}

/**
 * Process a single location
 */
function processLocation(location) {
  print('\n' + '='.repeat(70));
  print('Processing: ' + location.name);
  print('Description: ' + location.description);
  print('='.repeat(70));

  // Create region of interest
  var roi = ee.Geometry.Rectangle(location.bbox);
  print('Bounding box:', location.bbox);

  // Get cloud threshold (use custom or default)
  var maxCloudPct = location.maxCloud || CONFIG.MAX_CLOUD_PERCENTAGE;
  print('Max cloud percentage:', maxCloudPct + '%');

  // Get composite
  var composite = getCloudFreeComposite(
    roi,
    CONFIG.START_DATE,
    CONFIG.END_DATE,
    maxCloudPct
  );

  // Assess quality
  assessQuality(composite, roi, location.name);

  // Visualize on map
  visualizeOnMap(composite, roi, location.name);

  // Create export task
  exportToDrive(composite, roi, location.name);
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

print('╔═══════════════════════════════════════════════════════════════════╗');
print('║  Sentinel-2 Cloud-Free Image Downloader                          ║');
print('║  For RSVQA Custom Dataset                                        ║');
print('╚═══════════════════════════════════════════════════════════════════╝');

print('\nConfiguration:');
print('  Date range:', CONFIG.START_DATE, 'to', CONFIG.END_DATE);
print('  Default max cloud:', CONFIG.MAX_CLOUD_PERCENTAGE + '%');
print('  Export scale:', CONFIG.EXPORT_SCALE + 'm');
print('  Export folder:', CONFIG.EXPORT_FOLDER);

print('\nLocations to process:', LOCATIONS.length);

// Clear map
Map.clear();

// Process each location
LOCATIONS.forEach(function(location) {
  processLocation(location);
});

// Center map on first location
var firstROI = ee.Geometry.Rectangle(LOCATIONS[0].bbox);
Map.centerObject(firstROI, 11);

// Print instructions
print('\n' + '='.repeat(70));
print('NEXT STEPS:');
print('='.repeat(70));
print('1. Check the preview on the map (toggle layers on the right)');
print('2. Go to the "Tasks" tab (top-right)');
print('3. Click "RUN" for each export task');
print('4. Wait for tasks to complete (5-30 minutes)');
print('5. Download from Google Drive folder: ' + CONFIG.EXPORT_FOLDER);
print('6. Run: python prepare_sentinel2_data.py --input_dir ./downloads --output_dir ./dataset');
print('='.repeat(70));

// ============================================================================
// OPTIONAL: ADDITIONAL HELPER FUNCTIONS
// ============================================================================

/**
 * Calculate optimal date range for a location (find least cloudy period)
 * Uncomment and run this function separately to find best dates
 */
/*
function findBestDateRange(location, year) {
  var roi = ee.Geometry.Rectangle(location.bbox);

  // Check each month
  for (var month = 1; month <= 12; month++) {
    var startDate = year + '-' + String(month).padStart(2, '0') + '-01';
    var endDate = year + '-' + String(month).padStart(2, '0') + '-28';

    var collection = ee.ImageCollection('COPERNICUS/S2_SR')
      .filterBounds(roi)
      .filterDate(startDate, endDate);

    var count = collection.size();
    var avgCloud = collection.aggregate_mean('CLOUDY_PIXEL_PERCENTAGE');

    print('Month ' + month + ':',
          'Images:', count.getInfo(),
          'Avg Cloud:', avgCloud.getInfo().toFixed(1) + '%');
  }
}

// Example usage:
// findBestDateRange(LOCATIONS[0], '2023');
*/

/**
 * Visualize cloud coverage distribution
 */
/*
function visualizeCloudDistribution(location) {
  var roi = ee.Geometry.Rectangle(location.bbox);

  var collection = ee.ImageCollection('COPERNICUS/S2_SR')
    .filterBounds(roi)
    .filterDate(CONFIG.START_DATE, CONFIG.END_DATE)
    .select('CLOUDY_PIXEL_PERCENTAGE');

  var chart = ui.Chart.feature.histogram({
    features: collection,
    property: 'CLOUDY_PIXEL_PERCENTAGE',
    maxBuckets: 20
  }).setOptions({
    title: 'Cloud Coverage Distribution - ' + location.name,
    hAxis: {title: 'Cloud Percentage'},
    vAxis: {title: 'Number of Images'}
  });

  print(chart);
}

// Example usage:
// visualizeCloudDistribution(LOCATIONS[0]);
*/

// ============================================================================
// TIPS FOR SELECTING GOOD LOCATIONS
// ============================================================================

/*
TIPS:
1. Use Google Earth to preview areas first
2. Choose areas with interesting features (buildings, water, vegetation mix)
3. Start with 0.1° × 0.1° bounding boxes (~11km × 11km)
4. For tropical/coastal areas: increase maxCloud to 15-20%
5. For desert/arid areas: decrease maxCloud to 5%
6. Summer months (Jun-Sep in Northern Hemisphere) have less cloud cover
7. Avoid areas at high latitudes in winter (very dark)

EXAMPLE INTERESTING LOCATIONS:

Urban:
- New York: [-74.05, 40.7, -73.95, 40.8]
- Los Angeles: [-118.3, 34.0, -118.2, 34.1]
- Chicago: [-87.7, 41.8, -87.6, 41.9]

Agricultural:
- Iowa farmland: [-93.65, 41.55, -93.55, 41.65]
- Central Valley CA: [-120.5, 36.8, -120.4, 36.9]

Natural:
- Grand Canyon: [-112.2, 36.0, -112.1, 36.1]
- Yellowstone: [-110.8, 44.5, -110.7, 44.6]

Coastal:
- San Francisco Bay: [-122.5, 37.7, -122.4, 37.8]
- Florida Keys: [-81.5, 24.6, -81.4, 24.7]

Mixed:
- Phoenix AZ: [-112.1, 33.4, -112.0, 33.5]
- Seattle WA: [-122.4, 47.5, -122.3, 47.6]
*/
