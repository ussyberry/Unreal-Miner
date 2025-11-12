# Processing Pipeline Guide

This document provides step-by-step instructions for executing the complete Unreal Miner pipeline from raw satellite data to Unreal Engine visualization.

## Prerequisites

Before starting, ensure you have:
- [ ] SNAP installed with `gpt` accessible in PATH
- [ ] GDAL tools installed (`gdalwarp`, `gdalbuildvrt`)
- [ ] Python 3.9+ with required packages (see `requirements.txt`)
- [ ] Copernicus API credentials configured in `.env`
- [ ] At least 50 GB free disk space

## Pipeline Stages

### Stage 1: Data Acquisition

#### 1.1 Define Area of Interest (AOI)

Create a bounding box for your study area in WGS84 coordinates:

```python
# Example: Mining region in Australia
AOI = {
    "lon_min": 130.5,
    "lat_min": -23.5,
    "lon_max": 131.5,
    "lat_max": -22.5
}
```

#### 1.2 Download Sentinel-1 Data

Use the fetch script to download Sentinel-1 GRD products:

```bash
cd scripts
./fetch_copernicus.sh --sensor S1 \
  --bbox "130.5,-23.5,131.5,-22.5" \
  --start-date "2024-01-01" \
  --end-date "2024-03-31" \
  --output ../data/raw/s1/
```

**Parameters**:
- `--sensor`: S1 (Sentinel-1) or S2 (Sentinel-2)
- `--bbox`: lon_min,lat_min,lon_max,lat_max
- `--start-date` / `--end-date`: ISO format dates
- `--output`: Output directory for downloads

**Expected Output**:
```
data/raw/s1/S1A_IW_GRDH_1SDV_20240115T213045_*.zip
data/raw/s1/S1A_IW_GRDH_1SDV_20240127T213046_*.zip
...
```

#### 1.3 Download Sentinel-2 Data

```bash
./fetch_copernicus.sh --sensor S2 \
  --bbox "130.5,-23.5,131.5,-22.5" \
  --start-date "2024-01-01" \
  --end-date "2024-03-31" \
  --max-cloud 20 \
  --output ../data/raw/s2/
```

**Additional Parameters**:
- `--max-cloud`: Maximum cloud coverage percentage (0-100)

**Expected Output**:
```
data/raw/s2/S2A_MSIL2A_20240110T013711_*.zip
data/raw/s2/S2B_MSIL2A_20240115T013709_*.zip
...
```

#### 1.4 Download DEM Data

Download SRTM 1" DEM for terrain correction:

```bash
# Using GDAL VRT and NASA Earthdata
gdal_translate -projwin 130.5 -22.5 131.5 -23.5 \
  /vsicurl/https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/... \
  ../data/raw/dem/srtm_aoi.tif
```

Or manually download from:
- NASA Earthdata: https://search.earthdata.nasa.gov/
- OpenTopography: https://opentopography.org/

---

### Stage 2: SNAP Preprocessing

#### 2.1 Sentinel-1 Preprocessing

Process each S1 GRD product through the SNAP graph:

```bash
cd snap

# Single product processing
gpt s1_preproc.xml \
  -Pinput=../data/raw/s1/S1A_IW_GRDH_*.zip \
  -Pdem=../data/raw/dem/srtm_aoi.tif \
  -Poutput=../data/processed/s1_backscatter_20240115.tif \
  -t ../tmp/

# Batch processing all products
for s1_file in ../data/raw/s1/*.zip; do
  base=$(basename "$s1_file" .zip)
  gpt s1_preproc.xml \
    -Pinput="$s1_file" \
    -Pdem=../data/raw/dem/srtm_aoi.tif \
    -Poutput="../data/processed/s1_${base}.tif" \
    -t ../tmp/
done
```

