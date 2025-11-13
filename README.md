# Unreal Miner

**SAR Satellite Data Converted to Unreal Engine Visuals For Virtual Remote Mineral Exploration**

A proof-of-concept pipeline that converts Sentinel-1 (SAR) and Sentinel-2 (optical) Copernicus satellite data into fused anomaly products and georeferenced assets ready for interactive visualization in Unreal Engine (native Landscape or Cesium for Unreal). This repository enables AI-powered remote mineral identification by processing satellite imagery through advanced machine learning techniques.

## 🎯 Project Overview

This project provides an end-to-end, reproducible pipeline from Copernicus satellite data downloads through SNAP preprocessing, GDAL alignment, Python-based fusion and anomaly detection, to final export for Unreal Engine visualization. The system uses AI to identify potential mineral deposits by analyzing SAR backscatter patterns, optical imagery, and derived geophysical features.

### Key Features

- **Automated Satellite Data Processing**: Fetch and process Sentinel-1 GRD and Sentinel-2 L2A data via API
- **AI-Powered Anomaly Detection**: Machine learning models (IsolationForest, CNNs) identify geological anomalies
- **Geospatial Fusion**: Combine SAR and optical data with intelligent feature extraction
- **Unreal Engine Export**: Generate georeferenced heightmaps, textures, and anomaly overlays
- **Interactive Visualization**: Explore terrain and mineral anomalies in immersive 3D environments
- **Reproducible Pipeline**: Complete documentation and example data for validation

## 🚀 Quick Start

### Prerequisites

- **SNAP (Sentinel Application Platform)**: ESA Toolbox with `gpt` CLI
  - Download: https://step.esa.int/main/download/snap-download/
- **GDAL**: Geospatial Data Abstraction Library (≥3.0)
- **Python**: 3.9 or higher
- **Python Libraries**:
  ```bash
  pip install rasterio numpy scikit-learn scipy imageio jupyter gdal
  ```
- **Copernicus API Credentials**: Register at https://scihub.copernicus.eu/

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Unreal-Miner.git
cd Unreal-Miner

# Install Python dependencies
pip install -r requirements.txt

# Set up Copernicus credentials (edit with your credentials)
cp .env.example .env
# Edit .env with your Copernicus username and password
```

### Run the Example Pipeline

```bash
# Process the included sample tile (requires ~5-10 minutes)
cd examples
./run_example.sh

# View outputs in data/sample_tile/processed/
ls -lh ../data/sample_tile/processed/
```

The example pipeline will:
1. Process pre-downloaded Sentinel-1 and Sentinel-2 sample data
2. Run SNAP preprocessing for calibration and terrain correction
3. Align rasters with GDAL to common UTM grid
4. Extract features and detect anomalies using machine learning
5. Export Unreal-ready assets (heightmap, textures, anomaly maps)

## 📁 Repository Structure

```
Unreal-Miner/
├── README.md                    # This file
├── LICENSE                      # Project license
├── requirements.txt             # Python dependencies
├── CONTRIBUTING.md              # Contribution guidelines
├── CODE_OF_CONDUCT.md           # Community guidelines
├── CHANGELOG.md                 # Version history
│
├── .github/                     # GitHub configuration
│   ├── workflows/
│   │   └── ci.yml              # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docs/                        # Documentation
│   ├── architecture.md          # System architecture overview
│   ├── processing_pipeline.md  # Detailed pipeline steps
│   ├── unreal_import_checklist.md  # Unreal import guide
│   ├── cesium_notes.md          # Cesium for Unreal guide
│   └── validation_and_limitations.md  # Important caveats
│
├── data/                        # Data directory (not committed)
│   └── sample_tile/            # Small example dataset
│       ├── raw/                # Raw Sentinel data
│       └── processed/          # Pipeline outputs
│
├── snap/                        # SNAP graph templates
│   ├── s1_preproc.xml          # Sentinel-1 preprocessing
│   ├── s2_preproc.xml          # Sentinel-2 preprocessing
│   └── README.md               # SNAP usage guide
│
├── gdal/                        # GDAL helper scripts
│   ├── warp_examples.sh        # Reprojection examples
│   ├── build_vrt.sh            # VRT stacking
│   └── README.md
│
├── scripts/                     # Python processing scripts
│   ├── fetch_copernicus.sh     # Download Sentinel data
│   ├── process_fusion.py       # Core fusion & ML script
│   ├── export_unreal.py        # Unreal export utility
│   ├── utils.py                # CRS and helper functions
│   └── process_fusion_notebook.ipynb  # Interactive analysis
│
├── unreal/                      # Unreal Engine resources
│   ├── material_graph.md       # Material setup guide
│   ├── cesium_for_unreal_instructions.md
│   └── README.md
│
├── tests/                       # Unit tests
│   ├── test_processing.py
│   └── test_io.py
│
├── examples/                    # Example workflows
│   ├── run_example.sh          # Complete pipeline example
│   └── results_preview.md      # Expected outputs
│
└── meta/                        # Metadata schemas
    ├── metadata_schema.json    # Tile metadata spec
    └── sample_meta.json        # Example metadata
