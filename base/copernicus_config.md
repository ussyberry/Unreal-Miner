# Copernicus Data Space Infrastructure Configuration

## Overview
This document provides comprehensive configuration information for accessing and processing Copernicus satellite data through the new Data Space Infrastructure APIs.

## Sentinel Missions

### Sentinel-1
- **Mission**: C-band Synthetic Aperture Radar (SAR)
- **Frequency**: 5.405 GHz (C-band)
- **Polarization**: Dual-polarization (VV+VH, HH+HV) or Full polarimetry
- **Resolution**: 
  - Interferometric Wide (IW): ~20m × 22m
  - Extra Wide (EW): ~40m × 40m
  - Strip Map (SM): ~5m × 20m
- **Revisit Time**: 6 days (12 days with dual polarization)
- **Applications**: 
  - Land monitoring
  - Ocean monitoring
  - Emergency response
  - Change detection

### Sentinel-2
- **Mission**: Multi-spectral optical imaging
- **Spectral Bands**: 13 bands
  - Coastal aerosol (443 nm)
  - Blue (490 nm)
  - Green (560 nm)
  - Red (665 nm)
  - Vegetation red edge (705 nm)
  - Vegetation red edge (740 nm)
  - Vegetation red edge (783 nm)
  - NIR (842 nm)
  - Narrow NIR (865 nm)
  - Water vapour (945 nm)
  - SWIR (1610 nm)
  - SWIR (2190 nm)
- **Resolution**:
  - 10m: Bands 2, 3, 4, 8
  - 20m: Bands 5, 6, 7, 8A, 11, 12
  - 60m: Bands 1, 9, 10
- **Revisit Time**: 5 days (with two satellites)
- **Applications**:
  - Land cover classification
  - Vegetation monitoring
  - Water quality assessment
  - Mineral exploration

### Sentinel-3
- **Mission**: Ocean and land monitoring
- **Instruments**:
  - OLCI (Ocean and Land Colour Instrument): 21 spectral bands
  - SLSTR (Sea and Land Surface Temperature Radiometer): dual-view radiometer
- **Applications**:
  - Sea surface temperature
  - Ocean color
  - Land surface temperature
  - Wildfire detection

### Sentinel-5P
- **Mission**: Atmospheric composition monitoring
- **Instrument**: TROPOMI (TROPOspheric Monitoring Instrument)
- **Products**:
  - NO₂, SO₂, O₃, CO, CH₄
  - Aerosols, UV radiation
- **Applications**:
  - Air quality monitoring
  - Climate research
  - Volcanic ash detection

### Sentinel-6
- **Mission**: Ocean altimetry
- **Instruments**: Radar altimeter, microwave radiometer
- **Applications**:
  - Sea level monitoring
  - Ocean circulation
  - Climate studies

## Authentication APIs

### Token Authentication
- **Endpoint**: `https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token`
- **Grant Type**: `client_credentials`
- **Required Parameters**:
  - `client_id`: OAuth client ID
  - `client_secret`: OAuth client secret
  - `scope`: `cdse` (for data access)
- **Response**: Bearer token with expiration time
- **Usage**: Include in Authorization header: `Bearer <token>`

### OAuth Configuration
```python
# Example OAuth setup
token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
payload = {
    'grant_type': 'client_credentials',
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'scope': 'cdse'
}
```

## Data Access APIs

### OData API
- **Base URL**: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
- **Features**:
  - OData standard queries
  - Complex filtering capabilities
  - Spatial and temporal filtering
  - Metadata querying
- **Query Examples**:
  ```sql
  $filter=Name eq 'Sentinel-2' and ContentDate/Start ge 2025-12-10T00:00:00.000Z
  and footprint intersect geography'ST Polygon((...))' and CloudCoverPercentage le 20
  ```

### OpenSearch API
- **Standard**: OpenSearch 1.1
- **Features**:
  - Simple query syntax
  - RSS/Atom output formats
  - Basic filtering capabilities
- **Use Case**: Simple searches and basic filtering

### STAC (SpatioTemporal Asset Catalog)
- **Standard**: STAC API
- **Features**:
  - Modern spatiotemporal data discovery
  - JSON-based queries
  - Cloud-optimized formats
- **Use Case**: Cloud-native data access

### S3 API
- **Protocol**: AWS S3-compatible
- **Features**:
  - Direct data access
  - Bulk downloads
  - Integration with cloud tools
