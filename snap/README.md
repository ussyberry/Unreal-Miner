# SNAP Graph Templates

SNAP (Sentinel Application Platform) graph XML files for preprocessing satellite data.

## Files

- `s1_preproc.xml`: Sentinel-1 GRD preprocessing (calibration, speckle filtering, terrain correction)
- `s2_preproc.xml`: Sentinel-2 L2A preprocessing (resampling, cloud masking, RGB extraction)

## Usage

### Sentinel-1 Processing

```bash
gpt s1_preproc.xml \
  -Pinput=/path/to/S1A_IW_GRDH_*.zip \
  -Pdem=/path/to/dem.tif \
  -Poutput=/path/to/s1_backscatter.tif \
  -t /tmp/snap_temp/
```

### Sentinel-2 Processing

```bash
gpt s2_preproc.xml \
  -Pinput=/path/to/S2A_MSIL2A_*.zip \
  -Poutput=/path/to/s2_rgb.tif \
  -t /tmp/snap_temp/
```

## Parameters

- `-Pinput`: Input product path (ZIP or SAFE directory)
- `-Pdem`: External DEM GeoTIFF (optional, uses SRTM auto-download if omitted)
- `-Poutput`: Output GeoTIFF path
- `-t`: Temporary directory for intermediate files

## Requirements

- SNAP Toolbox 9.0+ with `gpt` command-line tool
- Internet connection (for orbit files and DEM auto-download)
- Sufficient disk space (~5-10 GB per product)

## Performance Tips

- Increase SNAP memory: Edit `snap.properties` and set `-Xmx16G` or higher
- Use SSD for temporary directory (`-t` parameter)
- Process multiple products in parallel (separate gpt instances)

## Customization

Edit XML files to modify processing parameters:
- Speckle filter type and window size
- Terrain correction resolution
- Output bands and format