```

## 🔬 Pipeline Overview

### 1. Data Acquisition
- Fetch Sentinel-1 GRD (SAR) and Sentinel-2 L2A (optical) data for your Area of Interest (AOI)
- Download DEM data (SRTM/ALOS) for terrain correction

### 2. SNAP Preprocessing
- **Sentinel-1**: Calibration, speckle filtering, multilook, terrain correction → VV/VH backscatter GeoTIFFs
- **Sentinel-2**: Cloud masking, resampling, RGB composite generation

### 3. GDAL Alignment
- Reproject all rasters to common UTM CRS
- Align to identical pixel grids (10m resolution)
- Create VRT stacks for multi-band analysis

### 4. Feature Extraction & AI Anomaly Detection
- Compute SAR features: VV/VH ratio, local texture, roughness
- Extract optical indices: NDVI, RGB statistics
- Run machine learning models (IsolationForest, neural networks)
- Generate anomaly probability maps (0-1 float)

### 5. Unreal Engine Export
- Convert DEM to 16-bit heightmap (power-of-two + 1 sizing)
- Export RGB textures as sRGB PNG/JPEG
- Export anomaly maps as grayscale overlays
- Generate `meta.json` with CRS, transforms, and Z-scale parameters

### 6. Visualization in Unreal
- Import heightmap into Unreal Landscape or Cesium for Unreal
- Apply material graphs with anomaly heatmap overlays
- Interactive exploration with adjustable parameters

## 📊 Unreal Engine Import

### Quick Import Checklist

✅ **Coordinate System**: Use projected CRS (UTM) for the tile  
✅ **Heightmap Format**: 16-bit PNG, power-of-two + 1 dimensions (513, 1025, 2049, 4097)  
✅ **Texture Assets**: sRGB PNG/JPEG for base imagery, linear grayscale for anomalies  
✅ **Metadata**: Record CRS, pixel_size, min/max elevation in `meta.json`  
✅ **Z Scale Calculation**: `((max_h - min_h) / 65535) × 100 × vertical_exaggeration`  
✅ **Units**: Convert meters to centimeters for Unreal (multiply by 100)

See [docs/unreal_import_checklist.md](docs/unreal_import_checklist.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Branch naming conventions (`feature/`, `fix/`)
- Code style guidelines (PEP8, Black formatting)
- Pull request process and checklist
- Testing requirements

### Reporting Issues

Found a bug or have a feature request? Open an issue using our templates:
- Bug Report
- Feature Request
- Data Request
- Model Tuning

## 📖 Documentation

- **[Architecture Overview](docs/architecture.md)**: System design and data flow
- **[Processing Pipeline](docs/processing_pipeline.md)**: Step-by-step execution guide
- **[Unreal Import Guide](docs/unreal_import_checklist.md)**: Complete import instructions
- **[Validation & Limitations](docs/validation_and_limitations.md)**: Important caveats and best practices

## 🔐 Data Policy

- **No Large Files**: Do not commit raw satellite data (use Git LFS or external storage)
- **Sample Data**: Small representative tiles (<10MB) included for testing
- **API Credentials**: Never commit credentials (use `.env` files, add to `.gitignore`)
- **Download Scripts**: Use `scripts/fetch_copernicus.sh` to retrieve data on-demand

## ⚙️ System Requirements

### Minimum
- CPU: 4 cores
- RAM: 16 GB
- Storage: 50 GB free space
- GPU: Not required (CPU-based processing)

### Recommended
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 200 GB SSD
- GPU: NVIDIA GPU for deep learning models (optional)

## 🧪 Testing

Run unit tests to verify your environment:

```bash
cd tests
python -m pytest test_processing.py
python -m pytest test_io.py
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Maintainers

- **Project Lead**: Usman Alex Kadiri
- **Contact**: usman.kadiri@gmail.com
- **Issues**: https://github.com/yourusername/Unreal-Miner/issues

## 🌟 Acknowledgments

- **ESA Copernicus Programme**: Sentinel-1 and Sentinel-2 data
- **SNAP Toolbox**: SAR preprocessing capabilities
- **GDAL/Rasterio**: Geospatial data processing
- **Unreal Engine**: Interactive 3D visualization
- **Cesium for Unreal**: Geospatial integration

## 📚 References

- [Sentinel-1 Technical Guide](https://sentinel.esa.int/web/sentinel/technical-guides/sentinel-1-sar)
- [Sentinel-2 User Handbook](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi)
- [SNAP Documentation](https://step.esa.int/main/doc/)
- [Unreal Engine Landscapes](https://docs.unrealengine.com/5.0/en-US/landscape-technical-guide-in-unreal-engine/)
- [Cesium for Unreal](https://cesium.com/learn/unreal/)

---

**Note**: This is a proof-of-concept research tool. Anomaly detection results should be validated with ground truth data and expert geological interpretation before any commercial exploration decisions.
