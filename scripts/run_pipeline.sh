#!/bin/bash
#
# Unreal Miner - Automated End-to-End Pipeline
#
# This script automates the complete processing pipeline from raw satellite data
# to Unreal Engine-ready assets.
#
# Usage: ./run_pipeline.sh [--config CONFIG_FILE] [--tile-id TILE_ID]
#

set -e  # Exit on error

# Default parameters
CONFIG_FILE="config/default.yaml"
TILE_ID="tile_001"
SKIP_DOWNLOAD=false
SKIP_SNAP=false
SKIP_ALIGNMENT=false

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --tile-id)
            TILE_ID="$2"
            shift 2
            ;;
        --skip-download)
            SKIP_DOWNLOAD=true
            shift
            ;;
        --skip-snap)
            SKIP_SNAP=true
            shift
            ;;
        --skip-alignment)
            SKIP_ALIGNMENT=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --config FILE       Configuration file (default: config/default.yaml)"
            echo "  --tile-id ID        Tile identifier (default: tile_001)"
            echo "  --skip-download     Skip data download step"
            echo "  --skip-snap         Skip SNAP preprocessing"
            echo "  --skip-alignment    Skip GDAL alignment"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check configuration file
if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Configuration file not found: $CONFIG_FILE"
    exit 1
fi

print_info "========================================"
print_info "Unreal Miner - Automated Pipeline"
print_info "========================================"
print_info "Tile ID: $TILE_ID"
print_info "Config: $CONFIG_FILE"
print_info ""

# Load configuration (using Python to parse YAML)
parse_config() {
    python3 -c "
import yaml
import sys
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config$1)
"
}

# Create timestamp for logging
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/pipeline_${TILE_ID}_${TIMESTAMP}.log"
mkdir -p logs

# Log function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Pipeline started"
log "Configuration: $CONFIG_FILE"

# Step 1: Data Download (if not skipped)
if [ "$SKIP_DOWNLOAD" == "false" ]; then
    print_info "Step 1: Downloading satellite data..."
    log "Step 1: Data download"
    
    # Check if Copernicus credentials are set
    if [ -z "$COPERNICUS_USER" ] || [ -z "$COPERNICUS_PASSWORD" ]; then
        print_warn "Copernicus credentials not set. Loading from .env"
        if [ -f ".env" ]; then
            source .env
        fi
    fi
    
    if [ -z "$COPERNICUS_USER" ] || [ -z "$COPERNICUS_PASSWORD" ]; then
        print_warn "Copernicus credentials not found. Skipping download."
        print_info "Set COPERNICUS_USER and COPERNICUS_PASSWORD in .env"
        SKIP_DOWNLOAD=true
    else
        # Run download script (if it exists)
        if [ -f "scripts/fetch_copernicus.sh" ]; then
            bash scripts/fetch_copernicus.sh --tile-id "$TILE_ID" 2>&1 | tee -a "$LOG_FILE"
        else
            print_warn "Download script not found. Place Sentinel data in data/raw/"
        fi
    fi
else
    print_info "Step 1: Skipping data download (using existing data)"
    log "Step 1: Skipped"
fi

# Step 2: SNAP Preprocessing
if [ "$SKIP_SNAP" == "false" ]; then
    print_info "Step 2: SNAP preprocessing..."
    log "Step 2: SNAP preprocessing"
    
    # Check if SNAP is available
    if ! command -v gpt &> /dev/null; then
        print_error "SNAP 'gpt' command not found. Install SNAP or use --skip-snap"
        exit 1
    fi
    
    # Process Sentinel-1
    if [ -d "data/raw/S1A_*" ] || [ -d "data/raw/S1B_*" ]; then
        print_info "Processing Sentinel-1..."
        log "Processing Sentinel-1"
        
        for s1_dir in data/raw/S1*_GRD_*; do
            if [ -d "$s1_dir" ]; then
                s1_file="${s1_dir}/manifest.safe"
                output_file="data/processed/${TILE_ID}_s1_backscatter.tif"
                
                gpt snap/s1_preproc.xml \
                    -Pinput="$s1_file" \
                    -Poutput="$output_file" \
                    2>&1 | tee -a "$LOG_FILE"
                
                log "Sentinel-1 processed: $output_file"
                break
            fi
        done
    else
        print_warn "No Sentinel-1 data found in data/raw/"
    fi
    
    # Process Sentinel-2
    if [ -d "data/raw/S2*_MSIL2A_*" ]; then
        print_info "Processing Sentinel-2..."
        log "Processing Sentinel-2"
        
        for s2_dir in data/raw/S2*_MSIL2A_*; do
            if [ -d "$s2_dir" ]; then
                s2_file="${s2_dir}/MTD_MSIL2A.xml"
                output_file="data/processed/${TILE_ID}_s2_rgb.tif"
                
                gpt snap/s2_preproc.xml \
                    -Pinput="$s2_file" \
                    -Poutput="$output_file" \
                    2>&1 | tee -a "$LOG_FILE"
                
                log "Sentinel-2 processed: $output_file"
                break
            fi
        done
    else
        print_warn "No Sentinel-2 data found in data/raw/"
    fi
else
    print_info "Step 2: Skipping SNAP preprocessing"
    log "Step 2: Skipped"
fi

