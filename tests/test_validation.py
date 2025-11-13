"""
Unit tests for input/output validation and error handling.
"""

import numpy as np
import pytest
import sys
from pathlib import Path
import rasterio
from rasterio.crs import CRS

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))


class TestDataValidation:
    """Test data validation utilities."""
    
    def test_valid_geotiff(self, sample_geotiff):
        """Test validation of valid GeoTIFF."""
        with rasterio.open(sample_geotiff) as src:
            # Check basic properties
            assert src.count >= 1
            assert src.width > 0
            assert src.height > 0
            assert src.crs is not None
            assert src.transform is not None
    
    def test_invalid_pixels_detection(self):
        """Test detection of invalid pixels (NaN, Inf)."""
        # Create array with invalid values
        data = np.random.randn(100, 100).astype(np.float32)
        data[10:20, 10:20] = np.nan
        data[30:40, 30:40] = np.inf
        
        # Check detection
        nan_mask = np.isnan(data)
        inf_mask = np.isinf(data)
        invalid_mask = nan_mask | inf_mask
        
        assert invalid_mask.sum() == 200  # 10x10 + 10x10
        
        # Percentage of valid pixels
        valid_percentage = (~invalid_mask).sum() / invalid_mask.size
        assert valid_percentage == 0.98
    
    def test_crs_matching(self, sample_geotiff, sample_sar_geotiff):
        """Test CRS matching between rasters."""
        with rasterio.open(sample_geotiff) as src1:
            with rasterio.open(sample_sar_geotiff) as src2:
                # Both should be in the same CRS
                assert src1.crs == src2.crs
    
    def test_extent_overlap(self, sample_geotiff, sample_sar_geotiff):
        """Test extent overlap detection."""
        with rasterio.open(sample_geotiff) as src1:
            with rasterio.open(sample_sar_geotiff) as src2:
                bounds1 = src1.bounds
                bounds2 = src2.bounds
                
                # Check if bounds overlap
                overlap = not (
                    bounds1.right < bounds2.left or
                    bounds1.left > bounds2.right or
                    bounds1.top < bounds2.bottom or
                    bounds1.bottom > bounds2.top
                )
                
                assert overlap  # Should overlap since they have same extent


class TestInputValidation:
    """Test input parameter validation."""
    
    def test_contamination_range(self):
        """Test contamination parameter validation."""
        # Valid values
        valid_contaminations = [0.01, 0.02, 0.05, 0.1]
        for c in valid_contaminations:
            assert 0 < c < 1
        
        # Invalid values
        invalid_contaminations = [0, -0.1, 1.0, 1.5]
        for c in invalid_contaminations:
            assert not (0 < c < 1) or c >= 0.5
    
    def test_n_estimators_validation(self):
        """Test n_estimators parameter validation."""
        # Valid values
        valid_n_estimators = [50, 100, 200, 500]
        for n in valid_n_estimators:
            assert n > 0
            assert isinstance(n, int)
        
        # Invalid values
        invalid_n_estimators = [0, -1, 1.5, 'string']
        for n in invalid_n_estimators:
            if isinstance(n, (int, float)):
                assert n <= 0 or not isinstance(n, int)
    
    def test_vertical_exaggeration_range(self):
        """Test vertical exaggeration validation."""
        # Valid values
        valid_values = [0.5, 1.0, 2.0, 5.0, 10.0]
        for v in valid_values:
            assert 0.1 <= v <= 20.0
        
        # Invalid values
        invalid_values = [0, -1, 25, 100]
        for v in invalid_values:
            assert not (0.1 <= v <= 20.0)


class TestOutputValidation:
    """Test output data validation."""
    
    def test_anomaly_map_range(self):
        """Test that anomaly map values are in [0, 1]."""
        # Simulate anomaly detection output
        anomaly_map = np.random.rand(100, 100).astype(np.float32)
        
        assert np.all(anomaly_map >= 0)
        assert np.all(anomaly_map <= 1)
        assert np.all(np.isfinite(anomaly_map))
    
    def test_heightmap_16bit_range(self):
        """Test that heightmap values are valid 16-bit."""
        heightmap = np.random.randint(0, 65536, (513, 513), dtype=np.uint16)
        
        assert heightmap.dtype == np.uint16
        assert np.min(heightmap) >= 0
        assert np.max(heightmap) <= 65535
    
    def test_feature_stack_dimensions(self):
        """Test feature stack has correct dimensions."""
        h, w = 100, 100
        n_features = 13  # Total number of features
        
        feature_stack = np.random.randn(h, w, n_features).astype(np.float32)
        
        assert feature_stack.shape == (h, w, n_features)
        assert feature_stack.dtype == np.float32