**SNAP Graph Operators** (`s1_preproc.xml`):
1. **Read**: Load S1 GRD product
2. **Apply-Orbit-File**: Download and apply precise orbit
3. **Thermal-Noise-Removal**: Remove additive noise
4. **Calibration**: Convert to sigma0 backscatter
5. **Speckle-Filter**: Refined Lee 7×7 window
6. **Terrain-Correction**: Range-Doppler with SRTM DEM
7. **LinearToFromdB**: Convert to dB scale
8. **Write**: Export GeoTIFF (bands: VV_dB, VH_dB)

**Processing Time**: ~10-15 minutes per scene (depends on AOI size)

**Troubleshooting**:
- **Out of Memory**: Increase SNAP memory in `snap.properties` (e.g., `-Xmx16G`)
- **Orbit file not found**: Ensure internet connection for automatic download
- **DEM errors**: Verify DEM covers full AOI extent

#### 2.2 Sentinel-2 Preprocessing

Process S2 L2A products:

```bash
cd snap

# Single product
gpt s2_preproc.xml \
  -Pinput=../data/raw/s2/S2A_MSIL2A_*.zip \
  -Poutput=../data/processed/s2_rgb_20240110.tif \
  -t ../tmp/

# Batch processing
for s2_file in ../data/raw/s2/*.zip; do
  base=$(basename "$s2_file" .zip)
  gpt s2_preproc.xml \
    -Pinput="$s2_file" \
    -Poutput="../data/processed/s2_${base}.tif" \
    -t ../tmp/
done
```

**SNAP Graph Operators** (`s2_preproc.xml`):
1. **Read**: Load S2 L2A product
2. **Subset**: Crop to AOI extent
3. **Resample**: Align all bands to 10m
4. **IdePix**: Cloud masking (or use SCL band)
5. **Mask**: Apply cloud mask
6. **Band-Merge**: Combine B04 (Red), B03 (Green), B02 (Blue)
7. **Write**: Export RGB GeoTIFF

**Processing Time**: ~5-10 minutes per scene

**Optional: Create Cloud-Free Mosaic**:
If multiple dates, composite to cloud-free mosaic:
```bash
gdal_calc.py -A s2_date1.tif -B s2_date2.tif \
  --outfile=s2_mosaic.tif \
  --calc="numpy.where(A>0, A, B)" \
  --NoDataValue=0
```

---

### Stage 3: GDAL Alignment

#### 3.1 Determine Target CRS

Choose UTM zone covering AOI center:

```python
# Python helper
from scripts.utils import get_utm_zone

lon_center = (130.5 + 131.5) / 2
lat_center = (-23.5 + -22.5) / 2
utm_epsg = get_utm_zone(lon_center, lat_center)
print(f"Target CRS: EPSG:{utm_epsg}")  # Example: EPSG:32753
```

#### 3.2 Reproject and Align Rasters

Use GDAL to create common grid:

```bash
cd gdal

# Set parameters
TARGET_EPSG=32753
RESOLUTION=10  # meters
XMIN=240000
YMIN=7400000
XMAX=340000
YMAX=7500000

# Reproject S1 backscatter
gdalwarp -t_srs EPSG:${TARGET_EPSG} \
  -tr ${RESOLUTION} ${RESOLUTION} \
  -r bilinear \
  -te ${XMIN} ${YMIN} ${XMAX} ${YMAX} \
  ../data/processed/s1_backscatter_20240115.tif \
  ../data/aligned/s1_backscatter_10m_utm.tif

# Reproject S2 RGB
gdalwarp -t_srs EPSG:${TARGET_EPSG} \
  -tr ${RESOLUTION} ${RESOLUTION} \
  -r bilinear \
  -te ${XMIN} ${YMIN} ${XMAX} ${YMAX} \
  ../data/processed/s2_rgb_20240110.tif \
  ../data/aligned/s2_rgb_10m_utm.tif

# Reproject DEM
gdalwarp -t_srs EPSG:${TARGET_EPSG} \
  -tr ${RESOLUTION} ${RESOLUTION} \
  -r cubic \
  -te ${XMIN} ${YMIN} ${XMAX} ${YMAX} \
  ../data/raw/dem/srtm_aoi.tif \
  ../data/aligned/dem_10m_utm.tif
```

