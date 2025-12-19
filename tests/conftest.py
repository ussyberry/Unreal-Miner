"""
Pytest fixtures for Unreal Miner tests
"""

import numpy as np
import pytest
import tempfile
from pathlib import Path
import rasterio
from rasterio.transform import from_origin


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_geotiff(temp_dir):
    """Create a sample single-band GeoTIFF for testing."""
    # Create sample data
    data = np.random.rand(100, 100).astype(np.float32)
    
    # Define geospatial properties
    transform = from_origin(-120.0, 40.0, 0.001, 0.001)  # lon, lat, pixel_x, pixel_y
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 1,
        'crs': 'EPSG:4326',
        'transform': transform
    }
    
    # Write to temporary file
    filepath = temp_dir / 'sample.tif'
    with rasterio.open(filepath, 'w', **profile) as dst:
        dst.write(data, 1)
    
    return filepath


@pytest.fixture
def sample_sar_geotiff(temp_dir):
    """Create a sample SAR GeoTIFF with VV and VH bands."""
    # Create sample SAR data (2 bands: VV, VH)
    vv_data = np.random.rand(100, 100).astype(np.float32) * 0.1 + 0.05  # Typical SAR backscatter range
    vh_data = vv_data * np.random.uniform(0.3, 0.7, size=(100, 100)).astype(np.float32)
    
    # Stack into 2-band array
    data = np.stack([vv_data, vh_data])
    
    # Define geospatial properties
    transform = from_origin(-120.0, 40.0, 0.001, 0.001)
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 2,
        'crs': 'EPSG:4326',
        'transform': transform
    }
    
    # Write to temporary file
    filepath = temp_dir / 'sample_sar.tif'
    with rasterio.open(filepath, 'w', **profile) as dst:
        dst.write(data)
    
    return filepath


@pytest.fixture
def sample_optical_geotiff(temp_dir):
    """Create a sample optical RGB GeoTIFF."""
    # Create sample RGB data (3 bands)
    r_data = np.random.rand(100, 100).astype(np.float32) * 0.3 + 0.1
    g_data = np.random.rand(100, 100).astype(np.float32) * 0.4 + 0.2
    b_data = np.random.rand(100, 100).astype(np.float32) * 0.3 + 0.1
    
    # Stack into 3-band array
    data = np.stack([r_data, g_data, b_data])
    
    # Define geospatial properties
    transform = from_origin(-120.0, 40.0, 0.001, 0.001)
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 3,
        'crs': 'EPSG:4326',
        'transform': transform
    }
    
    # Write to temporary file
    filepath = temp_dir / 'sample_optical.tif'
    with rasterio.open(filepath, 'w', **profile) as dst:
        dst.write(data)
    
    return filepath


@pytest.fixture
def sample_dem_geotiff(temp_dir):
    """Create a sample DEM GeoTIFF."""
    # Create realistic elevation data (100-1000m range)
    data = np.random.rand(100, 100).astype(np.float32) * 900 + 100
    
    # Add some spatial correlation (more realistic terrain)
    from scipy.ndimage import gaussian_filter
    data = gaussian_filter(data, sigma=5)
    
    # Define geospatial properties
    transform = from_origin(-120.0, 40.0, 0.001, 0.001)
    profile = {
        'driver': 'GTiff',
        'dtype': 'float32',
        'nodata': None,
        'width': 100,
        'height': 100,
        'count': 1,
        'crs': 'EPSG:4326',
        'transform': transform
    }
    
    # Write to temporary file
    filepath = temp_dir / 'sample_dem.tif'
    with rasterio.open(filepath, 'w', **profile) as dst:
        dst.write(data, 1)
    
    return filepath


@pytest.fixture
def sample_sar_data(sample_sar_geotiff):
    """Load sample SAR data as numpy arrays."""
    from unreal_miner.process_fusion import load_raster
    data, _, _, _ = load_raster(sample_sar_geotiff)
    return data


@pytest.fixture
def sample_optical_data(sample_optical_geotiff):
    """Load sample optical data as numpy arrays."""
    from unreal_miner.process_fusion import load_raster
    data, _, _, _ = load_raster(sample_optical_geotiff)
    return data


@pytest.fixture
def sample_dem_data(sample_dem_geotiff):
    """Load sample DEM data as numpy array."""
    from unreal_miner.process_fusion import load_raster
    data, _, _, _ = load_raster(sample_dem_geotiff, band=1)
    return data
