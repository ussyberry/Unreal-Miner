#!/usr/bin/env python3
"""
Unreal Miner - Export Utility for Unreal Engine

Converts GeoTIFF rasters to Unreal-compatible formats:
- 16-bit PNG heightmaps (power-of-2 + 1 sizing)
- Texture assets (RGB, anomaly overlays)
- meta.json with import parameters

Usage:
    python export_unreal.py \\
        --dem ../data/aligned/dem_10m_utm.tif \\
        --meta ../data/outputs/meta.json \\
        --output-dir ../data/unreal_export/ \\
        --target-size 4097 \\
        --vertical-exaggeration 2.0
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
import imageio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Unreal Landscape valid sizes (power-of-2 + 1)
UNREAL_SIZES = [127, 255, 511, 513, 1025, 2049, 4097, 8193]


def validate_unreal_size(size):
    """Validate if size is compatible with Unreal Landscape."""
    if size in UNREAL_SIZES:
        return True, size
    
    # Find nearest valid size
    nearest = min(UNREAL_SIZES, key=lambda x: abs(x - size))
    return False, nearest


def resample_dem(dem_data, target_size):
    """Resample DEM to target size using cubic interpolation."""
    logger.info(f"Resampling DEM from {dem_data.shape} to ({target_size}, {target_size})...")
    
    from scipy.ndimage import zoom
    
    h, w = dem_data.shape
    zoom_h = target_size / h
    zoom_w = target_size / w
    
    resampled = zoom(dem_data, (zoom_h, zoom_w), order=3)  # Cubic interpolation
    
    logger.info(f"Resampled to {resampled.shape}")
    return resampled


def export_heightmap(dem_path, output_dir, target_size, vertical_exaggeration):
    """Export DEM as 16-bit PNG heightmap for Unreal."""
    logger.info(f"Exporting heightmap from: {dem_path}")
    
    # Load DEM
    with rasterio.open(dem_path) as src:
        dem_data = src.read(1).astype(np.float32)
        profile = src.profile
        transform = src.transform
        crs = src.crs
    
    # Get elevation stats
    valid_mask = ~np.isnan(dem_data) & ~np.isinf(dem_data)
    min_elev = np.min(dem_data[valid_mask])
    max_elev = np.max(dem_data[valid_mask])
    elev_range = max_elev - min_elev
    
    logger.info(f"Elevation range: {min_elev:.2f} to {max_elev:.2f} m ({elev_range:.2f} m)")
    
    # Resample if needed
    h, w = dem_data.shape
    if h != target_size or w != target_size:
        dem_data = resample_dem(dem_data, target_size)
    
    # Normalize to 0-65535 (16-bit unsigned integer)
    dem_normalized = (dem_data - min_elev) / (elev_range + 1e-9)
    heightmap_16bit = (dem_normalized * 65535).astype(np.uint16)
    
    # Handle NaN/invalid values
    heightmap_16bit[~np.isfinite(dem_normalized)] = 0
    
    # Save as PNG
    output_path = output_dir / 'heightmap_16bit.png'
    imageio.imwrite(output_path, heightmap_16bit)
    logger.info(f"Saved heightmap: {output_path}")
    
    # Calculate Unreal import parameters
    pixel_size_m = abs(transform[0])
    
    # Z Scale calculation
    z_scale_cm = ((elev_range) / 65535) * 100 * vertical_exaggeration
    
    # X/Y Scale (meters to centimeters)
    xy_scale_cm = pixel_size_m * 100
    
    import_params = {
        'landscape_size': f"{target_size}x{target_size}",
        'section_size': '127x127',  # Recommended
        'sections_per_component': 1,
        'x_scale_cm': xy_scale_cm,
        'y_scale_cm': xy_scale_cm,
        'z_scale_cm': z_scale_cm,
        'min_elevation_m': float(min_elev),
        'max_elevation_m': float(max_elev),
        'elevation_range_m': float(elev_range),
        'vertical_exaggeration': vertical_exaggeration,
        'pixel_size_m': pixel_size_m
    }
    
    logger.info(f"Unreal Import Parameters:")
    logger.info(f"  X Scale: {xy_scale_cm:.2f} cm")
    logger.info(f"  Y Scale: {xy_scale_cm:.2f} cm")
    logger.info(f"  Z Scale: {z_scale_cm:.4f} cm")
    
    return import_params, profile, transform, crs


def export_texture(texture_path, output_dir, output_name, target_size, linear=False):
    """Export texture as PNG (RGB or grayscale)."""
    logger.info(f"Exporting texture: {texture_path} -> {output_name}")
    
    with rasterio.open(texture_path) as src:
        data = src.read()
    
    # Handle different band counts
    if data.shape[0] == 1:  # Grayscale
        img = data[0]
    elif data.shape[0] >= 3:  # RGB
        img = np.transpose(data[:3], (1, 2, 0))
    else:
        logger.error(f"Unexpected band count: {data.shape[0]}")
        return None
    
    # Resample if needed
    h, w = img.shape[:2]
    if h != target_size or w != target_size:
        from scipy.ndimage import zoom
        if img.ndim == 3:
            zoom_factors = (target_size / h, target_size / w, 1)
        else:
            zoom_factors = (target_size / h, target_size / w)
        img = zoom(img, zoom_factors, order=1)  # Bilinear
    
    # Normalize to 0-255
    if linear:
        # For anomaly overlays (preserve original values)
        img = np.clip(img * 255, 0, 255).astype(np.uint8)
    else:
        # For RGB textures
        img = np.clip(img, 0, 255).astype(np.uint8)
    
    # Save
    output_path = output_dir / output_name
    imageio.imwrite(output_path, img)
    logger.info(f"Saved texture: {output_path}")
    
    return output_path


def generate_meta_json(output_dir, import_params, profile, transform, crs, args):
    """Generate meta.json with all import parameters."""
    meta_path = output_dir / 'meta.json'
    logger.info(f"Generating metadata: {meta_path}")
    
    bbox = None
    if transform:
        bbox = [
            transform[2],  # xmin
            transform[5] + transform[4] * profile['height'],  # ymin
            transform[2] + transform[0] * profile['width'],  # xmax
            transform[5]  # ymax
        ]
    
    meta = {
        'tile_id': args.tile_id,
        'crs': crs.to_string() if crs else None,
        'bbox': bbox,
        'pixel_size_m': import_params['pixel_size_m'],
        'width': args.target_size,
        'height': args.target_size,
        'unreal_import_parameters': import_params,
        'export_date': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'textures': {
            'heightmap': 'heightmap_16bit.png',
            'base_rgb': args.s2_rgb.name if args.s2_rgb else None,
            'anomaly_overlay': args.anomaly.name if args.anomaly else None
        }
    }
    
    # Merge with existing meta.json if available
    if args.meta and args.meta.exists():
        with open(args.meta, 'r') as f:
            existing_meta = json.load(f)
            meta.update(existing_meta)
            # Keep unreal_import_parameters from new export
            meta['unreal_import_parameters'] = import_params
    
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    
    logger.info(f"Metadata saved: {meta_path}")
    return meta


def main():
    parser = argparse.ArgumentParser(
        description='Unreal Miner: Export utility for Unreal Engine'
    )
    parser.add_argument('--dem', required=True, type=Path,
                        help='Path to DEM GeoTIFF')
    parser.add_argument('--meta', type=Path,
                        help='Path to existing meta.json (optional, will be merged)')
    parser.add_argument('--output-dir', required=True, type=Path,
                        help='Output directory for Unreal assets')
    parser.add_argument('--target-size', type=int, default=4097,
                        choices=UNREAL_SIZES,
                        help=f'Target heightmap size (valid: {UNREAL_SIZES})')
    parser.add_argument('--vertical-exaggeration', type=float, default=2.0,
                        help='Vertical exaggeration factor (1.0-10.0)')
    parser.add_argument('--tile-id', default='tile_001',
                        help='Tile identifier')
    
    # Optional texture exports
    parser.add_argument('--s2-rgb', type=Path,
                        help='Path to Sentinel-2 RGB GeoTIFF (optional)')
    parser.add_argument('--anomaly', type=Path,
                        help='Path to anomaly probability GeoTIFF (optional)')
    parser.add_argument('--texture-size', type=int, default=4096,
                        help='Target texture size (power-of-2)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.dem.exists():
        logger.error(f"DEM not found: {args.dem}")
        sys.exit(1)
    
    # Validate vertical exaggeration
    if not 0.1 <= args.vertical_exaggeration <= 20.0:
        logger.warning(f"Vertical exaggeration {args.vertical_exaggeration} is unusual (recommend 1.0-10.0)")
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("UNREAL MINER - Export for Unreal Engine")
    logger.info("=" * 60)
    
    # Export heightmap
    import_params, profile, transform, crs = export_heightmap(
        args.dem, args.output_dir, args.target_size, args.vertical_exaggeration
    )
    
    # Export textures if provided
    if args.s2_rgb and args.s2_rgb.exists():
        export_texture(
            args.s2_rgb, args.output_dir,
            f'texture_rgb_{args.texture_size}.png',
            args.texture_size, linear=False
        )
    
    if args.anomaly and args.anomaly.exists():
        export_texture(
            args.anomaly, args.output_dir,
            f'anomaly_overlay_{args.texture_size}.png',
            args.texture_size, linear=True
        )
    
    # Generate metadata
    generate_meta_json(args.output_dir, import_params, profile, transform, crs, args)
    
    logger.info("=" * 60)
    logger.info("Export complete!")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Heightmap: heightmap_16bit.png ({args.target_size}x{args.target_size})")
    logger.info(f"Import into Unreal with Z Scale: {import_params['z_scale_cm']:.4f} cm")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
