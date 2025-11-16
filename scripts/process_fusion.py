#!/usr/bin/env python3
"""
Unreal Miner - Feature Extraction and Anomaly Detection

This script processes aligned Sentinel-1 (SAR) and Sentinel-2 (optical) rasters,
computes geophysical features, and applies machine learning for mineral anomaly detection.

Usage:
    python process_fusion.py \\
        --s1-path ../data/aligned/s1_backscatter_10m_utm.tif \\
        --s2-path ../data/aligned/s2_rgb_10m_utm.tif \\
        --dem-path ../data/aligned/dem_10m_utm.tif \\
        --output-dir ../data/outputs/ \\
        --contamination 0.02
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS
from scipy.ndimage import generic_filter
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_raster(path, band=None):
    """Load raster data and return array with profile."""
    logger.info(f"Loading raster: {path}")
    with rasterio.open(path) as src:
        if band:
            data = src.read(band).astype(np.float32)
        else:
            data = src.read().astype(np.float32)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
    return data, profile, transform, crs


def compute_sar_features(vv, vh):
    """Compute SAR-derived features from VV and VH polarizations."""
    logger.info("Computing SAR features...")
    
    eps = 1e-9  # Avoid division by zero
    
    # VV/VH ratio (cross-polarization ratio)
    ratio = vv / (vh + eps)
    
    # Local texture (coefficient of variation)
    def cv_filter(window):
        mean = np.mean(window)
        std = np.std(window)
        return std / (mean + eps) if mean > eps else 0
    
    vv_texture = generic_filter(vv, cv_filter, size=5)
    
    # Local mean backscatter
    vv_mean = generic_filter(vv, np.mean, size=5)
    vh_mean = generic_filter(vh, np.mean, size=5)
    
    features = {
        'vv_vh_ratio': ratio,
        'vv_texture': vv_texture,
        'vv_mean': vv_mean,
        'vh_mean': vh_mean
    }
    
    logger.info("SAR features computed successfully")
    return features


def compute_optical_features(rgb):
    """Compute optical features from RGB bands."""
    logger.info("Computing optical features...")
    
    r, g, b = rgb[0], rgb[1], rgb[2]
    eps = 1e-9
    
    # Brightness
    brightness = (r + g + b) / 3.0
    
    # Normalized Difference Vegetation Index (approximation using Red/Green)
    # True NDVI requires NIR band (B8), using Green as proxy
    ndvi_proxy = (g - r) / (g + r + eps)
    
    # Normalized Difference Water Index (approximation)
    ndwi_proxy = (g - b) / (g + b + eps)
    
    # RGB ratios
    rg_ratio = r / (g + eps)
    rb_ratio = r / (b + eps)
    
    features = {
        'brightness': brightness,
        'ndvi_proxy': ndvi_proxy,
        'ndwi_proxy': ndwi_proxy,
        'rg_ratio': rg_ratio,
        'rb_ratio': rb_ratio
    }
    
    logger.info("Optical features computed successfully")
    return features


def compute_terrain_features(dem):
    """Compute terrain-derived features from DEM."""
    logger.info("Computing terrain features...")
    
    # Gradient (slope components)
    gy, gx = np.gradient(dem)
    slope = np.sqrt(gx**2 + gy**2)
    
    # Aspect
    aspect = np.arctan2(gy, gx)
    
    # Roughness (local standard deviation)
    roughness = generic_filter(dem, np.std, size=5)
    
    # Curvature (second derivative)
    gyy, gyx = np.gradient(gy)
    gxy, gxx = np.gradient(gx)
    curvature = gxx + gyy
    
    features = {
        'slope': slope,
        'aspect': aspect,
        'roughness': roughness,
        'curvature': curvature
    }
    
    logger.info("Terrain features computed successfully")
    return features


def compute_emit_features(emit_data):
    """Placeholder for computing spectral indices from EMIT data."""
    logger.info("Computing EMIT features (placeholder)...")
    # This is a placeholder. In a real implementation, you would calculate
    # spectral indices for iron, clay, carbonates, etc. here.
    # For now, we'll just return a dummy feature.
    dummy_feature = emit_data[:, :, 0] * 0.1
    features = {
        'dummy_emit_feature': dummy_feature
    }
    return features


def stack_features(sar_features, optical_features, terrain_features, emit_features):
    """Stack all features into a single array for ML processing."""
    logger.info("Stacking features...")
    
    all_features = {}
    all_features.update(sar_features)
    all_features.update(optical_features)
    all_features.update(terrain_features)
    all_features.update(emit_features)
    
    # Get shape from first feature
    first_key = list(all_features.keys())[0]
    h, w = all_features[first_key].shape
    
    # Stack features
    feature_names = list(all_features.keys())
    n_features = len(feature_names)
    
    feature_array = np.zeros((h, w, n_features), dtype=np.float32)
    for i, key in enumerate(feature_names):
        feature_array[:, :, i] = all_features[key]
    
    logger.info(f"Stacked {n_features} features: {feature_names}")
    return feature_array, feature_names


def classify_minerals(feature_array, n_estimators=200):
    """Apply RandomForest for mineral classification."""
    logger.info("Running mineral classification...")
    
    h, w, n_features = feature_array.shape
    
    # Reshape to 2D array (n_samples, n_features)
    features_2d = feature_array.reshape(-1, n_features)
    
    # Create mask for valid pixels (no NaN/Inf)
    valid_mask = ~np.isnan(features_2d).any(axis=1) & ~np.isinf(features_2d).any(axis=1)
    
    logger.info(f"Valid pixels: {valid_mask.sum()} / {len(valid_mask)}")
    
    # Standardize features (zero mean, unit variance)
    scaler = StandardScaler()
    features_scaled = features_2d.copy()
    features_scaled[valid_mask] = scaler.fit_transform(features_2d[valid_mask])
    
    # Placeholder for training data
    # In a real scenario, you would load your labeled training data here.
    # For now, we'll generate some dummy training data.
    n_train_samples = 1000
    X_train = np.random.rand(n_train_samples, n_features)
    y_train = np.random.randint(0, 3, n_train_samples) # 3 mineral classes

    # Fit RandomForestClassifier
    logger.info("Training RandomForestClassifier model...")
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=42,
        n_jobs=-1,  # Use all CPU cores
        verbose=1
    )
    
    clf.fit(X_train, y_train)
    
    # Predict mineral classes
    logger.info("Predicting mineral classes...")
    predictions = np.full(features_2d.shape[0], np.nan, dtype=np.float32)
    predictions[valid_mask] = clf.predict(features_scaled[valid_mask])
    
    # Reshape to image
    classification_map = predictions.reshape(h, w)
    
    # Statistics
    stats = {
        'mean': float(np.nanmean(classification_map)),
        'std': float(np.nanstd(classification_map)),
        'min': float(np.nanmin(classification_map)),
        'max': float(np.nanmax(classification_map)),
    }
    
    logger.info(f"Mineral classification complete. Stats: {stats}")
    return classification_map, stats


def save_geotiff(data, output_path, profile):
    """Save array as GeoTIFF."""
    logger.info(f"Saving GeoTIFF: {output_path}")
    
    profile.update(
        dtype=rasterio.float32,
        count=1,
        compress='lzw'
    )
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)
    
    logger.info(f"Saved: {output_path}")


def save_metadata(output_dir, profile, transform, crs, stats, feature_names, args):
    """Save processing metadata to JSON."""
    meta_path = output_dir / 'meta.json'
    logger.info(f"Saving metadata: {meta_path}")
    
    meta = {
        'tile_id': args.tile_id,
        'processing_date': datetime.utcnow().isoformat() + 'Z',
        'crs': crs.to_string() if crs else None,
        'transform': list(transform)[:6] if transform else None,
        'width': profile['width'],
        'height': profile['height'],
        'pixel_size_m': abs(transform[0]) if transform else None,
        'bbox': [
            transform[2],  # xmin
            transform[5] + transform[4] * profile['height'],  # ymin
            transform[2] + transform[0] * profile['width'],  # xmax
            transform[5]  # ymax
        ] if transform else None,
        'features_used': feature_names,
        'anomaly_stats': stats,
        'parameters': {
            'contamination': args.contamination,
            'n_estimators': args.n_estimators,
            's1_path': str(args.s1_path),
            's2_path': str(args.s2_path),
            'dem_path': str(args.dem_path)
        }
    }
    
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    logger.info(f"Metadata saved: {meta_path}")
    return meta


def main():
    parser = argparse.ArgumentParser(
        description='Unreal Miner: Feature extraction and anomaly detection'
    )
    parser.add_argument('--s1-path', required=True, type=Path,
                        help='Path to Sentinel-1 backscatter GeoTIFF (VV, VH bands)')
    parser.add_argument('--s2-path', required=True, type=Path,
                        help='Path to Sentinel-2 RGB GeoTIFF')
    parser.add_argument('--dem-path', required=True, type=Path,
                        help='Path to DEM GeoTIFF')
    parser.add_argument('--emit-path', type=Path,
                        help='Path to EMIT GeoTIFF (optional)')
    parser.add_argument('--output-dir', required=True, type=Path,
                        help='Output directory for results')
    parser.add_argument('--tile-id', default='tile_001',
                        help='Tile identifier')
    parser.add_argument('--n-estimators', type=int, default=200,
                        help='Number of RandomForest trees')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.s1_path.exists():
        logger.error(f"S1 path not found: {args.s1_path}")
        sys.exit(1)
    if not args.s2_path.exists():
        logger.error(f"S2 path not found: {args.s2_path}")
        sys.exit(1)
    if not args.dem_path.exists():
        logger.error(f"DEM path not found: {args.dem_path}")
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("UNREAL MINER - Processing Pipeline")
    logger.info("=" * 60)
    
    # Load rasters
    s1_data, s1_profile, s1_transform, s1_crs = load_raster(args.s1_path)
    s2_data, s2_profile, s2_transform, s2_crs = load_raster(args.s2_path)
    dem_data, dem_profile, dem_transform, dem_crs = load_raster(args.dem_path, band=1)
    
    # Load EMIT data if provided
    if args.emit_path and args.emit_path.exists():
        emit_data, _, _, _ = load_raster(args.emit_path)
        emit_features = compute_emit_features(emit_data)
    else:
        logger.warning("No EMIT data provided. Skipping EMIT features.")
        emit_features = {}

    # Extract VV and VH from S1 (assume bands 1 and 2)
    vv = s1_data[0] if s1_data.ndim == 3 else s1_data
    vh = s1_data[1] if s1_data.ndim == 3 and s1_data.shape[0] > 1 else vv * 0.5  # Fallback
    
    # Extract RGB from S2
    rgb = s2_data
    
    # Compute features
    sar_features = compute_sar_features(vv, vh)
    optical_features = compute_optical_features(rgb)
    terrain_features = compute_terrain_features(dem_data)
    
    # Stack features
    feature_array, feature_names = stack_features(
        sar_features, optical_features, terrain_features, emit_features
    )
    
    # Classify minerals
    classification_map, stats = classify_minerals(
        feature_array,
        n_estimators=args.n_estimators
    )
    
    # Save outputs
    output_path = args.output_dir / 'classification_map.tif'
    save_geotiff(classification_map, output_path, s1_profile)
    
    # Save feature stack (optional, for debugging)
    feature_stack_path = args.output_dir / 'feature_stack.tif'
    feature_profile = s1_profile.copy()
    feature_profile.update(count=len(feature_names))
    with rasterio.open(feature_stack_path, 'w', **feature_profile) as dst:
        for i in range(len(feature_names)):
            dst.write(feature_array[:, :, i], i + 1)
        dst.descriptions = feature_names
    logger.info(f"Saved feature stack: {feature_stack_path}")
    
    # Save metadata
    save_metadata(args.output_dir, s1_profile, s1_transform, s1_crs, stats, feature_names, args)
    
    logger.info("=" * 60)
    logger.info("Processing complete!")
    logger.info(f"Anomaly map: {output_path}")
    logger.info(f"Feature stack: {feature_stack_path}")
    logger.info(f"Metadata: {args.output_dir / 'meta.json'}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