**Resampling Methods**:
- `bilinear`: Good for continuous data (backscatter, RGB)
- `cubic`: Best for elevation (smoother terrain)
- `near`: Use for categorical data (land cover)

#### 3.3 Create VRT Stack

Build virtual raster for efficient multi-band access:

```bash
gdalbuildvrt -separate ../data/aligned/stack.vrt \
  ../data/aligned/s1_backscatter_10m_utm.tif \
  ../data/aligned/s2_rgb_10m_utm.tif \
  ../data/aligned/dem_10m_utm.tif
```

**Verify Alignment**:
```bash
gdalinfo ../data/aligned/s1_backscatter_10m_utm.tif | grep -E "Origin|Pixel Size"
gdalinfo ../data/aligned/s2_rgb_10m_utm.tif | grep -E "Origin|Pixel Size"
# Should match exactly
```

---

### Stage 4: Feature Extraction & Anomaly Detection

#### 4.1 Run Feature Extraction

Execute the main Python processing script:

```bash
cd scripts

python process_fusion.py \
  --s1-path ../data/aligned/s1_backscatter_10m_utm.tif \
  --s2-path ../data/aligned/s2_rgb_10m_utm.tif \
  --dem-path ../data/aligned/dem_10m_utm.tif \
  --output-dir ../data/outputs/ \
  --contamination 0.02 \
  --n-estimators 200
```

**Parameters**:
- `--s1-path`: Sentinel-1 VV/VH GeoTIFF
- `--s2-path`: Sentinel-2 RGB GeoTIFF
- `--dem-path`: DEM GeoTIFF
- `--output-dir`: Output directory for results
- `--contamination`: Expected anomaly rate (0.01-0.05)
- `--n-estimators`: IsolationForest trees (higher = more accurate, slower)

**Processing Steps**:
1. Load rasters with `rasterio`
2. Compute SAR features (VV/VH ratio, texture)
3. Compute optical features (NDVI, brightness)
4. Compute terrain features (slope, roughness)
5. Stack features into N×M array
6. Fit IsolationForest model
7. Predict anomaly scores
8. Normalize to 0-1 probability
9. Export results

**Outputs**:
```
data/outputs/anomaly_probability.tif  # Float32 anomaly map
data/outputs/feature_stack.tif        # All computed features
data/outputs/meta.json                # Processing metadata
data/outputs/model_stats.json         # Model performance metrics
```

#### 4.2 Interactive Analysis (Optional)

For parameter tuning and visualization:

```bash
jupyter notebook process_fusion_notebook.ipynb
```

**Notebook Sections**:
1. Data loading and visualization
2. Feature engineering exploration
3. Anomaly detection parameter tuning
4. Results visualization (matplotlib)
5. Statistical validation

---

### Stage 5: Unreal Engine Export

#### 5.1 Prepare Heightmap

Convert DEM to Unreal-compatible heightmap:

```bash
cd scripts

python export_unreal.py \
  --dem ../data/aligned/dem_10m_utm.tif \
  --meta ../data/outputs/meta.json \
  --output-dir ../data/unreal_export/ \
  --target-size 4097 \
  --vertical-exaggeration 2.0
```

**Parameters**:
- `--dem`: Input DEM GeoTIFF
- `--meta`: Metadata JSON from processing stage
- `--output-dir`: Output directory for Unreal assets
- `--target-size`: Unreal Landscape size (513, 1025, 2049, 4097, 8193)
- `--vertical-exaggeration`: Z-scale multiplier (1.0-10.0)

