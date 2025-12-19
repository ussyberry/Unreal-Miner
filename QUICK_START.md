# Quick Start Guide

## 5-Minute MVP Demo

### Prerequisites
```bash
# Python 3.9+
python --version

# Node.js 18+
node --version
```

### Installation
```bash
# Clone and setup
git clone https://github.com/ussyberry/Unreal-Miner.git
cd Unreal-Miner

# Python dependencies
pip install -r requirements.txt
pip install -e .

# Web dependencies
cd web && npm install && cd ..
```

### Run Demo
```bash
# Option 1: Command Line
python -m unreal_miner.process_fusion \
    --s1-path data/sample_tile/raw/s1.tif \
    --s2-path data/sample_tile/raw/s2.tif \
    --dem-path data/sample_tile/raw/dem.tif \
    --output-dir data/outputs \
    --demo-mode

# Option 2: Web Interface
cd web && npm run dev
# Open http://localhost:3000
```

### Expected Output
- `classification_map.tif` - Mineral classification results
- `feature_stack.tif` - All extracted features
- `meta.json` - Processing metadata

## Next Steps
1. Read [README.md](README.md) for full documentation
2. Review [FUNDING.md](FUNDING.md) for investment opportunities
3. Check [docs/](docs/) for technical details