# Unreal Miner - Troubleshooting Guide

This guide helps resolve common issues when using Unreal Miner.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Data Processing Errors](#data-processing-errors)
3. [SNAP Preprocessing Problems](#snap-preprocessing-problems)
4. [GDAL Alignment Issues](#gdal-alignment-issues)
5. [Machine Learning Errors](#machine-learning-errors)
6. [Unreal Engine Import Problems](#unreal-engine-import-problems)
7. [Performance Issues](#performance-issues)
8. [Docker-Specific Issues](#docker-specific-issues)

---

## Installation Issues

### Python Version Mismatch

**Problem**: `ImportError` or version compatibility errors

**Solution**:
```bash
# Check Python version (must be 3.9+)
python3 --version

# Create virtual environment with specific version
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### GDAL Installation Failure

**Problem**: `ModuleNotFoundError: No module named 'osgeo'`

**Solution**:

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install gdal-bin python3-gdal libgdal-dev
pip install gdal==$(gdal-config --version)
```

**macOS**:
```bash
brew install gdal
pip install gdal==$(gdal-config --version)
```

**Docker**: Use the provided Docker image which includes GDAL

### SNAP Installation Issues

**Problem**: `gpt` command not found

**Solution**:
1. Download SNAP from https://step.esa.int/main/download/snap-download/
2. Install with GUI or silent installer
3. Add to PATH:
```bash
export PATH="/opt/snap/bin:$PATH"
# Add to ~/.bashrc for persistence
```

---

## Data Processing Errors

### Insufficient Valid Pixels

**Problem**: `ValidationError: Insufficient valid pixels (45.2%) in file.tif`

**Causes**:
- Heavy cloud cover in optical data
- No-data regions in SAR or DEM
- Corrupted download

**Solutions**:
1. Download data for different date/time
2. Adjust `min_valid_pixels` in `config/default.yaml`:
```yaml
validation:
  min_valid_pixels: 0.3  # Lower threshold (not recommended)
```
3. Clip to region with valid data

### CRS Mismatch

**Problem**: `ValidationError: CRS mismatch: EPSG:32610 vs EPSG:4326`

**Solution**: Reproject rasters to same CRS before processing:
```bash
gdalwarp -t_srs EPSG:32610 -tr 10 10 input.tif output_reprojected.tif
```

Or disable CRS check (not recommended):
```yaml
validation:
  check_crs_match: false
```

### No Extent Overlap

**Problem**: `ValidationError: No extent overlap between rasters`

**Causes**:
- Downloaded data for different tiles/areas
- Incorrect file paths

**Solutions**:
1. Verify all inputs cover same geographic area
2. Check file paths in command
3. Use `gdalinfo` to inspect extents:
```bash
gdalinfo input.tif | grep "Upper Left\|Lower Right"
```

---

## SNAP Preprocessing Problems

### OutOfMemoryError in SNAP

**Problem**: `java.lang.OutOfMemoryError: Java heap space`

**Solution**: Increase SNAP memory:

Edit `$SNAP_HOME/bin/gpt.vmoptions`:
```
-Xmx16G  # Increase from default 4G
```

### SNAP Graph Execution Failure

**Problem**: `Error: [NodeId: Read] Failed to read product`

**Causes**:
- Invalid Sentinel product structure
- Missing manifest file
- Corrupted download

**Solutions**:
1. Re-download Sentinel data
2. Verify manifest.safe exists
3. Check SNAP version compatibility

### DEM Download Failure

**Problem**: `Error downloading DEM: Connection timeout`

**Solutions**:
1. Check internet connection
2. Use pre-downloaded DEM:
```bash
# Download SRTM manually
wget https://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_12_04.zip
unzip srtm_12_04.zip
```
3. Specify local DEM in SNAP graph

---

## GDAL Alignment Issues

### Reprojection Failure

**Problem**: `ERROR 1: Reprojection failed`

**Solutions**:
1. Check source CRS is valid:
```bash
gdalinfo input.tif | grep "Coordinate System"
```

2. Try different resampling method:
```bash
gdalwarp -r cubic input.tif output.tif  # Instead of bilinear
```

### Output File Too Large

**Problem**: Aligned rasters exceed disk space

**Solutions**:
1. Enable compression:
```bash
gdalwarp -co COMPRESS=LZW -co TILED=YES -co PREDICTOR=2 input.tif output.tif
```

2. Reduce resolution:
```bash
gdalwarp -tr 20 20 input.tif output_20m.tif  # Instead of 10m
```

3. Clip to smaller area:
```bash
gdalwarp -te xmin ymin xmax ymax input.tif output_clipped.tif
```

---

## Machine Learning Errors

### IsolationForest Memory Error

**Problem**: `MemoryError: Unable to allocate array`

**Solutions**:
1. Reduce `n_estimators` in config:
```yaml
processing:
  n_estimators: 50  # Reduce from 200
```

2. Process smaller tiles
3. Increase system RAM or use swap
4. Enable downsampling in `process_fusion.py`

### All Pixels Flagged as Anomalies

**Problem**: Anomaly map is all white (high scores)

**Causes**:
- Wrong contamination parameter
- Data normalization issue
- Feature extraction problem

**Solutions**:
1. Adjust contamination:
```yaml
processing:
  contamination: 0.01  # Lower value (1% anomalies)
```

2. Check input data validity:
```python
python scripts/validation.py --check-inputs
```

### No Anomalies Detected

**Problem**: Anomaly map is uniform (no anomalies)

**Solutions**:
1. Increase contamination:
```yaml
processing:
  contamination: 0.05  # Higher value
```

2. Check feature diversity:
```bash
python scripts/process_fusion.py --debug-features
```

---

## Unreal Engine Import Problems

### Heightmap Size Invalid

**Problem**: "Landscape heightmap size must be a power of two plus one"

**Solution**: Use valid sizes (127, 255, 511, 513, 1025, 2049, 4097, 8193):
```bash
python scripts/export_unreal.py --target-size 4097  # Valid
# Not: 4096 (invalid)
```

### Heightmap Appears Flat

**Problem**: Terrain has no relief in Unreal

**Causes**:
- Z Scale set incorrectly
- Vertical exaggeration too low
- DEM normalization issue

**Solutions**:
1. Increase vertical exaggeration:
```bash
python scripts/export_unreal.py --vertical-exaggeration 5.0
```

2. Check Z Scale in meta.json:
```json
{
  "unreal_import_parameters": {
    "z_scale_cm": 1.2345  // Should match elevation range
  }
}
```

3. In Unreal Landscape properties, set Z Scale from meta.json

### Texture Misalignment

**Problem**: RGB texture doesn't align with terrain

**Causes**:
- Different resolutions between heightmap and texture
- CRS mismatch
- Transform error

**Solutions**:
1. Ensure both use same extent:
```bash
gdalwarp -te_srs EPSG:32610 -te xmin ymin xmax ymax texture.tif aligned.tif
```

2. Match resolutions:
```yaml
export:
  target_size: 4097
  texture_size: 4096  # Should be compatible
```

### Anomaly Overlay Not Visible

**Problem**: Anomaly overlay appears solid or invisible

**Solutions**:
1. Check anomaly map statistics:
```bash
gdalinfo -stats data/outputs/anomaly_probability.tif
```

2. Adjust material blend mode in Unreal
3. Increase anomaly contrast in material

---

## Performance Issues

### Processing Very Slow

**Problem**: Pipeline takes hours to complete

**Solutions**:

**1. Enable Parallel Processing**:
```yaml
processing:
  n_jobs: -1  # Use all CPU cores
```

**2. Reduce Data Size**:
- Downsample to 20m resolution
- Process smaller tiles
- Use `contamination=0.02` and `n_estimators=100`

**3. Enable Caching**:
```yaml
processing:
  enable_cache: true
```

**4. Use SSD Storage**: Move data to SSD drive

**5. Docker Resource Limits**:
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 32G
```

### Out of Memory

**Problem**: Process killed due to memory usage

**Solutions**:
1. Process smaller tiles
2. Reduce feature window sizes:
```yaml
features:
  sar:
    window_size: 3  # Instead of 5
```
3. Increase swap space
4. Use cloud instance with more RAM

---

## Docker-Specific Issues

### Docker Build Fails

**Problem**: `ERROR: failed to solve: failed to fetch`

**Solutions**:
1. Check internet connection
2. Increase Docker build timeout
3. Use cached layers:
```bash
docker-compose build --no-cache  # Force rebuild
```

### Permission Denied in Container

**Problem**: `PermissionError: [Errno 13] Permission denied: '/workspace/data'`

**Solution**: Fix volume permissions:
```bash
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

### Container Out of Memory

**Problem**: Container killed by OOM killer

**Solution**: Increase Docker memory in Docker Desktop settings or:
```bash
# Linux: edit /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Soft": -1
    }
  }
}
```

---

## Getting Help

### Collect Diagnostic Information

Before reporting issues, collect:

1. **System info**:
```bash
python --version
gdal-config --version
gpt --version
docker --version  # If using Docker
```

2. **Log files**:
```bash
cat logs/pipeline_*.log
```

3. **Error messages**: Full traceback

4. **Sample data**: Minimal reproducible example

### Where to Get Help

1. **GitHub Issues**: https://github.com/ussyberry/Unreal-Miner/issues
2. **Discussions**: GitHub Discussions for questions
3. **Email**: usman.kadiri@gmail.com

### Reporting Bugs

Include:
- OS and version
- Python, GDAL, SNAP versions
- Full error message and traceback
- Steps to reproduce
- Relevant config files
- Sample data (if possible)

---

## Common Error Messages Reference

| Error Message | Likely Cause | Quick Fix |
|--------------|-------------|-----------|
| `ModuleNotFoundError: No module named 'rasterio'` | Missing dependencies | `pip install -r requirements.txt` |
| `ValidationError: Insufficient valid pixels` | Poor data quality | Download different date/area |
| `java.lang.OutOfMemoryError` | SNAP memory too low | Increase in gpt.vmoptions |
| `ERROR 1: Reprojection failed` | Invalid CRS | Check CRS with gdalinfo |
| `MemoryError: Unable to allocate` | Insufficient RAM | Reduce n_estimators, process smaller tiles |
| `Permission denied` | File permissions | `chmod 755` or check ownership |
| `Landscape size must be power of two plus one` | Invalid heightmap size | Use 513, 1025, 2049, 4097, 8193 |

---

## Advanced Troubleshooting

### Enable Debug Logging

Edit `config/default.yaml`:
```yaml
logging:
  level: DEBUG
  console: true
  file: ./logs/debug.log
```

### Profile Performance

```python
python -m cProfile -o profile.stats scripts/process_fusion.py [args]
python -m pstats profile.stats
```

### Memory Profiling

```bash
pip install memory_profiler
python -m memory_profiler scripts/process_fusion.py [args]
```

---

**Last Updated**: 2024-01-15

For the latest troubleshooting tips, see the [GitHub Wiki](https://github.com/ussyberry/Unreal-Miner/wiki).
