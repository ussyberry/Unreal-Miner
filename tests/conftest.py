"""
Pytest configuration and shared fixtures for Unreal Miner tests.
"""

import numpy as np
import pytest
import tempfile
from pathlib import Path
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dem_data():
    """Generate sample DEM data for testing."""
    # Create a simple synthetic DEM (100x100)
    x = np.linspace(0, 10, 100)
    y = np.linspace(0, 10, 100)
    xx, yy = np.meshgrid(x, y)
    
    # Hills and valleys
    dem = (
        100 * np.sin(xx / 2) * np.cos(yy / 2) +
        50 * np.sin(xx) +
        200  # Base elevation
    )
    
    return dem.astype(np.float32)


@pytest.fixture
def sample_sar_data():
    """Generate sample SAR backscatter data (VV and VH)."""
    # Create synthetic SAR data (100x100, 2 bands)
    np.random.seed(42)
    
    vv = np.random.gamma(2.0, 2.0, (100, 100)).astype(np.float32)
    vh = vv * 0.3 + np.random.gamma(1.5, 1.0, (100, 100)).astype(np.float32)
    
    sar = np.stack([vv, vh], axis=0)
    return sar


@pytest.fixture
def sample_optical_data():
    """Generate sample optical RGB data."""
    # Create synthetic RGB data (100x100, 3 bands)
    np.random.seed(42)
    
    r = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
    g = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
    b = np.random.randint(50, 200, (100, 100), dtype=np.uint8)
    
    rgb = np.stack([r, g, b], axis=0).astype(np.float32)
    return rgb


@pytest.fixture
def sample_geotiff(temp_dir, sample_dem_data):
    """Create a sample GeoTIFF file for testing."""
    output_path = temp_dir / 'sample_dem.tif'
    
    # Define geospatial metadata
    transform = from_origin(600000, 4400000, 10, 10)  # UTM coordinates
    crs = CRS.from_epsg(32610)  # UTM Zone 10N
    
    # Write GeoTIFF
    profile = {
        'driver': 'GTiff',
        'height': sample_dem_data.shape[0],
        'width': sample_dem_data.shape[1],
        'count': 1,
        'dtype': rasterio.float32,
        'crs': crs,
        'transform': transform,
        'compress': 'lzw'
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(sample_dem_data, 1)
    
    return output_path


@pytest.fixture
def sample_sar_geotiff(temp_dir, sample_sar_data):
    """Create a sample SAR GeoTIFF (2 bands: VV, VH)."""
    output_path = temp_dir / 'sample_sar.tif'
    
    transform = from_origin(600000, 4400000, 10, 10)
    crs = CRS.from_epsg(32610)
    
    profile = {
        'driver': 'GTiff',
        'height': sample_sar_data.shape[1],
        'width': sample_sar_data.shape[2],
        'count': 2,
        'dtype': rasterio.float32,
        'crs': crs,
        'transform': transform,
        'compress': 'lzw'
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(sample_sar_data[0], 1)
        dst.write(sample_sar_data[1], 2)
    
    return output_path


@pytest.fixture
def sample_optical_geotiff(temp_dir, sample_optical_data):
    """Create a sample optical RGB GeoTIFF."""
    output_path = temp_dir / 'sample_rgb.tif'
    
    transform = from_origin(600000, 4400000, 10, 10)
    crs = CRS.from_epsg(32610)
    
    profile = {
        'driver': 'GTiff',
        'height': sample_optical_data.shape[1],
        'width': sample_optical_data.shape[2],
        'count': 3,
        'dtype': rasterio.float32,
        'crs': crs,
        'transform': transform,
        'compress': 'lzw'
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        for i in range(3):
            dst.write(sample_optical_data[i], i + 1)
    
    return output_path


@pytest.fixture
def sample_config():
    """Sample configuration dictionary."""
    return {
        'processing': {
            'contamination': 0.02,
            'n_estimators': 100,  # Reduced for faster tests
            'random_state': 42,
            'n_jobs': 1
        },
        'export': {
            'target_size': 513,  # Small for tests
            'texture_size': 512,
            'vertical_exaggeration': 2.0
        },
        'features': {
            'sar': {
                'enabled': True,
                'window_size': 3
            },
            'optical': {
                'enabled': True
            },
            'terrain': {
                'enabled': True,
                'window_size': 3
            }
        }
    }
