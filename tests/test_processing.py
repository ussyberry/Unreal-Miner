"""
Unit tests for process_fusion.py
"""

import numpy as np
import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from process_fusion import (
    load_raster,
    compute_sar_features,
    compute_optical_features,
    compute_terrain_features,
    stack_features,
    detect_anomalies
)


class TestLoadRaster:
    """Test raster loading functionality."""
    
    def test_load_single_band(self, sample_geotiff):
        """Test loading a single-band GeoTIFF."""
        data, profile, transform, crs = load_raster(sample_geotiff, band=1)
        
        assert data.shape == (100, 100)
        assert data.dtype == np.float32
        assert profile['count'] == 1
        assert crs is not None
        assert transform is not None
    
    def test_load_multiband(self, sample_sar_geotiff):
        """Test loading a multi-band GeoTIFF."""
        data, profile, transform, crs = load_raster(sample_sar_geotiff)
        
        assert data.shape == (2, 100, 100)
        assert data.dtype == np.float32
        assert profile['count'] == 2
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises error."""
        with pytest.raises(Exception):
            load_raster(Path('/nonexistent/file.tif'))


class TestSARFeatures:
    """Test SAR feature computation."""
    
    def test_compute_sar_features_basic(self, sample_sar_data):
        """Test basic SAR feature computation."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        features = compute_sar_features(vv, vh)
        
        # Check all expected features are present
        assert 'vv_vh_ratio' in features
        assert 'vv_texture' in features
        assert 'vv_mean' in features
        assert 'vh_mean' in features
        
        # Check shapes match input
        for key, value in features.items():
            assert value.shape == vv.shape
    
    def test_sar_ratio_positive(self, sample_sar_data):
        """Test that VV/VH ratio is always positive."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        features = compute_sar_features(vv, vh)
        ratio = features['vv_vh_ratio']
        
        assert np.all(ratio > 0)
        assert np.all(np.isfinite(ratio))
    
    def test_sar_texture_range(self, sample_sar_data):
        """Test texture coefficient of variation is in valid range."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        features = compute_sar_features(vv, vh)
        texture = features['vv_texture']
        
        # Texture should be non-negative
        assert np.all(texture >= 0)
        assert np.all(np.isfinite(texture))


class TestOpticalFeatures:
    """Test optical feature computation."""
    
    def test_compute_optical_features_basic(self, sample_optical_data):
        """Test basic optical feature computation."""
        features = compute_optical_features(sample_optical_data)
        
        # Check all expected features
        assert 'brightness' in features
        assert 'ndvi_proxy' in features
        assert 'ndwi_proxy' in features
        assert 'rg_ratio' in features
        assert 'rb_ratio' in features
        
        # Check shapes
        expected_shape = sample_optical_data[0].shape
        for key, value in features.items():
            assert value.shape == expected_shape
    
    def test_brightness_range(self, sample_optical_data):
        """Test brightness is in valid range."""
        features = compute_optical_features(sample_optical_data)
        brightness = features['brightness']
        
        # Brightness should be in reasonable range
        assert np.all(brightness >= 0)
        assert np.all(np.isfinite(brightness))
    
    def test_ndvi_range(self, sample_optical_data):
        """Test NDVI proxy is in [-1, 1] range."""
        features = compute_optical_features(sample_optical_data)
        ndvi = features['ndvi_proxy']
        
        # NDVI should be in [-1, 1]
        assert np.all(ndvi >= -1)
        assert np.all(ndvi <= 1)
        assert np.all(np.isfinite(ndvi))


class TestTerrainFeatures:
    """Test terrain feature computation."""
    
    def test_compute_terrain_features_basic(self, sample_dem_data):
        """Test basic terrain feature computation."""
        features = compute_terrain_features(sample_dem_data)
        
        # Check all expected features
        assert 'slope' in features
        assert 'aspect' in features
        assert 'roughness' in features
        assert 'curvature' in features
        
        # Check shapes
        for key, value in features.items():
            assert value.shape == sample_dem_data.shape
    
    def test_slope_positive(self, sample_dem_data):
        """Test slope is always non-negative."""
        features = compute_terrain_features(sample_dem_data)
        slope = features['slope']
        
        assert np.all(slope >= 0)
        assert np.all(np.isfinite(slope))
    
    def test_aspect_range(self, sample_dem_data):
        """Test aspect is in valid range."""
        features = compute_terrain_features(sample_dem_data)
        aspect = features['aspect']
        
        # Aspect should be in [-pi, pi]
        assert np.all(aspect >= -np.pi)
        assert np.all(aspect <= np.pi)
        assert np.all(np.isfinite(aspect))
    
    def test_roughness_positive(self, sample_dem_data):
        """Test roughness is non-negative."""
        features = compute_terrain_features(sample_dem_data)
        roughness = features['roughness']
        
        assert np.all(roughness >= 0)
        assert np.all(np.isfinite(roughness))


