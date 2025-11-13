"""
Unit tests for export_unreal.py
"""

import numpy as np
import pytest
import sys
import json
from pathlib import Path
import imageio

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from export_unreal import (
    validate_unreal_size,
    resample_dem,
    export_heightmap,
    export_texture,
    UNREAL_SIZES
)


class TestUnrealSizeValidation:
    """Test Unreal landscape size validation."""
    
    def test_valid_sizes(self):
        """Test that valid Unreal sizes are recognized."""
        for size in UNREAL_SIZES:
            is_valid, nearest = validate_unreal_size(size)
            assert is_valid
            assert nearest == size
    
    def test_invalid_sizes(self):
        """Test that invalid sizes return nearest valid size."""
        # Test sizes that are not valid
        test_cases = [
            (100, 127),
            (500, 511),
            (1000, 1025),
            (4000, 4097),
            (8000, 8193)
        ]
        
        for invalid_size, expected_nearest in test_cases:
            is_valid, nearest = validate_unreal_size(invalid_size)
            assert not is_valid
            assert nearest == expected_nearest


class TestDEMResampling:
    """Test DEM resampling functionality."""
    
    def test_resample_upscale(self, sample_dem_data):
        """Test upscaling DEM."""
        target_size = 255
        resampled = resample_dem(sample_dem_data, target_size)
        
        assert resampled.shape == (target_size, target_size)
        assert resampled.dtype == sample_dem_data.dtype
    
    def test_resample_downscale(self, sample_dem_data):
        """Test downscaling DEM."""
        target_size = 51
        resampled = resample_dem(sample_dem_data, target_size)
        
        assert resampled.shape == (target_size, target_size)
    
    def test_resample_preserves_range(self, sample_dem_data):
        """Test that resampling preserves value range approximately."""
        target_size = 127
        resampled = resample_dem(sample_dem_data, target_size)
        
        # Check that min/max are similar (within 10% tolerance)
        original_range = np.ptp(sample_dem_data)
        resampled_range = np.ptp(resampled)
        
        assert abs(resampled_range - original_range) / original_range < 0.1


class TestHeightmapExport:
    """Test heightmap export functionality."""
    
    def test_export_heightmap_basic(self, temp_dir, sample_geotiff):
        """Test basic heightmap export."""
        output_dir = temp_dir / 'export'
        output_dir.mkdir()
        
        target_size = 513
        vertical_exaggeration = 2.0
        
        import_params, profile, transform, crs = export_heightmap(
            sample_geotiff, output_dir, target_size, vertical_exaggeration
        )
        
        # Check output file exists
        heightmap_path = output_dir / 'heightmap_16bit.png'
        assert heightmap_path.exists()
        
        # Check import parameters
        assert 'landscape_size' in import_params
        assert 'z_scale_cm' in import_params
        assert 'x_scale_cm' in import_params
        assert import_params['vertical_exaggeration'] == vertical_exaggeration
        
        # Load and check heightmap
        heightmap = imageio.imread(heightmap_path)
        assert heightmap.shape == (target_size, target_size)
        assert heightmap.dtype == np.uint16
    
    def test_heightmap_16bit_range(self, temp_dir, sample_geotiff):
        """Test that heightmap uses full 16-bit range."""
        output_dir = temp_dir / 'export'
        output_dir.mkdir()
        
        import_params, _, _, _ = export_heightmap(
            sample_geotiff, output_dir, 513, 1.0
        )
        
        heightmap_path = output_dir / 'heightmap_16bit.png'
        heightmap = imageio.imread(heightmap_path)
        
        # Should use significant portion of 16-bit range
        assert np.min(heightmap) < 10000  # Not all high values
        assert np.max(heightmap) > 50000  # Uses upper range
    
    def test_vertical_exaggeration_effect(self, temp_dir, sample_geotiff):
        """Test that vertical exaggeration affects Z scale."""
        output_dir = temp_dir / 'export'
        output_dir.mkdir()
        
        params_1, _, _, _ = export_heightmap(
            sample_geotiff, output_dir, 513, 1.0
        )
        
        output_dir_2 = temp_dir / 'export2'
        output_dir_2.mkdir()
        
        params_2, _, _, _ = export_heightmap(
            sample_geotiff, output_dir_2, 513, 2.0
        )
        
        # Z scale should double with 2x exaggeration
        assert abs(params_2['z_scale_cm'] / params_1['z_scale_cm'] - 2.0) < 0.01