- **Use Case**: Large-scale data retrieval and processing

## Data Processing APIs

### Sentinel-1 SLC Burst
- **Purpose**: High-resolution SAR data processing
- **Features**:
  - Burst-level data access
  - Interferometric processing
  - Terrain correction
- **Applications**: 
  - High-precision change detection
  - Digital elevation models
  - Surface deformation monitoring

### TCP API
- **Purpose**: Transfer Control Protocol for data management
- **Features**:
  - Data transfer optimization
  - Connection management
  - Bandwidth control
- **Use Cases**: Large data file transfers and streaming

### Traceability API
- **Purpose**: Data provenance and lineage tracking
- **Features**:
  - Data processing history
  - Transformation tracking
  - Quality metadata
- **Use Cases**: Data quality assurance and audit trails

## Subscriptions API
- **Purpose**: Automated data delivery
- **Features**:
  - Define data filters
  - Schedule deliveries
  - Email notifications
- **Use Cases**:
  - Regular monitoring
  - Emergency response
  - Custom data pipelines

## openEO API

### Overview
openEO (Open Earth Observation) is a modern API standard for cloud-based geospatial data processing and analysis.

### openEO Authentication
- **Purpose**: Authentication for openEO services
- **Methods**:
  - Client credentials (OAuth 2.0)
  - Username/password
  - API key authentication
- **Configuration**:
  ```python
  from openeo import Connection
  conn = Connection(
      auth_type="client_credentials",
      client_id="your_client_id",
      client_secret="your_client_secret",
      url="https://openeo.dataspace.copernicus.eu"
  )
  ```

### openEO Collections
- **Purpose**: Discover available data collections
- **Features**:
  - Sentinel-1, Sentinel-2, Sentinel-3 collections
  - Custom collections and derived products
  - Metadata and metadata filtering
- **Usage**:
  ```python
  # List available collections
  collections = conn.list_collections()
  
  # Filter collections
  sentinel2_collections = [c for c in collections if "Sentinel-2" in c["id"]]
  ```

### openEO Processes
- **Purpose**: Define processing workflows
- **Available Processes**:
  - **Load Data**: Load satellite collections
  - **Apply Processing**: Apply band math, filters
  - **Reduce Data**: Aggregation and statistical operations
  - **Export**: Export results to various formats
- **Common Processes for Mineral Exploration**:
  - `NDVI`: Vegetation index calculation
  - `NDWI**: Water index calculation
  - `Band Math`: Custom spectral indices
  - `Reduce Region**: Area statistics
  - `Resample`: Spatial resolution adjustment

### openEO File Formats
- **Supported Formats**:
  - **GeoTIFF**: Standard geospatial raster format
  - **NetCDF**: Multi-dimensional scientific data
  - **CSV**: Tabular data export
  - **JSON**: Structured data export
  - **PNG/JPEG**: Visual imagery export
- **Format Selection**:
  ```python
  # Export options
  conn.download(
      process,
      format="GeoTIFF",
      options={"tiled": True, "overview": True}
  )
  ```

### openEO Python Client
- **Installation**: `pip install openeo`
- **Key Features**:
  - High-level Python API
  - Process graph building
  - Batch processing support
  - Progress monitoring
- **Example Workflow**:
  ```python
  from openeo import Connection
  from openeo.processes import ndvi
  
  # Connect to openEO
  conn = Connection(
      auth_type="client_credentials",
      client_id="your_client_id",
      client_secret="your_client_secret",
      url="https://openeo.dataspace.copernicus.eu"
  )
  
  # Define processing workflow
  process = conn.load_collection(
      "SENTINEL2_L2A",
      spatial_extent={"west": -75.8, "east": -75.4, "south": 45.2, "north": 45.4},
      temporal_extent=["2025-12-10", "2025-12-10"],
      bands=["B04", "B08"]  # Red and NIR for NDVI
  ).apply_process(ndvi).save_result(format="GeoTIFF")
  
  # Execute and download
  job = conn.create_job(process)
  job.start_and_wait()
  job.download_files("./output/")
  ```

### Dynamic Land Cover Mapping Example
- **Purpose**: Land cover classification for mineral exploration
- **Workflow**:
  1. Load multi-temporal Sentinel-2 data
  2. Calculate spectral indices (NDVI, NDWI, etc.)
  3. Apply machine learning classification
  4. Generate land cover maps
  5. Extract mineral indicator signatures
