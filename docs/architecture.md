# Unreal Miner - System Architecture

## Overview

The Unreal Miner system is a modular, end-to-end pipeline for processing satellite imagery and generating AI-powered mineral exploration visualizations in Unreal Engine. The architecture follows a linear data processing flow with clear separation of concerns.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA ACQUISITION                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ ┌───────────┐ │
│  │ Sentinel-1   │  │ Sentinel-2   │  │   DEM Data   │ │ EMIT      │ │
│  │  GRD (SAR)   │  │  L2A (RGB)   │  │ (SRTM/ALOS)  │ │ L2A RFL   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ └─────┬─────┘ │
│         │                  │                  │             │       │
│         └──────────────────┴──────────────────┴─────────────┘       │
│                                │                                    │
└────────────────────────────────┼────────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PREPROCESSING & ALIGNMENT                       │
│  ┌──────────────────────────────┐  ┌──────────────────────────┐   │
│  │   Sentinel-1 Processing      │  │  Sentinel-2 Processing   │   │
│  │  • Apply-Orbit-File          │  │  • Cloud Masking (SCL)   │   │
│  │  • Thermal Noise Removal     │  │  • Resampling to 10m     │   │
│  │  • Radiometric Calibration   │  │  • Band Selection (RGB)  │   │
│  │  • Speckle Filtering         │  │  • Atmospheric Correction│   │
│  │  • Multilook (optional)      │  │  • RGB Composite         │   │
│  │  • Terrain Correction        │  │  • GeoTIFF Export        │   │
│  │  • LinearToFromdB            │  └──────────┬───────────────┘   │
│  │  • GeoTIFF Export (VV, VH)   │             │                    │
│  └──────────────┬───────────────┘             │                    │
│                 │                               │                    │
│                 └───────────────┬───────────────┘                    │
│                                 │                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GDAL ALIGNMENT & STACKING                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Reproject all rasters to common UTM CRS                  │   │
│  │  • Align to identical pixel grid (10m resolution)           │   │
│  │  • Clip to common AOI extent                                │   │
│  │  • Create VRT stack for multi-band access                   │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│           PYTHON FEATURE EXTRACTION & AI CLASSIFICATION              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  FEATURE ENGINEERING                                        │   │
│  │  • SAR Metrics: VV/VH ratio, cross-polarization, texture    │   │
│  │  • Optical Indices: NDVI, NDWI, RGB statistics              │   │
│  │  • Hyperspectral Indices: Iron, clay, carbonates (from EMIT)│   │
│  │  • Terrain Features: Slope, aspect, curvature, roughness    │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  MACHINE LEARNING / AI MINERAL CLASSIFICATION               │   │
│  │  • Supervised: RandomForest, SVM, XGBoost                   │   │
│  │  • Training Data: Labeled mineral samples                   │   │
│  │  • Deep Learning: CNNs for spectral feature extraction      │   │
│  │  • Output: Mineral classification map (integer labels)      │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UNREAL ENGINE EXPORT                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Heightmap: 16-bit PNG, power-of-2 + 1 sizing             │   │
│  │  • Textures: RGB base imagery (sRGB PNG/JPEG)               │   │
│  │  • Overlays: Mineral classification maps (color-coded)      │   │
│  │  • Metadata: meta.json (CRS, transforms, Z-scale)           │   │
│  │  • Optional: Vector layers (CSV/LAS point clouds)           │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   UNREAL ENGINE VISUALIZATION                        │
│  ┌──────────────────────┐         ┌──────────────────────────┐     │
│  │  Native Landscape    │   OR    │  Cesium for Unreal       │     │
│  │  • Local projection  │         │  • Global georeferencing │     │
│  │  • Custom materials  │         │  • Streaming tiles       │     │
│  │  • LOD management    │         │  • 3D Tiles/Quantized    │     │
│  └──────────────────────┘         └──────────────────────────┘     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  INTERACTIVE FEATURES                                       │   │
│  │  • Real-time anomaly overlay opacity                        │   │
│  │  • Adjustable vertical exaggeration                         │   │
│  │  • Multi-temporal visualization toggle                      │   │
│  │  • Color ramp customization                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Acquisition Layer

**Purpose**: Fetch satellite imagery and elevation data from remote APIs

**Components**:
- `scripts/fetch_copernicus.sh`: Automated download from Copernicus Open Access Hub.
- `scripts/fetch_emit.py`: Automated download from NASA Earthdata (using `earthaccess`).
- API credentials management via `.env` file.
- Local caching and file management.

**Inputs**:
- AOI coordinates (bounding box or polygon)
- Date range for temporal analysis
- Sensor specifications (S1 GRD, S2 L2A, EMIT L2A RFL)

**Outputs**:
- `data/raw/s1_*.zip`: Sentinel-1 GRD products
- `data/raw/s2_*.zip`: Sentinel-2 L2A products
- `data/raw/dem_*.tif`: DEM rasters
- `data/raw/emit_*.nc`: EMIT L2A Reflectance products

### 2. SNAP Preprocessing Layer

**Purpose**: Convert raw satellite products to calibrated, geocorrected rasters