class TestTextureExport:
    """Test texture export functionality."""
    
    def test_export_rgb_texture(self, temp_dir, sample_optical_geotiff):
        """Test RGB texture export."""
        output_name = 'test_texture.png'
        target_size = 512
        
        output_path = export_texture(
            sample_optical_geotiff, temp_dir, output_name, target_size, linear=False
        )
        
        assert output_path is not None
        assert output_path.exists()
        
        # Load and check texture
        texture = imageio.imread(output_path)
        assert texture.shape == (target_size, target_size, 3)
        assert texture.dtype == np.uint8
    
    def test_export_grayscale_texture(self, temp_dir, sample_geotiff):
        """Test grayscale texture export."""
        output_name = 'test_gray.png'
        target_size = 256
        
        output_path = export_texture(
            sample_geotiff, temp_dir, output_name, target_size, linear=True
        )
        
        assert output_path is not None
        assert output_path.exists()
        
        # Load and check texture
        texture = imageio.imread(output_path)
        assert texture.shape[:2] == (target_size, target_size)
        assert texture.dtype == np.uint8
    
    def test_texture_value_range(self, temp_dir, sample_optical_geotiff):
        """Test that texture values are in valid range."""
        output_path = export_texture(
            sample_optical_geotiff, temp_dir, 'test.png', 256, linear=False
        )
        
        texture = imageio.imread(output_path)
        
        # Should be in [0, 255]
        assert np.min(texture) >= 0
        assert np.max(texture) <= 255


class TestMetadataGeneration:
    """Test metadata JSON generation."""
    
    def test_meta_json_creation(self, temp_dir, sample_geotiff):
        """Test that meta.json is created correctly."""
        from export_unreal import generate_meta_json
        
        output_dir = temp_dir / 'export'
        output_dir.mkdir()
        
        # Create mock import params
        import_params = {
            'landscape_size': '513x513',
            'z_scale_cm': 1.234,
            'x_scale_cm': 1000.0,
            'y_scale_cm': 1000.0,
            'pixel_size_m': 10.0
        }
        
        # Create mock args
        class MockArgs:
            tile_id = 'test_tile'
            target_size = 513
            s2_rgb = None
            anomaly = None
            meta = None
        
        # Mock profile, transform, crs
        import rasterio
        from rasterio.transform import from_origin
        from rasterio.crs import CRS
        
        with rasterio.open(sample_geotiff) as src:
            profile = src.profile
            transform = src.transform
            crs = src.crs
        
        meta = generate_meta_json(
            output_dir, import_params, profile, transform, crs, MockArgs()
        )
        
        # Check meta.json exists
        meta_path = output_dir / 'meta.json'
        assert meta_path.exists()
        
        # Load and validate
        with open(meta_path, 'r') as f:
            meta_data = json.load(f)
        
        assert 'tile_id' in meta_data
        assert 'unreal_import_parameters' in meta_data
        assert 'crs' in meta_data
        assert meta_data['tile_id'] == 'test_tile'


class TestEndToEndExport:
    """Test complete export workflow."""
    
    def test_complete_export_workflow(
        self, temp_dir, sample_geotiff, sample_optical_geotiff
    ):
        """Test complete export from DEM and textures to Unreal assets."""
        output_dir = temp_dir / 'unreal_export'
        output_dir.mkdir()
        
        # Export heightmap
        import_params, profile, transform, crs = export_heightmap(
            sample_geotiff, output_dir, 513, 2.0
        )
        
        # Export RGB texture
        export_texture(
            sample_optical_geotiff, output_dir, 'texture_rgb.png', 512, linear=False
        )
        
        # Check all files exist
        assert (output_dir / 'heightmap_16bit.png').exists()
        assert (output_dir / 'texture_rgb.png').exists()
        
        # Validate heightmap dimensions match target
        heightmap = imageio.imread(output_dir / 'heightmap_16bit.png')
        assert heightmap.shape == (513, 513)
        
        # Validate texture dimensions
        texture = imageio.imread(output_dir / 'texture_rgb.png')
        assert texture.shape[:2] == (512, 512)


class TestErrorHandling:
    """Test error handling in export functions."""
    
    def test_invalid_dem_path(self, temp_dir):
        """Test handling of invalid DEM path."""
        with pytest.raises(Exception):
            export_heightmap(
                Path('/nonexistent/dem.tif'), temp_dir, 513, 2.0
            )
    
    def test_invalid_texture_path(self, temp_dir):
        """Test handling of invalid texture path."""
        result = export_texture(
            Path('/nonexistent/texture.tif'), temp_dir, 'out.png', 512, linear=False
        )
        # Should handle gracefully (return None or raise exception)
        assert result is None or not Path(result).exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