- **Implementation**:
  ```python
  # Multi-temporal analysis
  process = (
      conn.load_collection("SENTINEL2_L2A", temporal_extent=["2025-01-01", "2025-12-31"])
      .filter_temporal("2025-12-10")
      .apply(lambda data: data.add_dimension("time", "2025-12-10"))
      .reduce_time(lambda x: x.mean())
      .apply_process("NDVI", nir="B08", red="B04")
      .save_result(format="GeoTIFF")
  )
  ```

### openEO vs Traditional APIs Comparison
| Feature | openEO | Traditional OData |
|---------|---------|-------------------|
| **Processing** | Cloud-based processing | Download-then-process |
| **Scalability** | Built for large datasets | Limited by local resources |
| **Complex Workflows** | Process graphs support | Limited query capabilities |
| **Cost Model** | Pay-for-processing | Free data access |
| **Best For** | Complex analysis, large areas | Simple downloads, small areas |

### openEO Integration with Unreal Miner
- **Recommended Approach**:
  1. Use openEO for initial data processing and feature extraction
  2. Export processed results to local format
  3. Apply Unreal Miner ML algorithms for anomaly detection
  4. Generate 3D visualizations and mineral maps
- **Benefits**:
  - Reduced computational overhead
  - Scalable processing capabilities
  - Access to advanced processing algorithms
  - Integration with cloud infrastructure

## Rate Limiting and Processing Units

### Processing Units (PU)
- **Concept**: New rate limiting system replacing traditional API limits
- **Measurement**: Each API operation consumes Processing Units
- **Monitoring**: Track PU consumption to avoid service interruptions
- **Management**: Implement PU tracking in applications

### Rate Limiting Best Practices
- Monitor PU consumption
- Implement retry logic with exponential backoff
- Batch operations when possible
- Cache results to reduce API calls

## Data Formats and Products

### Standard Products
- **Level-1C**: Top-of-atmosphere reflectance (Sentinel-2)
- **Level-2A**: Bottom-of-atmosphere reflectance (Sentinel-2)
- **GRD**: Ground Range Detected (Sentinel-1)
- **SLC**: Single Look Complex (Sentinel-1)

### File Formats
- **Sentinel-2**: JPEG 2000 compression
- **Sentinel-1**: GeoTIFF, NetCDF
- **Metadata**: XML, JSON

## Configuration for Unreal Miner

### Authentication Setup
```python
# Environment variables
COPERNICUS_CLIENT_ID=your_client_id
COPERNICUS_CLIENT_SECRET=your_client_secret

# API endpoints
BASE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
OPENEO_URL = "https://openeo.dataspace.copernicus.eu"
```

### Data Query Parameters
```python
# Ottawa bounding box
bbox = "-75.8,45.2,-75.4,45.4"  # xmin,ymin,xmax,ymax

# Date range
start_date = "2025-12-10"
end_date = "2025-12-10"

# Cloud cover filter (Sentinel-2 only)
max_cloud = 20

# openEO collection IDs
SENTINEL1_COLLECTION = "SENTINEL1_GRD"
SENTINEL2_COLLECTION = "SENTINEL2_L2A"
SENTINEL3_COLLECTION = "SENTINEL3_OLCI_L1R"
```

### Recommended Workflow
#### Option 1: Traditional Download-then-Process
1. **Authentication**: Obtain OAuth token
2. **Data Discovery**: Use OData API to find suitable products
3. **Metadata Check**: Verify cloud cover and data quality
4. **Data Download**: Use S3 API for bulk downloads
5. **Processing**: Apply Unreal Miner processing pipeline
6. **Export**: Generate mineral anomaly maps and 3D assets

#### Option 2: openEO Cloud Processing (Recommended)
1. **Authentication**: Set up openEO client credentials
2. **Data Loading**: Load collections using openEO API
3. **Pre-processing**: Apply cloud masking and atmospheric correction
4. **Feature Extraction**: Calculate spectral indices and terrain metrics
5. **ML Processing**: Apply mineral anomaly detection algorithms
6. **Export**: Download results for Unreal Engine integration