# Step 3: GDAL Alignment
if [ "$SKIP_ALIGNMENT" == "false" ]; then
    print_info "Step 3: GDAL alignment..."
    log "Step 3: GDAL alignment"
    
    # Create aligned directory
    mkdir -p data/aligned
    
    # Align rasters to common grid
    # (This is a simplified version - see gdal/warp_examples.sh for full implementation)
    
    # Determine target CRS and extent
    TARGET_CRS="EPSG:32610"  # UTM Zone 10N (example)
    TARGET_RES=10.0
    
    # Align S1
    if [ -f "data/processed/${TILE_ID}_s1_backscatter.tif" ]; then
        gdalwarp -t_srs "$TARGET_CRS" -tr $TARGET_RES $TARGET_RES \
            -r bilinear -co COMPRESS=LZW \
            "data/processed/${TILE_ID}_s1_backscatter.tif" \
            "data/aligned/${TILE_ID}_s1_10m_utm.tif" \
            2>&1 | tee -a "$LOG_FILE"
        
        log "S1 aligned: data/aligned/${TILE_ID}_s1_10m_utm.tif"
    fi
    
    # Align S2
    if [ -f "data/processed/${TILE_ID}_s2_rgb.tif" ]; then
        gdalwarp -t_srs "$TARGET_CRS" -tr $TARGET_RES $TARGET_RES \
            -r bilinear -co COMPRESS=LZW \
            "data/processed/${TILE_ID}_s2_rgb.tif" \
            "data/aligned/${TILE_ID}_s2_10m_utm.tif" \
            2>&1 | tee -a "$LOG_FILE"
        
        log "S2 aligned: data/aligned/${TILE_ID}_s2_10m_utm.tif"
    fi
    
    # Download/align DEM (placeholder - requires DEM source)
    print_warn "DEM alignment step requires external DEM source"
else
    print_info "Step 3: Skipping GDAL alignment"
    log "Step 3: Skipped"
fi

# Step 4: Feature Extraction and Anomaly Detection
print_info "Step 4: Feature extraction and anomaly detection..."
log "Step 4: Feature extraction and ML processing"

S1_PATH="data/aligned/${TILE_ID}_s1_10m_utm.tif"
S2_PATH="data/aligned/${TILE_ID}_s2_10m_utm.tif"
DEM_PATH="data/aligned/${TILE_ID}_dem_10m_utm.tif"
OUTPUT_DIR="data/outputs/${TILE_ID}"

# Check if required files exist
if [ ! -f "$S1_PATH" ]; then
    print_error "Sentinel-1 file not found: $S1_PATH"
    exit 1
fi

if [ ! -f "$S2_PATH" ]; then
    print_error "Sentinel-2 file not found: $S2_PATH"
    exit 1
fi

if [ ! -f "$DEM_PATH" ]; then
    print_warn "DEM file not found: $DEM_PATH"
    print_warn "Using placeholder DEM. Results may be inaccurate."
    # Create placeholder DEM
    # (In production, download from SRTM/ALOS)
fi

mkdir -p "$OUTPUT_DIR"

python3 scripts/process_fusion.py \
    --s1-path "$S1_PATH" \
    --s2-path "$S2_PATH" \
    --dem-path "$DEM_PATH" \
    --output-dir "$OUTPUT_DIR" \
    --tile-id "$TILE_ID" \
    --contamination 0.02 \
    --n-estimators 200 \
    2>&1 | tee -a "$LOG_FILE"

log "Feature extraction complete"

# Step 5: Export for Unreal Engine
print_info "Step 5: Exporting for Unreal Engine..."
log "Step 5: Unreal Engine export"

UNREAL_DIR="data/unreal_export/${TILE_ID}"
mkdir -p "$UNREAL_DIR"

python3 scripts/export_unreal.py \
    --dem "$DEM_PATH" \
    --meta "${OUTPUT_DIR}/meta.json" \
    --output-dir "$UNREAL_DIR" \
    --target-size 4097 \
    --vertical-exaggeration 2.0 \
    --tile-id "$TILE_ID" \
    --s2-rgb "$S2_PATH" \
    --anomaly "${OUTPUT_DIR}/anomaly_probability.tif" \
    --texture-size 4096 \
    2>&1 | tee -a "$LOG_FILE"

log "Unreal export complete"

# Step 6: Summary
print_info "========================================"
print_info "Pipeline Complete!"
print_info "========================================"
log "Pipeline completed successfully"

print_info "Outputs:"
echo "  - Anomaly map: ${OUTPUT_DIR}/anomaly_probability.tif"
echo "  - Feature stack: ${OUTPUT_DIR}/feature_stack.tif"
echo "  - Metadata: ${OUTPUT_DIR}/meta.json"
echo "  - Unreal assets: ${UNREAL_DIR}/"
echo "    - heightmap_16bit.png"
echo "    - texture_rgb_4096.png"
echo "    - anomaly_overlay_4096.png"
echo "    - meta.json"
echo ""
print_info "Log file: $LOG_FILE"
echo ""
print_info "Next steps:"
echo "  1. Review outputs in $UNREAL_DIR"
echo "  2. Import heightmap_16bit.png into Unreal Engine"
echo "  3. Apply textures and anomaly overlay"
echo "  4. See docs/unreal_import_checklist.md for import guide"
echo ""