**Heightmap Processing**:
1. Read DEM and extract min/max elevation
2. Resample to target size (e.g., 4097×4097) using cubic interpolation
3. Normalize to 0-65535 (16-bit unsigned integer)
4. Export as PNG
5. Calculate Z-scale for Unreal import

#### 5.2 Export Textures

Export base imagery and overlays:

```bash
python export_unreal.py \
  --textures \
  --s2-rgb ../data/aligned/s2_rgb_10m_utm.tif \
  --anomaly ../data/outputs/anomaly_probability.tif \
  --output-dir ../data/unreal_export/ \
  --texture-size 4096
```

**Texture Processing**:
- **Base RGB**: Convert to sRGB color space, resize to power-of-2 (4096×4096)
- **Anomaly Overlay**: Normalize to 0-255, export as grayscale PNG

#### 5.3 Generate Metadata

The export script automatically creates `meta.json`:

```json
{
  "tile_id": "AOI_001",
  "crs": "EPSG:32753",
  "bbox": [240000, 7400000, 340000, 7500000],
  "pixel_size_m": 10.0,
  "width": 4097,
  "height": 4097,
  "min_elevation_m": 145.3,
  "max_elevation_m": 892.7,
  "elevation_range_m": 747.4,
  "z_scale_cm": 1.145,
  "vertical_exaggeration": 2.0,
  "processing_date": "2024-11-12T10:30:00Z",
  "unreal_import_parameters": {
    "landscape_size": "4097x4097",
    "sections_per_component": 1,
    "section_size": "127x127",
    "x_scale_cm": 1000.0,
    "y_scale_cm": 1000.0,
    "z_scale_cm": 1.145
  }
}
```

**Outputs**:
```
data/unreal_export/
├── heightmap_16bit.png        # Unreal Landscape heightmap
├── texture_rgb_4096.png       # Base imagery
├── anomaly_overlay_4096.png   # Anomaly heatmap
└── meta.json                  # Import parameters
```

---

### Stage 6: Unreal Engine Import

#### 6.1 Create New Landscape

1. Open Unreal Engine project
2. Navigate to **Landscape Mode** (Shift+2)
3. Select **Import from File** tab
4. Click **Heightmap File** → Select `heightmap_16bit.png`

#### 6.2 Configure Landscape Settings

Use values from `meta.json`:

- **Section Size**: 127×127 (or 63×63 for smaller tiles)
- **Sections Per Component**: 1 (or 2 for LOD)
- **Number of Components**: Auto-calculated from heightmap size
- **Location**: X=0, Y=0, Z=0 (adjust if multiple tiles)
- **Scale**:
  - **X**: 1000.0 (10m pixel × 100 cm/m)
  - **Y**: 1000.0
  - **Z**: 1.145 (from meta.json `z_scale_cm`)

#### 6.3 Import Textures

1. Import `texture_rgb_4096.png` as **Texture2D** (sRGB enabled)
2. Import `anomaly_overlay_4096.png` as **Texture2D** (Linear color space)

#### 6.4 Create Landscape Material

See [Unreal Material Graph Guide](../unreal/material_graph.md) for detailed material setup.

**Quick Setup**:
1. Create new Material → Name: `M_Terrain_Anomaly`
2. Add Texture Samples for RGB and anomaly textures
3. Add Landscape Layer Coordinates for UV mapping
4. Create Lerp node to blend anomaly overlay
5. Add Scalar Parameters: `P_AnomalyOpacity`, `P_VerticalExaggeration`
6. Apply material to Landscape

#### 6.5 Verify Import

**Checklist**:
- [ ] Landscape loads without errors
- [ ] Elevation range appears correct (not flat or exaggerated)
- [ ] Textures align with terrain (no obvious offset)
- [ ] Anomaly overlay appears in correct locations
- [ ] World coordinates match expected AOI extent

**Common Issues**:
- **Flat landscape**: Check Z-scale value
- **Extreme spikes**: Heightmap may have invalid data (re-export with `-nodata`)
- **Texture misalignment**: Verify all rasters used same CRS and extent
- **Seams**: Ensure heightmap is power-of-2 + 1 size

