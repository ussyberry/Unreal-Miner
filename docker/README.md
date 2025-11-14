# Docker Setup for Unreal Miner

This directory contains Docker configuration for fully containerized Unreal Miner environment.

## Quick Start

### Prerequisites

- Docker (≥20.10)
- Docker Compose (≥1.29)
- 50GB free disk space
- 16GB RAM minimum (32GB recommended)

### Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your Copernicus credentials**:
   ```bash
   nano .env
   # Set COPERNICUS_USER and COPERNICUS_PASSWORD
   ```

3. **Build the Docker image**:
   ```bash
   docker-compose build
   ```

### Usage

#### Interactive Shell

Run the pipeline interactively:

```bash
docker-compose run --rm unreal-miner
```

Inside the container:

```bash
# Process example data
cd examples
./run_example.sh

# Or run individual scripts
cd /workspace
python scripts/process_fusion.py --help
```

#### Jupyter Notebook

Start Jupyter Lab for interactive analysis:

```bash
docker-compose up jupyter
```

Access at: http://localhost:8888

#### Run Automated Pipeline

Execute the complete pipeline:

```bash
docker-compose run --rm unreal-miner ./scripts/run_pipeline.sh
```

## Architecture

### Image Layers

1. **Base**: GDAL 3.6.0 with geospatial libraries
2. **System Dependencies**: Java 11, Python 3, build tools
3. **SNAP Installation**: ESA SNAP 9.0.0 with Sentinel toolboxes
4. **Python Dependencies**: rasterio, scikit-learn, tensorflow
5. **Application Code**: Unreal Miner scripts

### Volumes

- `./data`: Persistent data storage
- `./scripts`: Processing scripts (hot-reload)
- `./config`: Configuration files
- `./tests`: Unit tests

## Configuration

### Environment Variables

Set in `.env` file or pass directly to `docker-compose run`:

| Variable | Description | Default |
|----------|-------------|---------|
| `COPERNICUS_USER` | Copernicus username | - |
| `COPERNICUS_PASSWORD` | Copernicus password | - |
| `CONTAMINATION` | Anomaly detection rate | 0.02 |
| `N_ESTIMATORS` | IsolationForest trees | 200 |
| `VERTICAL_EXAGGERATION` | Heightmap Z-scale | 2.0 |
| `TARGET_SIZE` | Unreal heightmap size | 4097 |

### Resource Limits

Edit `docker-compose.yml` to adjust CPU and memory limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 32G
```

## Troubleshooting

### SNAP Installation Issues

If SNAP installation fails during build:

```bash
# Build with verbose output
docker-compose build --no-cache --progress=plain
```

### Out of Memory

Increase Docker memory allocation in Docker Desktop settings or add swap:

```bash
# Check Docker stats
docker stats unreal-miner-pipeline
```

### Permission Issues

Ensure mounted volumes have correct permissions:

```bash
sudo chown -R $USER:$USER data/
```

## Advanced Usage

### Custom SNAP Graphs

Mount custom SNAP XML graphs:

```bash
docker-compose run --rm -v $(pwd)/custom_graphs:/workspace/snap unreal-miner
```

### GPU Support (TensorFlow)

Add GPU support for deep learning models:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update `docker-compose.yml`:

```yaml
services:
  unreal-miner:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

3. Rebuild:

```bash
docker-compose build
```

### CI/CD Integration

Use in GitHub Actions:

```yaml
- name: Build Docker image
  run: docker-compose build

- name: Run tests
  run: docker-compose run --rm unreal-miner pytest tests/
```

## Maintenance

### Update SNAP Version

Edit `Dockerfile`:

```dockerfile
ENV SNAP_VERSION=10.0.0
```

Rebuild:

```bash
docker-compose build --no-cache
```

### Clean Up

Remove containers and images:

```bash
docker-compose down
docker system prune -a
```

## Support

For issues related to Docker setup, open an issue with:

- Docker version: `docker --version`
- Docker Compose version: `docker-compose --version`
- Build logs: `docker-compose build --no-cache --progress=plain 2>&1 | tee build.log`
