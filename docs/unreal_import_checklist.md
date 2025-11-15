# Unreal Engine Import Checklist

Complete guide for importing satellite-derived terrain and anomaly data into Unreal Engine.

## Unreal Engine Version Compatibility

| UE Version | Status | Compatibility Notes |
|------------|--------|---------------------|
| **5.4+** | ⚠️ Untested | Should work - same landscape system as 5.3 |
| **5.3** | ✅ Tested | Full support, Nanite landscapes recommended |
| **5.2** | ✅ Tested | Full support, Nanite available |
| **5.1** | ✅ Tested | Full support, Nanite landscapes introduced |
| **5.0** | ✅ Tested | Full support, minor UI changes from UE4 |
| **4.27** | ✅ Tested | Full support, most stable UE4 version |
| **4.26** | ✅ Compatible | Should work, not extensively tested |
| **4.25 and earlier** | ⚠️ Limited | Landscape import works, some features missing |

**Recommended Versions**:
- **Best for New Projects**: Unreal Engine 5.3 or 5.4 (Nanite, Lumen, latest features)
- **Most Stable**: Unreal Engine 4.27 (mature ecosystem, extensive documentation)
- **Experimental Features**: Unreal Engine 5.4+ (early access to cutting-edge tech)

**Cesium for Unreal Compatibility**:
- UE 5.0+: Cesium 2.0+ fully supported
- UE 4.27: Cesium 1.x supported (limited features)

---

## Pre-Import Checklist

Before importing into Unreal, verify:

- [ ] **Heightmap Format**: 16-bit single-channel PNG or RAW
- [ ] **Heightmap Size**: Power-of-two + 1 (513, 1025, 2049, 4097, 8193)
- [ ] **Texture Format**: Power-of-two dimensions (1024, 2048, 4096, 8192)
- [ ] **Coordinate System**: Projected CRS (UTM) documented in `meta.json`
- [ ] **Metadata File**: `meta.json` contains CRS, bbox, pixel_size, min/max elevation
- [ ] **File Organization**: All assets in same directory, clearly named
- [ ] **Backup**: Original GeoTIFFs preserved for re-export if needed

---

## Heightmap Specifications

### Unreal Landscape Sizing Rules

Unreal landscapes must follow: **Overall Resolution = (Component Size × Sections Per Component × Number of Components) + 1**

**Common Configurations**:

| Heightmap Size | Section Size | Sections/Comp | Components | Total Quads |
|----------------|--------------|---------------|------------|-------------|
| 513×513        | 63×63        | 1             | 8×8        | 512×512     |
| 1025×1025      | 127×127      | 1             | 8×8        | 1024×1024   |
| 2049×2049      | 127×127      | 1             | 16×16      | 2048×2048   |
| 4097×4097      | 127×127      | 1             | 32×32      | 4096×4096   |
| 8193×8193      | 127×127      | 1             | 64×64      | 8192×8192   |

**Section Size Options**: 7×7, 15×15, 31×31, 63×63, 127×127, 255×255

**Recommendations**:
- Small AOI (<10km): Use 1025×1025 or 2049×2049
- Medium AOI (10-50km): Use 4097×4097
- Large AOI (>50km): Use 8193×8193 or tile into multiple landscapes

### Heightmap Value Encoding

**16-bit PNG Encoding**:
```python
# Linear mapping from elevation to 16-bit integer
heightmap_value = (elevation - min_elev) / (max_elev - min_elev) * 65535
```

**Preserve Precision**:
- Store min/max elevation in `meta.json`
- Avoid lossy compression (use PNG, not JPEG)
- Test import by checking known elevation points

---

## Texture Specifications

### Base Imagery (RGB)

- **Format**: PNG or JPEG
- **Color Space**: sRGB (enable sRGB in Unreal import settings)
- **Dimensions**: Power-of-two (2048, 4096, 8192)
- **Compression**: 
  - PNG: Lossless (larger files)
  - JPEG: Quality 90-95 (smaller files, slight artifacts)
- **Aspect Ratio**: Match heightmap aspect ratio