### openEO Integration Example for Unreal Miner
```python
from openeo import Connection
from openeo.processes import ndvi, ndwi, band_math

def setup_openeo_connection():
    """Set up openEO connection for Unreal Miner"""
    return Connection(
        auth_type="client_credentials",
        client_id=os.getenv('COPERNICUS_CLIENT_ID'),
        client_secret=os.getenv('COPERNICUS_CLIENT_SECRET'),
        url="https://openeo.dataspace.copernicus.eu"
    )

def create_mineral_extraction_workflow(conn, bbox, date):
    """Create processing workflow for mineral anomaly detection"""
    
    # Load Sentinel-2 data
    data = conn.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "west": bbox[0], "east": bbox[2], 
            "south": bbox[1], "north": bbox[3]
        },
        temporal_extent=[date, date],
        bands=["B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B11", "B12"]
    )
    
    # Apply cloud masking
    data = data.apply_process("mask_scl", data=data, scl_band="SCL")
    
    # Calculate spectral indices
    ndvi_data = data.apply_process(ndvi, nir="B08", red="B04")
    ndwi_data = data.apply_process(ndwi, green="B03", nir="B08")
    
    # Custom mineral indices
    iron_oxide = data.apply_process(
        band_math,
        data=data,
        expression="(B12 - B08) / (B12 + B08)"  # Iron oxide index
    )
    
    clay_mineral = data.apply_process(
        band_math,
        data=data,
        expression="(B11 - B12) / (B11 + B12)"  # Clay mineral index
    )
    
    # Combine all indices
    combined = data.merge_bands([ndvi_data, ndwi_data, iron_oxide, clay_mineral])
    
    # Export for Unreal Miner processing
    return combined.save_result(format="GeoTIFF")

def execute_mineral_analysis():
    """Execute complete mineral analysis workflow"""
    conn = setup_openeo_connection()
    
    # Ottawa coordinates
    bbox = [-75.8, 45.2, -75.4, 45.4]
    date = "2025-12-10"
    
    # Create and execute workflow
    workflow = create_mineral_extraction_workflow(conn, bbox, date)
    
    # Start job and monitor
    job = conn.create_job(workflow)
    job.start_and_wait()
    
    # Download results
    output_dir = "./data/processed/mineral_analysis"
    job.download_files(output_dir)
    
    return output_dir
```

### Hybrid Approach: Best of Both Worlds
```python
def hybrid_mineral_detection():
    """Combine openEO preprocessing with Unreal Miner ML"""
    
    # Step 1: Use openEO for data preprocessing
    conn = setup_openeo_connection()
    
    # Load and preprocess data
    data = conn.load_collection("SENTINEL2_L2A", ...)
    processed = data.apply_process("atmospheric_correction").apply_process("cloud_masking")
    
    # Extract key features
    features = processed.apply_process("calculate_indices", 
                                       indices=["NDVI", "NDWI", "IronOxide", "ClayMineral"])
    
    # Export feature data
    features.save_result(format="CSV")
    
    # Step 2: Use Unreal Miner for ML analysis
    # (Load CSV data and apply RandomForest classification)
    
    # Step 3: Generate 3D visualizations
    # (Export results to Unreal Engine format)
```

### Processing Recommendations
- **For Large Areas**: Use openEO cloud processing
- **For Complex ML**: Use hybrid approach
- **For Quick Analysis**: Use traditional download
- **For Real-time Processing**: Consider S3 API streaming

### Cost Considerations
- **openEO**: Pay-for-processing (cost-effective for complex workflows)
- **Traditional APIs**: Free data access (cost-effective for simple downloads)
- **Hybrid**: Optimized cost-balance for complex analysis

## Error Handling and Troubleshooting

### Common Issues
- **Authentication failures**: Check client ID/secret and scope
- **No data found**: Adjust search parameters or date range
- **Rate limiting**: Implement PU monitoring and backoff
- **Network issues**: Add retry logic and timeout handling

### Best Practices
- Always validate API responses
- Implement proper error handling
- Monitor PU consumption
- Cache frequently accessed metadata
- Use appropriate data formats for processing

## Integration Examples

### Python Example
```python
import requests
from datetime import datetime

# Authenticate
auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
payload = {
    'grant_type': 'client_credentials',
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'scope': 'cdse'
}

response = requests.post(auth_url, data=payload)
token = response.json()['access_token']

# Query data
headers = {'Authorization': f'Bearer {token}'}
query_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
params = {
    '$filter': "Name eq 'Sentinel-2' and ContentDate/Start ge 2025-12-10T00:00:00.000Z"
}

response = requests.get(query_url, headers=headers, params=params)
data = response.json()
```

This configuration provides a comprehensive guide for accessing and processing Copernicus satellite data through the modern Data Space Infrastructure APIs.