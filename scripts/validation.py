#!/usr/bin/env python3
"""
Unreal Miner - Data Validation and Error Handling Utilities

This module provides comprehensive validation functions for input data,
parameters, and output quality assurance.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
import rasterio
from rasterio.crs import CRS

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """Validator for geospatial raster data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator with configuration.
        
        Args:
            config: Optional configuration dictionary with validation parameters
        """
        self.config = config or {}
        self.min_valid_pixels = self.config.get('min_valid_pixels', 0.5)
        self.max_input_size_mb = self.config.get('max_input_size', 5000)
        self.check_crs = self.config.get('check_crs_match', True)
        self.check_extent = self.config.get('check_extent_overlap', True)
    
    def validate_file_exists(self, file_path: Path) -> None:
        """
        Validate that a file exists and is readable.
        
        Args:
            file_path: Path to file
            
        Raises:
            ValidationError: If file doesn't exist or isn't readable
        """
        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        # Check file size
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_input_size_mb:
            logger.warning(
                f"File size ({size_mb:.2f} MB) exceeds recommended maximum "
                f"({self.max_input_size_mb} MB): {file_path}"
            )
        
        logger.debug(f"File validation passed: {file_path}")
    
    def validate_raster(self, raster_path: Path) -> Dict[str, Any]:
        """
        Validate raster file and return metadata.
        
        Args:
            raster_path: Path to raster file
            
        Returns:
            Dictionary with raster metadata
            
        Raises:
            ValidationError: If raster is invalid
        """
        self.validate_file_exists(raster_path)
        
        try:
            with rasterio.open(raster_path) as src:
                # Basic properties
                metadata = {
                    'path': str(raster_path),
                    'driver': src.driver,
                    'width': src.width,
                    'height': src.height,
                    'count': src.count,
                    'dtype': src.dtypes[0],
                    'crs': src.crs,
                    'transform': src.transform,
                    'bounds': src.bounds
                }
                
                # Validate dimensions
                if src.width <= 0 or src.height <= 0:
                    raise ValidationError(
                        f"Invalid raster dimensions: {src.width}x{src.height}"
                    )
                
                # Validate CRS
                if src.crs is None:
                    logger.warning(f"No CRS defined for: {raster_path}")
                
                # Check data validity
                sample_data = src.read(1)
                valid_percentage = self._check_data_validity(sample_data)
                metadata['valid_percentage'] = valid_percentage
                
                if valid_percentage < self.min_valid_pixels:
                    raise ValidationError(
                        f"Insufficient valid pixels ({valid_percentage:.1%}) "
                        f"in {raster_path}. Minimum required: {self.min_valid_pixels:.1%}"
                    )
                
                logger.info(
                    f"Raster validation passed: {raster_path} "
                    f"({src.width}x{src.height}, {src.count} bands, "
                    f"{valid_percentage:.1%} valid pixels)"
                )
                
                return metadata
                
        except rasterio.errors.RasterioError as e:
            raise ValidationError(f"Failed to read raster {raster_path}: {e}")
    
    def _check_data_validity(self, data: np.ndarray) -> float:
        """
        Check percentage of valid (non-NaN, non-Inf) pixels.
        
        Args:
            data: Numpy array
            
        Returns:
            Percentage of valid pixels (0.0 to 1.0)
        """
        valid_mask = np.isfinite(data)
        return valid_mask.sum() / valid_mask.size
    
    def validate_crs_match(
        self, raster1_path: Path, raster2_path: Path
    ) -> Tuple[CRS, CRS]:
        """
        Validate that two rasters have matching CRS.
        
        Args:
            raster1_path: Path to first raster
            raster2_path: Path to second raster
            
        Returns:
            Tuple of (crs1, crs2)
            
        Raises:
            ValidationError: If CRS don't match
        """
        with rasterio.open(raster1_path) as src1:
            crs1 = src1.crs
        
        with rasterio.open(raster2_path) as src2:
            crs2 = src2.crs
        
        if self.check_crs and crs1 != crs2:
            raise ValidationError(
                f"CRS mismatch: {raster1_path} ({crs1}) vs "
                f"{raster2_path} ({crs2})"
            )
        
        logger.debug(f"CRS match validated: {crs1}")
        return crs1, crs2
    
    def validate_extent_overlap(
        self, raster1_path: Path, raster2_path: Path
    ) -> bool:
        """
        Validate that two rasters have overlapping extents.
        
        Args:
            raster1_path: Path to first raster
            raster2_path: Path to second raster
            
        Returns:
            True if extents overlap
            
        Raises:
            ValidationError: If no overlap
        """
        with rasterio.open(raster1_path) as src1:
            bounds1 = src1.bounds
        
        with rasterio.open(raster2_path) as src2:
            bounds2 = src2.bounds
        
        # Check overlap
        overlap = not (
            bounds1.right < bounds2.left or
            bounds1.left > bounds2.right or
            bounds1.top < bounds2.bottom or
            bounds1.bottom > bounds2.top
        )
        
        if self.check_extent and not overlap:
            raise ValidationError(
                f"No extent overlap between {raster1_path} and {raster2_path}"
            )
        
        logger.debug(f"Extent overlap validated")
        return overlap
    
    def validate_array(
        self, array: np.ndarray, name: str, 
        expected_shape: Optional[Tuple] = None,
        value_range: Optional[Tuple[float, float]] = None
    ) -> None:
        """
        Validate numpy array properties.
        
        Args:
            array: Numpy array to validate
            name: Name for logging
            expected_shape: Expected shape (optional)
            value_range: Expected (min, max) value range (optional)
            
        Raises:
            ValidationError: If validation fails
        """
        if array is None:
            raise ValidationError(f"{name} is None")
        
        if array.size == 0:
            raise ValidationError(f"{name} is empty")
        
        # Check shape
        if expected_shape is not None and array.shape != expected_shape:
            raise ValidationError(
                f"{name} shape mismatch: expected {expected_shape}, "
                f"got {array.shape}"
            )
        
        # Check for invalid values
        valid_percentage = self._check_data_validity(array)
        if valid_percentage < self.min_valid_pixels:
            raise ValidationError(
                f"{name} has {valid_percentage:.1%} valid pixels "
                f"(minimum: {self.min_valid_pixels:.1%})"
            )
        
        # Check value range
        if value_range is not None:
            valid_data = array[np.isfinite(array)]
            if valid_data.size > 0:
                data_min = np.min(valid_data)
                data_max = np.max(valid_data)
                
                expected_min, expected_max = value_range
                if data_min < expected_min or data_max > expected_max:
                    logger.warning(
                        f"{name} values [{data_min:.2f}, {data_max:.2f}] "
                        f"outside expected range [{expected_min}, {expected_max}]"
                    )
        
        logger.debug(
            f"Array validation passed: {name} "
            f"(shape={array.shape}, valid={valid_percentage:.1%})"
        )


class ParameterValidator:
    """Validator for processing parameters."""
    
    @staticmethod
    def validate_contamination(contamination: float) -> None:
        """
        Validate anomaly detection contamination parameter.
        
        Args:
            contamination: Contamination value
            
        Raises:
            ValidationError: If invalid
        """
        if not (0 < contamination < 0.5):
            raise ValidationError(
                f"Contamination must be in (0, 0.5), got {contamination}"
            )
        
        if contamination > 0.1:
            logger.warning(
                f"High contamination value ({contamination}). "
                f"Typical range is 0.01-0.05"
            )
    
    @staticmethod
    def validate_n_estimators(n_estimators: int) -> None:
        """
        Validate n_estimators parameter.
        
        Args:
            n_estimators: Number of trees
            
        Raises:
            ValidationError: If invalid
        """
        if not isinstance(n_estimators, int):
            raise ValidationError(
                f"n_estimators must be int, got {type(n_estimators)}"
            )
        
        if n_estimators < 10:
            raise ValidationError(
                f"n_estimators too small ({n_estimators}). Minimum: 10"
            )
        
        if n_estimators > 1000:
            logger.warning(
                f"High n_estimators ({n_estimators}) may be slow. "
                f"Typical range: 50-500"
            )
    
    @staticmethod
    def validate_vertical_exaggeration(vertical_exaggeration: float) -> None:
        """
        Validate vertical exaggeration parameter.
        
        Args:
            vertical_exaggeration: Exaggeration factor
            
        Raises:
            ValidationError: If invalid
        """
        if not (0.1 <= vertical_exaggeration <= 20.0):
            raise ValidationError(
                f"Vertical exaggeration must be in [0.1, 20.0], "
                f"got {vertical_exaggeration}"
            )
        
        if vertical_exaggeration > 10.0:
            logger.warning(
                f"High vertical exaggeration ({vertical_exaggeration}). "
                f"Typical range: 1.0-5.0"
            )
    
    @staticmethod
    def validate_target_size(target_size: int, valid_sizes: list) -> None:
        """
        Validate Unreal landscape target size.
        
        Args:
            target_size: Target size
            valid_sizes: List of valid sizes
            
        Raises:
            ValidationError: If invalid
        """
        if target_size not in valid_sizes:
            raise ValidationError(
                f"Target size {target_size} not valid. "
                f"Valid sizes: {valid_sizes}"
            )


def validate_processing_inputs(
    s1_path: Path, s2_path: Path, dem_path: Path, config: Dict
) -> Dict[str, Any]:
    """
    Validate all processing inputs before starting pipeline.
    
    Args:
        s1_path: Path to Sentinel-1 data
        s2_path: Path to Sentinel-2 data
        dem_path: Path to DEM
        config: Configuration dictionary
        
    Returns:
        Dictionary with validation results
        
    Raises:
        ValidationError: If validation fails
    """
    logger.info("Validating processing inputs...")
    
    validator = DataValidator(config.get('validation', {}))
    param_validator = ParameterValidator()
    
    results = {}
    
    # Validate files exist
    validator.validate_file_exists(s1_path)
    validator.validate_file_exists(s2_path)
    validator.validate_file_exists(dem_path)
    
    # Validate rasters
    results['s1'] = validator.validate_raster(s1_path)
    results['s2'] = validator.validate_raster(s2_path)
    results['dem'] = validator.validate_raster(dem_path)
    
    # Validate CRS match
    validator.validate_crs_match(s1_path, s2_path)
    validator.validate_crs_match(s1_path, dem_path)
    
    # Validate extent overlap
    validator.validate_extent_overlap(s1_path, s2_path)
    validator.validate_extent_overlap(s1_path, dem_path)
    
    # Validate parameters
    processing_config = config.get('processing', {})
    param_validator.validate_contamination(
        processing_config.get('contamination', 0.02)
    )
    param_validator.validate_n_estimators(
        processing_config.get('n_estimators', 200)
    )
    
    logger.info("All input validation passed ✓")
    return results


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    print("Data validation utilities loaded")
