# Data Acquisition Guide

This guide covers acquiring Sentinel-1 (SAR) and Sentinel-2 (optical) satellite data for Unreal Miner, including API setup, data selection, and troubleshooting.

## Copernicus Open Access Hub

The primary source for Sentinel data is the **ESA Copernicus Open Access Hub**.

### Registration

1. **Visit**: https://scihub.copernicus.eu/dhus/#/self-registration
2. **Complete Registration**:
   - Username (email address)
   - Password (strong, 8+ characters)
   - Accept terms and conditions
3. **Verify Email**: Check inbox and click verification link
4. **Wait for Activation**: 24-48 hours for account approval

**Alternative**: Some regions have national Copernicus mirrors (faster, no wait):
- Australia: https://copernicus.nci.org.au/
- Norway: https://colhub.met.no/

### Authentication

Once activated, add credentials to Unreal Miner:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add:
```bash
COPERNICUS_USERNAME=your_email@example.com
COPERNICUS_PASSWORD=your_strong_password
```

**Security**:
- Never commit `.env` to git (already in `.gitignore`)
- Use read-only permissions: `chmod 600 .env`

---

## API Access Methods

### Method 1: Web Interface (Manual)

**Good for**: Single-tile downloads, exploring available data

1. Visit https://scihub.copernicus.eu/dhus/#/home
2. Draw bounding box or enter coordinates
3. Set search filters:
   - **Sentinel-1**: Product Type = GRD, Sensor Mode = IW
   - **Sentinel-2**: Product Type = S2MSI2A, Cloud Cover < 10%
4. Select products and download

**Limitations**: Manual process, slow for multiple tiles

### Method 2: Command Line (Automated)

**Good for**: Batch processing, reproducible workflows

Unreal Miner includes a download script:

```bash
# Download Sentinel-1 for area and date range
./scripts/fetch_copernicus.sh \
  --sensor S1 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --bbox "-122.5,37.5,-122.0,38.0" \
  --product-type GRD \
  --output data/raw/

# Download Sentinel-2 (cloud cover < 10%)
./scripts/fetch_copernicus.sh \
  --sensor S2 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --bbox "-122.5,37.5,-122.0,38.0" \
  --cloud-cover 10 \
  --output data/raw/
```

### Method 3: Python API (sentinelsat)

**Good for**: Custom scripting, integration with other tools

```python
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date

# Connect to API
api = SentinelAPI('username', 'password', 'https://scihub.copernicus.eu/dhus')

# Define area of interest (AOI)
footprint = geojson_to_wkt(read_geojson('aoi.geojson'))

# Search for Sentinel-1 products
products = api.query(
    footprint,
    date=(date(2024, 1, 1), date(2024, 1, 31)),
    platformname='Sentinel-1',
    producttype='GRD',
    sensoroperationalmode='IW'
)

# Download all products
api.download_all(products, directory_path='data/raw/')
```

---

## Data Selection Guidelines

### Sentinel-1 (SAR)

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| **Product Type** | GRD (Ground Range Detected) | Preprocessed, ready for analysis |
| **Sensor Mode** | IW (Interferometric Wide Swath) | 250 km swath, 10m resolution |
| **Polarization** | Dual VV+VH | Both required for ratio calculation |
| **Orbit Direction** | Any (prefer Descending) | Descending = evening pass, consistent lighting |
| **Date Range** | Dry season preferred | Avoid snow/ice, heavy rain |
| **Temporal Baseline** | Single date or 3-month composite | Multi-temporal for speckle reduction |

**Example Search**:
```
Mission: Sentinel-1
Product Type: GRD
Sensor Mode: IW
Polarization: VV+VH
Start Date: 2024-06-01
End Date: 2024-08-31
```

### Sentinel-2 (Optical)

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| **Product Type** | L2A (Surface Reflectance) | Atmospherically corrected |
| **Processing Level** | Level-2A | Prefer over L1C (Top-of-Atmosphere) |
| **Cloud Cover** | < 10% (adjust per region) | Lower is better, 0-5% ideal |
| **Tile ID** | Match Sentinel-2 grid | Ensures consistent coverage |
| **Date Range** | Dry season, leaf-off | Maximize bedrock exposure |
| **Temporal Baseline** | Single cloud-free scene | Or multi-temporal cloud composite |

**Example Search**:
```
Mission: Sentinel-2
Product Type: S2MSI2A
Cloud Cover: 0-10%
Start Date: 2024-07-01
End Date: 2024-09-30
```

### DEM (Digital Elevation Model)

For terrain correction and elevation features:

| Source | Resolution | Coverage | Access |
|--------|------------|----------|--------|
| **SRTM v3** | 30m (1 arc-second) | Global (60°N-56°S) | https://earthexplorer.usgs.gov/ |
| **ALOS World 3D** | 30m | Global | https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/ |
| **Copernicus DEM** | 30m / 90m | Global | https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model |

**Recommendation**: Use **Copernicus DEM** (30m) for consistency with Sentinel data.

---

## Rate Limits and Quotas

### Copernicus Hub Limits

| Limit Type | Value | Notes |
|------------|-------|-------|
| **Concurrent Downloads** | 2 per user | Additional requests queued |
| **API Requests** | ~100 per minute | Throttled during peak hours |
| **Daily Download Limit** | None | Unlimited downloads |
| **File Size** | ~5-7 GB per Sentinel-1 scene | Expect long downloads |

**Best Practices**:
- Download during off-peak hours (evenings UTC)
- Use `--resume` flag to continue interrupted downloads
- Cache downloaded files to avoid re-downloading

### API Throttling

If you encounter `HTTP 429 Too Many Requests`:

```python
import time
from sentinelsat.exceptions import ServerError

try:
    api.download(product_id)
except ServerError as e:
    if e.response.status_code == 429:
        print("Rate limit hit, waiting 60 seconds...")
        time.sleep(60)
        api.download(product_id)  # Retry
```

---

## Alternative Data Sources

### AWS Open Data Registry

**Pros**: Fast downloads, no authentication, no rate limits  
**Cons**: Limited to recent data (~2 years)

**Sentinel-2 on AWS**:
```bash
# Install AWS CLI
pip install awscli

# List available tiles
aws s3 ls s3://sentinel-s2-l2a/ --no-sign-request

# Download specific tile
aws s3 cp s3://sentinel-s2-l2a/tiles/10/S/DG/2024/1/15/0/ . --recursive --no-sign-request
```

**Sentinel-1 on AWS**:
```bash
aws s3 ls s3://sentinel-s1-l1c/ --no-sign-request
```

### Google Earth Engine (GEE)

**Pros**: Server-side processing, no downloads, planetary-scale analysis  
**Cons**: JavaScript/Python API, steeper learning curve, export limits

**Setup**:
1. Register at https://earthengine.google.com/
2. Install Python API: `pip install earthengine-api`
3. Authenticate: `earthengine authenticate`

**Example**:
```python
import ee

ee.Initialize()

# Load Sentinel-1 image collection
s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
    .filterBounds(ee.Geometry.Point(-122.5, 37.5)) \
    .filterDate('2024-01-01', '2024-01-31') \
    .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))

# Compute mean composite
s1_mean = s1.mean()

# Export to Google Drive
task = ee.batch.Export.image.toDrive(
    image=s1_mean,
    description='S1_mean_export',
    scale=10,
    region=ee.Geometry.Point(-122.5, 37.5).buffer(5000).bounds()
)
task.start()
```

**Integration with Unreal Miner**: Export GEE results as GeoTIFF, then use Unreal Miner pipeline

### Microsoft Planetary Computer

**Pros**: Free STAC API, Jupyter notebooks, cloud processing  
**Cons**: Requires registration, less mature than GEE

**Access**: https://planetarycomputer.microsoft.com/

---

## Data Organization

### Recommended Directory Structure

```
data/
├── raw/                          # Downloaded SAFE files (never commit)
│   ├── sentinel1/
│   │   └── S1A_IW_GRDH_1SDV_20240115T...
│   └── sentinel2/
│       └── S2A_MSIL2A_20240115T...
├── processed/                    # SNAP outputs
│   ├── sentinel1_preprocessed/
│   └── sentinel2_preprocessed/
├── aligned/                      # GDAL warped rasters
│   ├── sar_vv.tif
│   ├── sar_vh.tif
│   └── rgb_composite.tif
└── final/                        # Unreal Engine assets
    ├── heightmap_16bit.png
    ├── anomaly_map.png
    └── meta.json
```

### Naming Convention

Use descriptive, parseable filenames:

```
S1_<TILE>_<DATE>_<PROCESSING>.tif
S2_<TILE>_<DATE>_<PROCESSING>.tif

Examples:
S1_10SDG_20240115_VV_calibrated.tif
S2_10SDG_20240115_RGB_composite.tif
```

---

## Troubleshooting

### Authentication Failed

**Error**: `HTTP 401 Unauthorized`

**Causes**:
- Incorrect username/password
- Account not yet activated (wait 24-48 hours)
- Password with special characters not properly escaped

**Solution**:
```bash
# Test credentials manually
curl -u "username:password" "https://scihub.copernicus.eu/dhus/search?q=*"

# If successful: HTTP 200 with XML response
```

### No Data Found

**Error**: `No products found for given criteria`

