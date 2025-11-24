#!/bin/bash
# Unreal Miner - Example Pipeline Run

# Ensure we are in the project root or examples directory
if [ -d "../unreal_miner" ]; then
    cd ..
fi

# Create example directories
mkdir -p data/sample_tile/raw
mkdir -p data/sample_tile/processed
mkdir -p data/outputs

# Note: In a real scenario, you would download data here.
# For this example, we assume data exists or we'd need to generate dummy data.
# Since we don't have the raw data, we'll just show the commands that WOULD run.

echo "1. Preprocessing (Skipped - requires SNAP)"
# ./scripts/snap_process.sh ...

echo "2. Alignment (Skipped - requires GDAL)"
# ./scripts/align_rasters.sh ...

echo "3. Feature Extraction & Classification (Demo Mode)"
# We need dummy input files for this to actually run in the example
# Creating dummy inputs if they don't exist
if [ ! -f "data/aligned/s1_backscatter_10m_utm.tif" ]; then
    echo "Creating dummy input data for demonstration..."
    mkdir -p data/aligned
    # We can't easily create valid GeoTIFFs with bash alone without python/gdal
    # So we will rely on the user having data or just print the command.
fi

echo "Running process_fusion..."
echo "Command:"
echo "unreal-miner-process \\"
echo "    --s1-path data/aligned/s1_backscatter_10m_utm.tif \\"
echo "    --s2-path data/aligned/s2_rgb_10m_utm.tif \\"
echo "    --dem-path data/aligned/dem_10m_utm.tif \\"
echo "    --output-dir data/outputs/ \\"
echo "    --demo-mode"

# Uncomment to run if you have data:
# unreal-miner-process \
#     --s1-path data/aligned/s1_backscatter_10m_utm.tif \
#     --s2-path data/aligned/s2_rgb_10m_utm.tif \
#     --dem-path data/aligned/dem_10m_utm.tif \
#     --output-dir data/outputs/ \
#     --demo-mode

echo "4. Export to Unreal"
echo "Command:"
echo "unreal-miner-export \\"
echo "    --dem data/aligned/dem_10m_utm.tif \\"
echo "    --output-dir data/unreal_export/ \\"
echo "    --target-size 1025"

echo "Done! (This was a dry run/demo script)"