**Technology Stack**:
- ESA SNAP Toolbox (gpt command-line interface)
- XML graph processing templates
- SNAP operators for SAR and optical processing

**Sentinel-1 Processing Chain** (`snap/s1_preproc.xml`):
1. **Read**: Load S1 GRD product
2. **Apply-Orbit-File**: Precise orbit correction
3. **Thermal-Noise-Removal**: Remove sensor noise
4. **Calibration**: Convert DN to sigma0 backscatter
5. **Speckle-Filter**: Lee or Refined Lee filter (5×5 or 7×7 window)
6. **Multilook**: Optional averaging for noise reduction
7. **Terrain-Correction**: Range-Doppler with DEM (SRTM 1")
8. **LinearToFromdB**: Convert to dB scale for visualization
9. **Write**: Export as GeoTIFF (VV, VH bands)

**Sentinel-2 Processing Chain** (`snap/s2_preproc.xml`):
1. **Read**: Load S2 L2A product
2. **Subset**: Crop to AOI extent
3. **Resample**: Align all bands to 10m resolution
4. **Cloud-Mask**: Apply Scene Classification Layer (SCL)
5. **Band-Merge**: Combine B04 (Red), B03 (Green), B02 (Blue)
6. **Write**: Export RGB GeoTIFF

**Outputs**:
- `data/processed/s1_backscatter_geocorrected.tif`: 2-band GeoTIFF (VV, VH)
- `data/processed/s2_rgb_mosaic.tif`: 3-band GeoTIFF (R, G, B)

### 3. GDAL Alignment Layer

**Purpose**: Ensure all rasters share identical CRS, resolution, and extent

**Technology Stack**:
- GDAL/OGR utilities (`gdalwarp`, `gdalbuildvrt`)
- Shell scripts for automation

**Processing Steps**:
1. **CRS Unification**: Reproject to target UTM zone
   ```bash
   gdalwarp -t_srs EPSG:32633 -tr 10 10 -r bilinear input.tif output.tif
   ```
2. **Extent Alignment**: Clip to common bounding box
   ```bash
   gdalwarp -te xmin ymin xmax ymax input.tif output.tif
   ```
3. **VRT Stack Creation**: Virtual raster for efficient multi-band access
   ```bash
   gdalbuildvrt -separate stack.vrt s1.tif s2.tif dem.tif
   ```

**Outputs**:
- `data/aligned/s1_backscatter_10m_utm.tif`
- `data/aligned/s2_rgb_10m_utm.tif`
- `data/aligned/dem_10m_utm.tif`
- `data/aligned/stack.vrt`

### 4. Feature Extraction & AI Analysis Layer

**Purpose**: Compute geophysical features and classify minerals using machine learning

**Technology Stack**:
- Python 3.9+
- Libraries: `rasterio`, `numpy`, `scipy`, `scikit-learn`, `tensorflow` (optional)
- Jupyter notebooks for interactive analysis

**Feature Engineering** (`scripts/process_fusion.py`):

**SAR Features**:
- **VV/VH Ratio**: Cross-polarization ratio (sensitive to surface roughness)
- **Texture Metrics**: GLCM contrast, entropy, correlation
- **Local Statistics**: Focal mean, std deviation, coefficient of variation
- **Temporal Features**: Multi-date coherence, intensity change

**Optical Features**:
- **NDVI**: `(NIR - Red) / (NIR + Red)` - vegetation index
- **NDWI**: `(Green - NIR) / (Green + NIR)` - water index
- **RGB Statistics**: Mean, std deviation, brightness

**Hyperspectral Features (from EMIT)**:
- **Iron Index**: Based on absorption features around 850-950 nm.
- **Clay Index**: Based on absorption features around 2100-2300 nm.
- **Carbonate Index**: Based on absorption features around 2300-2350 nm.

**Terrain Features**:
- **Slope**: First derivative of elevation
- **Aspect**: Direction of slope
- **Curvature**: Second derivative (convex/concave)
- **Roughness**: Local elevation variance

**Mineral Classification Models**:

1. **RandomForestClassifier** (Primary):
   - Supervised classification
   - Robust to high-dimensional data and feature scaling.
   - Provides feature importance scores.

2. **Support Vector Machine (SVM)**:
   - Effective in high-dimensional spaces.
   - Kernel tricks for non-linear classification.

3. **Deep Learning** (Optional):
   - 1D CNNs for spectral feature extraction from EMIT data.
   - Transfer learning from existing mineral spectral libraries.

**Outputs**:
- `classification_map.tif`: Integer raster with mineral class labels.
- `feature_stack.tif`: Multi-band feature raster.
- `classification_report.txt`: F1 scores, precision, recall for each class.

### 5. Unreal Export Layer

**Purpose**: Convert geospatial data to Unreal Engine compatible formats

**Technology Stack**:
- Python script: `scripts/export_unreal.py`
- Libraries: `rasterio`, `imageio`, `json`

**Export Operations**:

1. **Heightmap Conversion**:
   - Read DEM GeoTIFF
   - Resample to Unreal-compatible size (e.g., 4097×4097)
   - Normalize to 0-65535 range (16-bit)
   - Export as PNG
   - Calculate Z-scale: `(max_elev - min_elev) / 65535 × 100` (cm)

2. **Texture Export**:
   - RGB base imagery: Convert to sRGB PNG (power-of-2 dimensions)
   - Anomaly overlay: Normalize to 0-255, export as grayscale PNG

3. **Metadata Generation** (`meta.json`):
   ```json
   {
     "tile_id": "AOI_001",
     "crs": "EPSG:32633",
     "bbox": [xmin, ymin, xmax, ymax],
     "pixel_size_m": 10.0,
     "width": 4097,
     "height": 4097,
     "min_elevation_m": 145.3,
     "max_elevation_m": 892.7,
     "z_scale_cm": 1.145,
     "processing_date": "2024-11-12T10:30:00Z"
   }
   ```

**Outputs**:
- `heightmap_16bit.png`: Unreal Landscape heightmap
- `texture_rgb.png`: Base imagery texture
- `anomaly_overlay.png`: Anomaly heatmap overlay
- `meta.json`: Import parameters

### 6. Unreal Visualization Layer

**Purpose**: Interactive 3D visualization of terrain and anomalies

**Implementation Options**:

**Option A: Native Unreal Landscape**
- Best for: Local-scale projects, custom materials, offline visualization
- Import heightmap via Landscape tool
- Apply custom materials with anomaly overlays
- Manual georeferencing via world coordinates

**Option B: Cesium for Unreal**
- Best for: Global-scale projects, precise georeferencing, streaming data
- Use CesiumGeoreference actor for coordinate transforms
- Stream raster overlays and 3D Tiles
- Automatic CRS handling

**Material Graph Architecture**:
- **Base Layer**: RGB texture mapped via world coordinates
- **Anomaly Overlay**: Lerp between base and heatmap color based on probability
- **SAR Roughness**: Drive surface roughness/normal from SAR backscatter
- **Interactive Parameters**:
  - `P_AnomalyOpacity` (0-1): Blend strength
  - `P_AnomalyColorLow`, `P_AnomalyColorHigh`: Color ramp
  - `P_VerticalExaggeration` (1-10): Z-scale multiplier

**User Interactions**:
- Fly-through camera controls
- Real-time parameter adjustment via UI
- Click-to-query anomaly scores
- Multi-temporal timeline scrubbing

## Data Flow Summary

```
Raw Satellite Data (ZIP)
    ↓ [SNAP gpt]
Calibrated GeoTIFFs (VV, VH, RGB, EMIT)
    ↓ [GDAL warp]
Aligned Rasters (Common CRS, Grid)
    ↓ [Python rasterio]
Feature Vectors (N×M array)
    ↓ [scikit-learn]
Mineral Class Predictions (N×1 array)
    ↓ [Python imageio]
Unreal Assets (PNG, JSON)
    ↓ [Unreal Import]
Interactive 3D Scene
```

## Scalability Considerations

### Processing Performance
- **Parallel Processing**: Use `multiprocessing` for per-pixel operations
- **Chunked I/O**: Process large rasters in windowed chunks (rasterio.windows)
- **GPU Acceleration**: Optional CUDA/OpenCL for deep learning inference

### Data Volume Management
- **Tiling**: Split large AOIs into manageable tiles (10km × 10km)
- **Pyramid Levels**: Generate multiple resolutions for LOD
- **Compression**: Use LZW/DEFLATE for GeoTIFFs, DXT for textures

### Cloud Deployment (Future)
- Docker containerization for processing pipeline
- AWS/GCP batch processing for parallel tile generation
- Cloud storage for large datasets (S3, Cloud Storage)

## Technology Dependencies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| SNAP | ESA SNAP Toolbox | ≥9.0 | SAR/optical preprocessing |
| GDAL | GDAL/OGR | ≥3.0 | Raster reprojection |
| Python | CPython | ≥3.9 | Feature extraction, ML |
| rasterio | rasterio | ≥1.3 | Raster I/O |
| numpy | NumPy | ≥1.21 | Array operations |
| scikit-learn | scikit-learn | ≥1.0 | Machine learning |
| scipy | SciPy | ≥1.7 | Signal processing |
| imageio | imageio | ≥2.9 | Image export |
| Unreal Engine | Unreal Engine | ≥5.0 | 3D visualization |
| Cesium for Unreal | Plugin | ≥2.0 | Georeferencing |

## Security & Credentials

- **API Keys**: Store in `.env` file (never commit)
- **Data Privacy**: Do not commit raw satellite data (use `.gitignore`)
- **Licensing**: Respect Copernicus data usage terms

## Future Enhancements

1. **Real-time Processing**: Integrate with Copernicus streaming API
2. **Multi-sensor Fusion**: Add Landsat, ASTER, hyperspectral data
3. **Deep Learning**: Implement CNN-based mineral classifiers
4. **InSAR**: Add interferometric analysis for deformation detection
5. **Cloud Platform**: Deploy as web service with REST API
6. **Validation Tools**: Ground truth comparison and accuracy metrics

---

**Last Updated**: 2024-11-12  
**Maintained By**: Unreal Miner Development Team