### Anomaly Overlay

- **Format**: PNG or uncompressed TIFF
- **Color Space**: Linear (disable sRGB)
- **Channels**: Single-channel grayscale (0-255) or RGB for color ramps
- **Dimensions**: Match base imagery size
- **Encoding**: 
  - 0 = No anomaly
  - 255 = Maximum anomaly
  - Interpolated values for gradient

### SAR Backscatter (Optional)

- **Format**: PNG (grayscale)
- **Color Space**: Linear
- **Usage**: Drive roughness/normal maps in material
- **Range**: Remap dB values to 0-255

---

## Coordinate System & Georeferencing

### CRS Selection

**Recommended**: Local UTM zone for minimal distortion

**Determine UTM Zone**:
```python
import math

def get_utm_zone(lon, lat):
    zone_number = math.floor((lon + 180) / 6) + 1
    if lat >= 0:
        return f"EPSG:326{zone_number:02d}"  # Northern hemisphere
    else:
        return f"EPSG:327{zone_number:02d}"  # Southern hemisphere

# Example: lon=130.5, lat=-23.0
utm_epsg = get_utm_zone(130.5, -23.0)  # Returns "EPSG:32753"
```

### Pixel Resolution Mapping

**Critical**: Ensure world-space pixel size matches GeoTIFF resolution

```python
# GeoTIFF pixel size (meters)
pixel_size_m = 10.0

# Unreal uses centimeters
x_scale_cm = pixel_size_m * 100  # 1000 cm
y_scale_cm = pixel_size_m * 100  # 1000 cm

# Verify: (heightmap_width - 1) * pixel_size_m should equal AOI width in meters
```

### Vertical Scale Calculation

**Formula**:
```
Z Scale (cm) = [(max_elev - min_elev) / 65535] × 100 × vertical_exaggeration
```

**Example**:
```python
min_elev = 145.3  # meters
max_elev = 892.7  # meters
vertical_exaggeration = 2.0  # Optional artistic scaling

z_scale_cm = ((max_elev - min_elev) / 65535) * 100 * vertical_exaggeration
# Result: 1.145 cm per heightmap unit

# In Unreal: Set Landscape Z Scale = 1.145
```

**Vertical Exaggeration**:
- 1.0 = True scale (realistic)
- 2.0-3.0 = Subtle enhancement (recommended for visualization)
- 5.0-10.0 = Dramatic terrain (exploration/gaming)

---

## Unreal Engine Import Steps

### Method 1: Native Landscape Import

#### Step 1: Prepare Assets

Copy to Unreal project directory:
```
YourProject/Content/Satellite/
├── heightmap_16bit.png
├── texture_rgb_4096.png
├── anomaly_overlay_4096.png
└── meta.json
```

#### Step 2: Create Landscape

1. **Open Landscape Mode**: Press `Shift+2` or select from Mode panel
2. **Select Import Tab**: Click "Import from File"
3. **Load Heightmap**:
   - Click "Heightmap File" → Browse to `heightmap_16bit.png`
   - Unreal auto-detects dimensions
4. **Configure Settings**:
   - **Section Size**: 127×127 (good balance)
   - **Sections Per Component**: 1 (or 2 for LOD)
   - **Number of Components**: Auto-calculated
   - **Material**: Leave as default (apply later)

#### Step 3: Set Transform

1. **Location**: X=0, Y=0, Z=0 (or offset for multi-tile)
2. **Rotation**: X=0, Y=0, Z=0
3. **Scale**:
   - **X**: From `meta.json` → `x_scale_cm` (e.g., 1000.0)
   - **Y**: From `meta.json` → `y_scale_cm` (e.g., 1000.0)
   - **Z**: From `meta.json` → `z_scale_cm` (e.g., 1.145)

#### Step 4: Import

- Click **Import** button
- Wait for landscape generation (may take 1-5 minutes)
- Landscape appears in viewport

#### Step 5: Verify Import

**Visual Checks**:
- [ ] Terrain is not flat (check elevation variation)
- [ ] No extreme spikes or holes
- [ ] Overall shape matches expected topography
- [ ] World coordinates align with expected extent