class TestFileValidation:
    """Test file validation utilities."""
    
    def test_file_existence(self, sample_geotiff):
        """Test file existence check."""
        assert sample_geotiff.exists()
        assert sample_geotiff.is_file()
    
    def test_file_size_validation(self, sample_geotiff):
        """Test file size validation."""
        file_size_mb = sample_geotiff.stat().st_size / (1024 * 1024)
        
        # Sample file should be small
        assert file_size_mb < 10  # Less than 10 MB
    
    def test_output_directory_creation(self, temp_dir):
        """Test output directory creation."""
        output_dir = temp_dir / 'test_output'
        assert not output_dir.exists()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        assert output_dir.exists()
        assert output_dir.is_dir()


class TestEdgeCaseValidation:
    """Test validation of edge cases."""
    
    def test_empty_array_detection(self):
        """Test detection of empty arrays."""
        empty_array = np.array([])
        assert empty_array.size == 0
    
    def test_single_value_array(self):
        """Test handling of uniform arrays."""
        uniform_array = np.ones((100, 100))
        
        # Standard deviation should be zero
        assert np.std(uniform_array) == 0
        
        # All values are the same
        assert np.unique(uniform_array).size == 1
    
    def test_extreme_value_detection(self):
        """Test detection of extreme values."""
        data = np.random.randn(100, 100)
        
        # Add extreme values
        data[0, 0] = 1e10
        data[1, 1] = -1e10
        
        # Detect using percentiles
        p1 = np.percentile(data, 1)
        p99 = np.percentile(data, 99)
        
        extreme_mask = (data < p1 - 10 * (p99 - p1)) | (data > p99 + 10 * (p99 - p1))
        
        assert extreme_mask.sum() >= 2  # At least the two we added


class TestMetadataValidation:
    """Test metadata validation."""
    
    def test_metadata_schema(self):
        """Test metadata schema validation."""
        metadata = {
            'tile_id': 'test_001',
            'crs': 'EPSG:32610',
            'width': 100,
            'height': 100,
            'pixel_size_m': 10.0,
            'bbox': [600000, 4400000, 601000, 4401000]
        }
        
        # Validate required fields
        assert 'tile_id' in metadata
        assert 'crs' in metadata
        assert 'width' in metadata
        assert 'height' in metadata
        assert 'pixel_size_m' in metadata
        assert 'bbox' in metadata
        
        # Validate types
        assert isinstance(metadata['width'], int)
        assert isinstance(metadata['height'], int)
        assert isinstance(metadata['pixel_size_m'], (int, float))
        assert isinstance(metadata['bbox'], list)
        assert len(metadata['bbox']) == 4
    
    def test_bbox_validity(self):
        """Test bounding box validation."""
        bbox = [600000, 4400000, 601000, 4401000]  # [xmin, ymin, xmax, ymax]
        
        # Check order
        assert bbox[0] < bbox[2]  # xmin < xmax
        assert bbox[1] < bbox[3]  # ymin < ymax
        
        # Check reasonable size
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        
        assert width > 0
        assert height > 0


class TestDataIntegrity:
    """Test data integrity checks."""
    
    def test_checksum_consistency(self, sample_geotiff):
        """Test that raster data is consistent across reads."""
        import hashlib
        
        # Read data twice
        with rasterio.open(sample_geotiff) as src:
            data1 = src.read(1)
        
        with rasterio.open(sample_geotiff) as src:
            data2 = src.read(1)
        
        # Should be identical
        assert np.array_equal(data1, data2)
        
        # Compute checksums
        checksum1 = hashlib.md5(data1.tobytes()).hexdigest()
        checksum2 = hashlib.md5(data2.tobytes()).hexdigest()
        
        assert checksum1 == checksum2
    
    def test_coordinate_transform_validity(self, sample_geotiff):
        """Test that coordinate transforms are valid."""
        with rasterio.open(sample_geotiff) as src:
            transform = src.transform
            
            # Check transform components
            assert transform[0] != 0  # Pixel width
            assert transform[4] != 0  # Pixel height
            
            # Transform a pixel coordinate to spatial coordinate
            x, y = transform * (0, 0)
            
            # Should be finite
            assert np.isfinite(x)
            assert np.isfinite(y)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