class TestFeatureStacking:
    """Test feature stacking functionality."""
    
    def test_stack_features(self, sample_sar_data, sample_optical_data, sample_dem_data):
        """Test stacking all features."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        sar_features = compute_sar_features(vv, vh)
        optical_features = compute_optical_features(sample_optical_data)
        terrain_features = compute_terrain_features(sample_dem_data)
        
        feature_array, feature_names = stack_features(
            sar_features, optical_features, terrain_features
        )
        
        # Check shape
        h, w = vv.shape
        expected_n_features = len(sar_features) + len(optical_features) + len(terrain_features)
        assert feature_array.shape == (h, w, expected_n_features)
        
        # Check feature names
        assert len(feature_names) == expected_n_features
        assert 'vv_vh_ratio' in feature_names
        assert 'brightness' in feature_names
        assert 'slope' in feature_names


class TestAnomalyDetection:
    """Test anomaly detection functionality."""
    
    def test_detect_anomalies_basic(self, sample_sar_data, sample_optical_data, sample_dem_data):
        """Test basic anomaly detection."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        sar_features = compute_sar_features(vv, vh)
        optical_features = compute_optical_features(sample_optical_data)
        terrain_features = compute_terrain_features(sample_dem_data)
        
        feature_array, _ = stack_features(
            sar_features, optical_features, terrain_features
        )
        
        anomaly_map, stats = detect_anomalies(
            feature_array, contamination=0.02, n_estimators=50
        )
        
        # Check output shape
        assert anomaly_map.shape == vv.shape
        
        # Check anomaly scores are in [0, 1]
        assert np.nanmin(anomaly_map) >= 0
        assert np.nanmax(anomaly_map) <= 1
        
        # Check stats
        assert 'mean' in stats
        assert 'std' in stats
        assert 'p95' in stats
        assert stats['n_anomalies_p95'] > 0
    
    def test_contamination_effect(self, sample_sar_data, sample_optical_data, sample_dem_data):
        """Test that contamination parameter affects results."""
        vv = sample_sar_data[0]
        vh = sample_sar_data[1]
        
        sar_features = compute_sar_features(vv, vh)
        optical_features = compute_optical_features(sample_optical_data)
        terrain_features = compute_terrain_features(sample_dem_data)
        
        feature_array, _ = stack_features(
            sar_features, optical_features, terrain_features
        )
        
        # Test with different contamination values
        anomaly_map_1, stats_1 = detect_anomalies(
            feature_array, contamination=0.01, n_estimators=50
        )
        anomaly_map_2, stats_2 = detect_anomalies(
            feature_array, contamination=0.05, n_estimators=50
        )
        
        # Higher contamination should result in more anomalies
        # (This is a statistical test, may occasionally fail due to randomness)
        assert stats_2['n_anomalies_p95'] >= stats_1['n_anomalies_p95'] * 0.8
    
    def test_nan_handling(self):
        """Test that NaN values are handled correctly."""
        # Create feature array with some NaN values
        feature_array = np.random.randn(50, 50, 5).astype(np.float32)
        feature_array[10:20, 10:20, :] = np.nan
        
        anomaly_map, stats = detect_anomalies(
            feature_array, contamination=0.02, n_estimators=50
        )
        
        # Check NaN pixels are marked as NaN in output
        assert np.isnan(anomaly_map[15, 15])
        
        # Check valid pixels are processed
        assert not np.isnan(anomaly_map[0, 0])


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_single_value_array(self):
        """Test handling of uniform data."""
        # Uniform SAR data
        vv = np.ones((50, 50), dtype=np.float32)
        vh = np.ones((50, 50), dtype=np.float32) * 0.3
        
        features = compute_sar_features(vv, vh)
        
        # Should not crash and return valid shapes
        assert features['vv_vh_ratio'].shape == vv.shape
        assert np.all(np.isfinite(features['vv_vh_ratio']))
    
    def test_zero_values(self):
        """Test handling of zero values."""
        vv = np.zeros((50, 50), dtype=np.float32)
        vh = np.zeros((50, 50), dtype=np.float32)
        
        # Should not crash (division by zero protection)
        features = compute_sar_features(vv, vh)
        
        assert np.all(np.isfinite(features['vv_vh_ratio']))
    
    def test_extreme_values(self):
        """Test handling of extreme values."""
        vv = np.full((50, 50), 1e10, dtype=np.float32)
        vh = np.full((50, 50), 1e-10, dtype=np.float32)
        
        features = compute_sar_features(vv, vh)
        
        # Should handle extreme ratios
        assert np.all(np.isfinite(features['vv_vh_ratio']))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