**Measurement Validation**:
```cpp
// Blueprint: Get elevation at known coordinate
FVector KnownLocation(250000.0, 7450000.0, 0.0);  // UTM coordinates
float Elevation = Landscape->GetHeightAtLocation(KnownLocation);
// Compare with meta.json expected elevation
```

---

### Method 2: Cesium for Unreal (Georeferenced)

Use when precise global coordinates are required.

#### Step 1: Install Cesium for Unreal

1. Download plugin from [Cesium for Unreal](https://cesium.com/platform/cesium-for-unreal/)
2. Install to `YourProject/Plugins/CesiumForUnreal/`
3. Enable plugin in Unreal Editor
4. Restart editor

#### Step 2: Add CesiumGeoreference Actor

1. **Add Actor**: Content Browser → Search "CesiumGeoreference" → Drag to level
2. **Configure Georeference**:
   - **Origin Latitude**: Center of AOI (e.g., -22.75)
   - **Origin Longitude**: Center of AOI (e.g., 130.5)
   - **Origin Height**: Mean elevation (e.g., 500.0)

#### Step 3: Add Cesium3DTileset

1. **Add Tileset Actor**: Search "Cesium3DTileset"
2. **Set Ion Asset ID**: If using Cesium ion (optional)
3. **Or Use Local Files**: Point to local quantized-mesh tiles

#### Step 4: Add Raster Overlay

1. **Add Raster Overlay**: Component on Cesium3DTileset
2. **Configure**:
   - **Source**: Local GeoTIFF or URL
   - **Path**: Point to `s2_rgb_mosaic.tif`
3. **Material Options**: Overlay opacity, blend mode

#### Step 5: Add Custom Landscape

For anomaly overlay with Cesium base terrain:

1. Create Landscape as in Method 1
2. **Position Landscape**:
   - Use `CesiumGeoreference->TransformLongLatHeightToUnreal()` to compute Unreal coordinates
   - Set Landscape location to match UTM bbox origin
3. **Apply Anomaly Material**: See Material Setup section

---

## Material Setup

### Basic Material Graph

**Goal**: Display RGB base texture with adjustable anomaly overlay

#### Create Material

1. **Content Browser**: Right-click → Material → Name: `M_Terrain_Anomaly`
2. **Open Material Editor**: Double-click material

#### Node Setup

**Input Textures**:
```
TextureSample (T_BaseRGB) → [RGB output]
TextureSample (T_AnomalyOverlay) → [R output]
```

**UV Coordinates**:
```
LandscapeLayerCoords (Mapping Scale = 1.0) → [UV input for both textures]
```

**Anomaly Overlay Logic**:
```
T_AnomalyOverlay.R → Multiply → [Scalar Parameter: P_AnomalyOpacity]
                                        ↓
T_BaseRGB → Lerp (Alpha ←──────────────┘
               B ← [Color Parameter: P_AnomalyColor])
→ BaseColor output
```

**Parameters**:
- `P_AnomalyOpacity` (Scalar): 0.0-1.0, Default: 0.5
- `P_AnomalyColor` (Vector): Default: (1.0, 0.0, 0.0) [Red]

#### Advanced: Color Ramp

For gradient anomaly visualization:

**Custom HLSL Node**:
```hlsl
// Input: AnomalyValue (0-1)
float3 ColorRamp(float value)
{
    // 3-color gradient: Blue (low) → Yellow (mid) → Red (high)
    float3 low = float3(0.2, 0.2, 1.0);    // Blue
    float3 mid = float3(1.0, 0.92, 0.3);   // Yellow
    float3 high = float3(1.0, 0.0, 0.0);   // Red
    
    if (value < 0.5)
        return lerp(low, mid, value * 2.0);
    else
        return lerp(mid, high, (value - 0.5) * 2.0);
}

// Return value
return ColorRamp(AnomalyValue);
```

**Node Connections**:
```
T_AnomalyOverlay.R → Custom Node (ColorRamp) → Lerp.B
```

### SAR Roughness Material

Use SAR backscatter to drive surface roughness:

```
TextureSample (T_SAR_Backscatter) → Power (Exp=2.2) → Multiply (0.5)
                                                          ↓
                                                    Roughness output
```

**Normal Map from SAR**:
```
T_SAR_Backscatter → NormalFromHeightmap (Intensity=2.0)
                                            ↓
                                      Normal output
```

### Material Instance

1. **Create Material Instance**: Right-click `M_Terrain_Anomaly` → Create Material Instance
2. **Name**: `MI_Terrain_Anomaly_Instance`
3. **Assign to Landscape**: Select landscape → Details panel → Landscape Material → Select MI
4. **Adjust Parameters**:
   - Toggle `P_AnomalyOpacity` in Details panel
   - Test different `P_AnomalyColor` values

---

## Multi-Tile Management

For large AOIs split into multiple tiles:

### Tile Naming Convention

```
tile_x00_y00_heightmap.png
tile_x01_y00_heightmap.png
tile_x00_y01_heightmap.png
...
```

### World Partition (Unreal 5.0+)

1. **Enable World Partition**: Project Settings → World Partition
2. **Create Tile Landscapes**:
   - Import each tile as separate Landscape actor
   - Position using `meta.json` bbox coordinates
3. **Configure Streaming**:
   - Set Landscape → Details → LOD settings
   - Enable Streaming Distance
4. **Data Layers**: Organize tiles into data layers for management

### Manual Tiling (Unreal 4.x)

1. **Import Tiles**: Import each heightmap as separate landscape
2. **Position Tiles**:
   ```python
   # Calculate Unreal location from UTM bbox
   tile_x_unreal = (tile_bbox_xmin - origin_xmin) * 100  # to cm
   tile_y_unreal = (tile_bbox_ymin - origin_ymin) * 100
   ```
3. **Blend Seams**: Use Landscape Spline tool to smooth tile boundaries

---

## Performance Optimization

### LOD Settings

**Landscape LOD**:
- **LOD 0**: Full resolution (close-up)
- **LOD 1-6**: Progressive simplification
- **Screen Size**: Configure transition distances

**Recommended Settings** (Details panel):
- **LOD Distribution**: 1.5 (moderate falloff)
- **LOD 0 Screen Size**: 0.5
- **Enable Streaming**: True for tiles >4097

### Texture Streaming

1. **Enable Virtual Textures**: Material → Details → Enable Virtual Texture Support
2. **Create Runtime Virtual Texture**:
   - Add RVT Volume to level
   - Size: 8192×8192 (or larger)
   - Materials: BaseColor, Normal, Roughness
3. **Assign to Landscape**: Landscape → Details → Virtual Texture → Select RVT

### Nanite (Unreal 5.0+)

**Note**: Landscapes do not support Nanite directly. Use for static meshes (e.g., detailed outcrops).

---

## Troubleshooting

### Issue: Flat Landscape

**Symptoms**: Imported landscape appears completely flat

**Solutions**:
1. Check Z-scale value (should be >0.001)
2. Verify heightmap is 16-bit (not 8-bit)
3. Ensure `min_elev` ≠ `max_elev` in processing
4. Re-export heightmap with correct range

### Issue: Extreme Elevation Spikes

**Symptoms**: Sharp spikes or holes in terrain

**Solutions**:
1. Check for NoData values in original DEM
2. Re-process with `-dstnodata` flag:
   ```bash
   gdalwarp -dstnodata 0 input.tif output.tif
   ```
3. Apply median filter in export script:
   ```python
   from scipy.ndimage import median_filter
   dem_smooth = median_filter(dem_data, size=3)
   ```

### Issue: Texture Misalignment

**Symptoms**: RGB texture doesn't match terrain features

**Solutions**:
1. Verify all GeoTIFFs used same CRS:
   ```bash
   gdalinfo dem.tif | grep AUTHORITY
   gdalinfo rgb.tif | grep AUTHORITY
   ```
2. Check bbox alignment:
   ```bash
   gdalinfo -mm dem.tif | grep "Corner Coordinates"
   ```
3. Re-export textures with exact heightmap extent

### Issue: Seams Between Tiles

**Symptoms**: Visible lines at tile boundaries

**Solutions**:
1. Use overlapping extent (1-2 pixel overlap)
2. Apply Gaussian blur to tile edges
3. Use Landscape Spline tool to blend manually
4. Enable mipmap blending in Material

### Issue: Low Frame Rate

**Symptoms**: Poor performance in Unreal Editor/Runtime

**Solutions**:
1. Reduce landscape LOD 0 screen size
2. Enable texture streaming
3. Use lower resolution textures (2048 instead of 4096)
4. Split large landscapes into smaller tiles with streaming
5. Profile with Unreal Insights: `stat unit`, `stat landscape`

---

## Validation Checklist

After import, verify:

- [ ] **Elevation Accuracy**: Spot-check known elevation points
- [ ] **Texture Alignment**: RGB features align with terrain (rivers, roads)
- [ ] **Anomaly Overlay**: Anomalies appear at expected locations
- [ ] **Scale Correctness**: Measure distances between known landmarks
- [ ] **Performance**: Maintains 30+ FPS in editor viewport
- [ ] **Material Parameters**: Anomaly opacity and color adjustable
- [ ] **LOD Transitions**: No popping or artifacts at distance
- [ ] **Collision**: Landscape collision mesh generated correctly

---

## Best Practices

1. **Always Keep Originals**: Preserve GeoTIFFs and meta.json for re-export
2. **Document Coordinates**: Record CRS, origin, and scale in project documentation
3. **Version Control Assets**: Use Git LFS for binary assets (PNG, uasset)
4. **Test Small First**: Import 1025×1025 test tile before full 8193×8193
5. **Material Instances**: Use MI for parameter variations, not base material edits
6. **Backup Projects**: Large landscapes can corrupt; maintain backups
7. **Iterate Export**: Adjust Z-scale and vertical exaggeration until visually correct
8. **Ground Truth**: Compare with known terrain features (Google Earth, field data)

---

## Example meta.json

Complete metadata file for import:

```json
{
  "tile_id": "australia_mining_001",
  "crs": "EPSG:32753",
  "bbox": [240000, 7400000, 340000, 7500000],
  "bbox_wgs84": [130.5, -23.5, 131.5, -22.5],
  "pixel_size_m": 10.0,
  "width": 4097,
  "height": 4097,
  "min_elevation_m": 145.3,
  "max_elevation_m": 892.7,
  "elevation_range_m": 747.4,
  "vertical_exaggeration": 2.0,
  "z_scale_cm": 1.145,
  "processing_date": "2024-11-12T10:30:00Z",
  "source_data": {
    "sentinel1_ids": ["S1A_IW_GRDH_1SDV_20240115T213045_20240115T213110_051234_062F3A_1234"],
    "sentinel2_ids": ["S2A_MSIL2A_20240110T013711_N0510_R074_T52KFU_20240110T041234"],
    "dem_source": "SRTM_1arcsec"
  },
  "unreal_import_parameters": {
    "landscape_size": "4097x4097",
    "section_size": "127x127",
    "sections_per_component": 1,
    "number_of_components": "32x32",
    "x_scale_cm": 1000.0,
    "y_scale_cm": 1000.0,
    "z_scale_cm": 1.145,
    "location_offset": [0.0, 0.0, 0.0]
  },
  "textures": {
    "base_rgb": "texture_rgb_4096.png",
    "anomaly_overlay": "anomaly_overlay_4096.png",
    "sar_backscatter": "sar_backscatter_4096.png"
  },
  "validation": {
    "known_elevation_points": [
      {"name": "Peak A", "utm_x": 285000, "utm_y": 7450000, "elevation_m": 687.2},
      {"name": "Valley B", "utm_x": 275000, "utm_y": 7425000, "elevation_m": 234.8}
    ]
  }
}
```

---

**Last Updated**: 2024-11-12  
**Next**: See [Material Graph Guide](../unreal/material_graph.md) for advanced material setup