---

## Performance Optimization

### Processing Speed

**Parallel Processing**:
```python
# In process_fusion.py
from multiprocessing import Pool

def process_chunk(args):
    # Process window
    pass

with Pool(8) as p:  # 8 parallel workers
    results = p.map(process_chunk, chunks)
```

**Memory Management**:
```python
# Process large rasters in chunks
import rasterio
from rasterio.windows import Window

with rasterio.open('large.tif') as src:
    for ji, window in src.block_windows(1):
        data = src.read(window=window)
        # Process chunk
```

### Storage Optimization

**Compress GeoTIFFs**:
```bash
gdal_translate -co COMPRESS=LZW -co TILED=YES input.tif output.tif
```

**Generate Overviews**:
```bash
gdaladdo -r average output.tif 2 4 8 16
```

---

## Validation & Quality Control

### Visual Inspection

```python
# Quick visualization
import rasterio
import matplotlib.pyplot as plt

with rasterio.open('anomaly_probability.tif') as src:
    anomaly = src.read(1)
    
plt.imshow(anomaly, cmap='hot', vmin=0, vmax=1)
plt.colorbar(label='Anomaly Probability')
plt.title('Detected Anomalies')
plt.savefig('anomaly_preview.png', dpi=150)
```

### Statistical Validation

```python
# Check anomaly distribution
import numpy as np

anomaly_flat = anomaly[~np.isnan(anomaly)].flatten()
print(f"Mean: {anomaly_flat.mean():.4f}")
print(f"Std Dev: {anomaly_flat.std():.4f}")
print(f"P95: {np.percentile(anomaly_flat, 95):.4f}")
print(f"Max: {anomaly_flat.max():.4f}")
```

### Ground Truth Comparison

If known mineral deposits exist in AOI:

```python
# Load ground truth points
import geopandas as gpd

gt_points = gpd.read_file('known_deposits.geojson')

# Extract anomaly scores at GT locations
from rasterio.sample import sample_gen

with rasterio.open('anomaly_probability.tif') as src:
    coords = [(p.x, p.y) for p in gt_points.geometry]
    gt_scores = [s[0] for s in sample_gen(src, coords)]

print(f"Mean GT Score: {np.mean(gt_scores):.4f}")
print(f"Detection Rate (>0.5): {(np.array(gt_scores) > 0.5).mean():.2%}")
```

---

## Complete Example Workflow

```bash
#!/bin/bash
# Complete pipeline execution

# 1. Download data
cd scripts
./fetch_copernicus.sh --sensor S1 --bbox "130.5,-23.5,131.5,-22.5" \
  --start-date "2024-01-01" --end-date "2024-01-31" --output ../data/raw/s1/

# 2. Process with SNAP
cd ../snap
gpt s1_preproc.xml -Pinput=../data/raw/s1/*.zip \
  -Poutput=../data/processed/s1_backscatter.tif

# 3. Align with GDAL
cd ../gdal
./warp_examples.sh

# 4. Extract features and detect anomalies
cd ../scripts
python process_fusion.py --s1-path ../data/aligned/s1_backscatter_10m_utm.tif \
  --s2-path ../data/aligned/s2_rgb_10m_utm.tif \
  --dem-path ../data/aligned/dem_10m_utm.tif \
  --output-dir ../data/outputs/

# 5. Export for Unreal
python export_unreal.py --dem ../data/aligned/dem_10m_utm.tif \
  --meta ../data/outputs/meta.json \
  --output-dir ../data/unreal_export/ \
  --target-size 4097

echo "Pipeline complete! Import data/unreal_export/ into Unreal Engine."
```

---

**Last Updated**: 2024-11-12  
**Next**: See [Unreal Import Checklist](unreal_import_checklist.md) for detailed import instructions
