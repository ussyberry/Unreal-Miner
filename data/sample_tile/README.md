# Sample Tile Data

This directory contains a small sample tile for testing the Unreal Miner pipeline.

## Directory Structure

```
sample_tile/
├── raw/               # Raw Sentinel data (not committed to Git)
│   ├── s1_sample.zip  # Sentinel-1 GRD product
│   ├── s2_sample.zip  # Sentinel-2 L2A product
│   └── dem_srtm.tif   # SRTM DEM
└── processed/         # Pipeline outputs
    ├── s1_backscatter_geocorrected.tif
    ├── s2_rgb_mosaic.tif
    ├── anomaly_probability.tif
    ├── heightmap_16bit.png
    └── meta.json
```

## Data Policy

**Raw data is NOT committed to Git** due to file size.

To obtain sample data:
1. Run `scripts/fetch_copernicus.sh` with example AOI
2. Or download manually from [Copernicus Open Access Hub](https://scihub.copernicus.eu/)

## Example AOI

**Location**: Test mining site (Australia)
- Coordinates: 130.5°E to 131.5°E, 23.5°S to 22.5°S
- Size: ~10km × 10km
- Date: January 2024

## Processing Example

```bash
cd examples
./run_example.sh
```

This will process the sample tile through the complete pipeline.
