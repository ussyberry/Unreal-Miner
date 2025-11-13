#!/bin/bash
#
# Unreal Miner - Automated Environment Setup
# 
# This script sets up the complete development environment for Unreal Miner
# including Python dependencies, GDAL, and directory structure.
#
# Usage: ./setup_environment.sh [--docker]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in Docker
DOCKER_MODE=false
if [ "$1" == "--docker" ]; then
    DOCKER_MODE=true
    print_info "Running in Docker mode"
fi

print_info "Setting up Unreal Miner environment..."

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    print_error "Python 3.9+ required. Found: Python $PYTHON_VERSION"
    exit 1
fi

print_info "Python $PYTHON_VERSION detected ✓"

# Check GDAL installation
print_info "Checking GDAL installation..."
if ! command -v gdalinfo &> /dev/null; then
    print_warn "GDAL not found. Please install GDAL 3.0+"
    if [ "$DOCKER_MODE" == "false" ]; then
        print_info "Ubuntu/Debian: sudo apt-get install gdal-bin python3-gdal"
        print_info "macOS: brew install gdal"
        exit 1
    fi
else
    GDAL_VERSION=$(gdalinfo --version | awk '{print $2}' | cut -d, -f1)
    print_info "GDAL $GDAL_VERSION detected ✓"
fi

# Check SNAP installation (optional)
print_info "Checking SNAP installation..."
if command -v gpt &> /dev/null; then
    SNAP_VERSION=$(gpt --version 2>&1 | head -n1 || echo "unknown")
    print_info "SNAP detected: $SNAP_VERSION ✓"
else
    print_warn "SNAP not found. Install from: https://step.esa.int/main/download/snap-download/"
    print_warn "SNAP is required for Sentinel-1/2 preprocessing"
fi

# Create directory structure
print_info "Creating directory structure..."
mkdir -p data/{raw,processed,aligned,outputs,unreal_export,cache}
mkdir -p data/sample_tile/{raw,processed}
mkdir -p logs
mkdir -p config
mkdir -p tests
mkdir -p notebooks

print_info "Directory structure created ✓"

# Create virtual environment (if not in Docker)
if [ "$DOCKER_MODE" == "false" ]; then
    print_info "Creating Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_info "Virtual environment created ✓"
    else
        print_info "Virtual environment already exists ✓"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements.txt

print_info "Python dependencies installed ✓"

# Create .env file from example
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_warn "Please edit .env and add your Copernicus credentials"
else
    print_info ".env file already exists ✓"
fi

# Create default config file
print_info "Creating default configuration..."
cat > config/default.yaml <<EOF
# Unreal Miner - Default Configuration

# Processing parameters
processing:
  contamination: 0.02
  n_estimators: 200
  random_state: 42
  n_jobs: -1  # Use all CPU cores

# Export parameters
export:
  target_size: 4097
  texture_size: 4096
  vertical_exaggeration: 2.0

# Data paths
paths:
  data_dir: ./data
  raw_dir: ./data/raw
  processed_dir: ./data/processed
  aligned_dir: ./data/aligned
  output_dir: ./data/outputs
  unreal_export_dir: ./data/unreal_export
  cache_dir: ./data/cache

# Logging
logging:
  level: INFO
  format: '%(asctime)s - %(levelname)s - %(message)s'
  file: ./logs/pipeline.log

# Feature extraction
features:
  sar:
    - vv_vh_ratio
    - vv_texture
    - vv_mean
    - vh_mean
  optical:
    - brightness
    - ndvi_proxy
    - ndwi_proxy
    - rg_ratio
    - rb_ratio
  terrain:
    - slope
    - aspect
    - roughness
    - curvature

# SNAP preprocessing
snap:
  calibration:
    auxiliary_file: 'Latest Auxiliary File'
    output_sigma: true
  speckle_filter:
    filter: 'Lee Sigma'
    window_size: 7
  terrain_correction:
    dem_name: 'SRTM 1Sec HGT'
    pixel_spacing: 10.0
    resampling: 'BILINEAR_INTERPOLATION'
EOF

print_info "Default configuration created ✓"

# Create .gitkeep files for empty directories
touch data/.gitkeep
touch logs/.gitkeep
touch notebooks/.gitkeep

# Set up pre-commit hooks (if git repo)
if [ -d ".git" ]; then
    print_info "Setting up git hooks..."
    
    cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
# Pre-commit hook for code quality checks

echo "Running pre-commit checks..."

# Check for large files
large_files=$(find . -type f -size +10M ! -path "./.*" ! -path "./data/*")
if [ -n "$large_files" ]; then
    echo "ERROR: Large files detected (>10MB):"
    echo "$large_files"
    echo "Please use Git LFS or external storage"
    exit 1
fi

# Run black formatter
if command -v black &> /dev/null; then
    black --check scripts/ 2>&1 | head -5
    if [ $? -ne 0 ]; then
        echo "WARNING: Code formatting issues detected. Run: black scripts/"
    fi
fi

# Run flake8
if command -v flake8 &> /dev/null; then
    flake8 scripts/ --count --show-source --statistics --max-line-length=100
fi

echo "Pre-commit checks complete"
EOF
    
    chmod +x .git/hooks/pre-commit
    print_info "Git hooks configured ✓"
fi

# Print summary
print_info "========================================"
print_info "Environment setup complete!"
print_info "========================================"
echo ""
print_info "Next steps:"
echo "  1. Edit .env with your Copernicus credentials"
echo "  2. Review config/default.yaml"
echo "  3. Run example pipeline: cd examples && ./run_example.sh"
echo ""
if [ "$DOCKER_MODE" == "false" ]; then
    print_info "Activate environment: source venv/bin/activate"
fi
print_info "Run tests: pytest tests/"
echo ""

print_info "For Docker usage:"
echo "  docker-compose build"
echo "  docker-compose run --rm unreal-miner"
echo ""