**Causes**:
- Incorrect date format
- Area outside Sentinel coverage
- Overly restrictive filters (e.g., 0% cloud cover)

**Solution**:
```bash
# Broaden search parameters
# 1. Expand date range
--start 2023-01-01 --end 2024-12-31

# 2. Increase cloud cover tolerance
--cloud-cover 30

# 3. Check if area is covered
# Visit: https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2/data-products
```

### Download Timeout

**Error**: `Connection timeout` or `Incomplete download`

**Causes**:
- Network instability
- Server overload
- Large file size (>5 GB)

**Solution**:
```bash
# Enable resume capability
wget --continue --user=USERNAME --password=PASSWORD <PRODUCT_URL>

# Or use sentinelsat with retry
api.download(product_id, max_attempts=5)
```

### Corrupted Download

**Error**: `Invalid SAFE format` or `Checksum mismatch`

**Solution**:
```bash
# Verify MD5 checksum
md5sum downloaded_file.zip
# Compare with value from Copernicus Hub

# Re-download if mismatch
rm downloaded_file.zip
./scripts/fetch_copernicus.sh --product-id <ID>
```

### High Cloud Cover in All Scenes

**Issue**: Cannot find cloud-free Sentinel-2 data for area

**Solutions**:
1. **Extend Date Range**: Try dry season months
2. **Use SAR Only**: Sentinel-1 unaffected by clouds
3. **Cloud Compositing**: Combine multiple partially cloudy scenes
4. **Sentinel-1 Optical Synthesis**: Use ML to generate synthetic optical from SAR (advanced)

---

## Data Quality Checks

### Pre-Processing Validation

Before investing processing time, validate downloads:

```bash
# Check Sentinel-1 SAFE structure
ls S1A_IW_GRDH_*.SAFE/measurement/
# Should contain: s1a-*-vv-*.tiff, s1a-*-vh-*.tiff

# Check Sentinel-2 SAFE structure
ls S2A_MSIL2A_*.SAFE/GRANULE/*/IMG_DATA/R10m/
# Should contain: *_B02_10m.jp2, *_B03_10m.jp2, *_B04_10m.jp2, *_B08_10m.jp2

# Verify raster validity
gdalinfo S1A_*.SAFE/measurement/s1a-*-vv-*.tiff
# Check: Driver, Size, CRS, No Error
```

### Post-Download Checklist

- [ ] File size reasonable (S1: ~5 GB, S2: ~1-2 GB)
- [ ] MD5 checksum matches (if provided)
- [ ] GDAL can open files without errors
- [ ] Coordinate reference system is geographic (WGS84) or UTM
- [ ] No excessive no-data regions (check with `gdalinfo -stats`)

---

## Advanced: Bulk Download Script

For downloading multiple tiles/dates:

```bash
#!/bin/bash
# scripts/bulk_download.sh

TILES=("10SDG" "10SEG" "10SFG")
DATES=("2024-01-15" "2024-04-15" "2024-07-15")

for tile in "${TILES[@]}"; do
    for date in "${DATES[@]}"; do
        echo "Downloading tile $tile for $date..."
        
        ./scripts/fetch_copernicus.sh \
            --sensor S1 \
            --tile "$tile" \
            --start "$date" \
            --end "$date" \
            --output "data/raw/tile_${tile}/"
        
        ./scripts/fetch_copernicus.sh \
            --sensor S2 \
            --tile "$tile" \
            --start "$date" \
            --end "$date" \
            --cloud-cover 10 \
            --output "data/raw/tile_${tile}/"
    done
done
```

---

## Cost Comparison

| Source | Cost | Speed | Ease | Best For |
|--------|------|-------|------|----------|
| **Copernicus Hub** | Free | Slow (2 concurrent) | Easy | Small projects, learning |
| **AWS Open Data** | Free (egress charged) | Fast | Medium | Recent data, batch processing |
| **Google Earth Engine** | Free (compute limits) | Very Fast | Hard | Large-scale analysis, research |
| **Commercial APIs** | $$ (per scene) | Very Fast | Easy | Time-critical, enterprise |

**Recommendation**: Start with Copernicus Hub, scale to AWS/GEE for production

---

## References

- **Copernicus Open Access Hub User Guide**: https://scihub.copernicus.eu/userguide/
- **sentinelsat Python Library**: https://sentinelsat.readthedocs.io/
- **AWS Sentinel Data**: https://registry.opendata.aws/sentinel-1/ & https://registry.opendata.aws/sentinel-2/
- **Google Earth Engine Datasets**: https://developers.google.com/earth-engine/datasets/catalog/sentinel

---

**Last Updated**: 2024-11-15  
**API Version**: Copernicus Open Access Hub v1.0
