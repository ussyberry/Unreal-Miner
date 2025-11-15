# Machine Learning Models

This document details the machine learning algorithms used in Unreal Miner for anomaly detection, including configuration options, customization techniques, and technical implementation details.

## Overview

Unreal Miner employs unsupervised machine learning to identify geological anomalies in multi-spectral satellite data. The current implementation focuses on **IsolationForest**, with extensibility for additional models.

---

## IsolationForest Anomaly Detection

### Algorithm Overview

**IsolationForest** is an unsupervised learning algorithm designed to detect outliers by isolating anomalies rather than profiling normal data.

#### Key Principles

1. **Isolation**: Anomalies are easier to isolate (fewer splits in decision trees)
2. **Randomization**: Uses random feature selection and split values
3. **Ensemble**: Combines multiple isolation trees for robust detection

#### Why IsolationForest for Mineral Exploration?

✅ **No Training Data Required**: Works without labeled examples of mineral deposits  
✅ **Handles High-Dimensional Data**: Effective with multi-band satellite features  
✅ **Computationally Efficient**: Faster than distance-based methods (k-NN, DBSCAN)  
✅ **Robust to Noise**: Outlier detection inherently handles noisy geospatial data  
✅ **Interpretable**: Anomaly scores indicate degree of "unusualness"

---

### Default Configuration

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(
    n_estimators=200,           # Number of isolation trees
    contamination=0.02,         # Expected proportion of anomalies (2%)
    max_samples='auto',         # Samples per tree (default: min(256, n_samples))
    max_features=1.0,           # Use all features
    bootstrap=False,            # No sample replacement
    random_state=42,            # Reproducibility
    n_jobs=-1                   # Use all CPU cores
)
```

### Configuration Parameters Explained

#### 1. `n_estimators` (Number of Trees)

**Default**: `200`

Controls the number of isolation trees in the ensemble.

| Value | Effect | Use Case |
|-------|--------|----------|
| 100 | Faster, less stable | Quick testing, small tiles |
| **200** | Balanced (recommended) | Production use |
| 500+ | More stable, slower | Critical exploration, large budgets |

**Recommendation**: Start with 200, increase if results vary between runs.

#### 2. `contamination` (Anomaly Rate)

**Default**: `0.02` (2%)

The expected proportion of anomalies in the dataset.

| Value | Anomalies per 25 km² | Interpretation |
|-------|---------------------|----------------|
| 0.01 (1%) | ~2,500 pixels | Very conservative, high-confidence targets |
| **0.02 (2%)** | ~5,000 pixels | Balanced for initial exploration |
| 0.05 (5%) | ~12,500 pixels | Aggressive, many false positives expected |
| 0.10 (10%) | ~25,000 pixels | Too permissive, not recommended |

**Guideline Selection**:
- **Greenfield exploration** (unknown geology): 0.02-0.03
- **Known mineralized district**: 0.03-0.05
- **Follow-up targeting** (validated area): 0.01

#### 3. `max_samples` (Subsampling)

**Default**: `'auto'` (min(256, n_samples))

Number of samples to build each tree. Affects memory and speed.

```python
# For large tiles (>50 km²), limit memory usage
model = IsolationForest(max_samples=512, ...)
```

#### 4. `max_features` (Feature Subsampling)

**Default**: `1.0` (use all features)

Fraction of features to consider per tree. Can improve diversity.

```python
# Use 80% of features per tree for more varied isolation
model = IsolationForest(max_features=0.8, ...)
```

---

### Input Features

IsolationForest operates on a feature vector extracted from multi-spectral satellite data.

#### Current Feature Set

```python
# scripts/process_fusion.py

features = np.column_stack([
    sar_vv,              # Sentinel-1 VV polarization (dB)
    sar_vh,              # Sentinel-1 VH polarization (dB)
    sar_vv / sar_vh,     # VV/VH ratio (surface scattering indicator)
    optical_red,         # Sentinel-2 Red band
    optical_green,       # Sentinel-2 Green band
    optical_blue,        # Sentinel-2 Blue band
    ndvi,                # Normalized Difference Vegetation Index
    texture_variance,    # Local SAR texture (GLCM)
    elevation,           # Digital Elevation Model (DEM)
    slope,               # Terrain slope (degrees)
    aspect               # Terrain aspect (radians)
])
```

**Total Dimensionality**: 11 features (expandable)

#### Feature Importance

Not all features contribute equally. Typical relative importance:

| Feature | Importance | Geological Significance |
|---------|------------|------------------------|
| **SAR VV/VH Ratio** | ⭐⭐⭐⭐⭐ | Surface roughness, composition |
| **SAR VV** | ⭐⭐⭐⭐ | Backscatter intensity |
| **Texture Variance** | ⭐⭐⭐⭐ | Structural heterogeneity |
| **NDVI** | ⭐⭐⭐ | Vegetation stress anomalies |
| **Elevation** | ⭐⭐⭐ | Geomorphology, erosion patterns |
| **Slope** | ⭐⭐ | Structural controls |
| **Optical RGB** | ⭐⭐ | Visual anomalies, alteration colors |

---

### Output

#### Anomaly Scores

```python
# Predict anomaly scores for all pixels
scores = model.decision_function(features)

# scores: float array, shape (n_pixels,)
# Higher (positive) = more normal
# Lower (negative) = more anomalous
```

#### Binary Labels

```python
# Predict binary anomaly labels
labels = model.predict(features)

# labels: int array, {1: normal, -1: anomaly}
```

#### Probability Map

For visualization in Unreal Engine, convert scores to 0-1 probability:

```python
from sklearn.preprocessing import MinMaxScaler

# Normalize scores to [0, 1]
scaler = MinMaxScaler()
anomaly_prob = scaler.fit_transform(scores.reshape(-1, 1)).flatten()

# Now: 0 = most normal, 1 = most anomalous
```

---

## Customization Techniques

### 1. Adjusting Sensitivity

**Goal**: Detect more or fewer anomalies based on exploration strategy

```python
# Conservative (fewer anomalies, higher confidence)
model = IsolationForest(contamination=0.01, n_estimators=300)

# Aggressive (more anomalies, initial reconnaissance)
model = IsolationForest(contamination=0.05, n_estimators=150)
```

**Validation**: Process a known mineralized area and adjust until:
- Known deposits are flagged
- False positives are manageable (<50% of anomalies)

### 2. Feature Engineering

Add custom features to improve detection:

#### Example: SAR Texture Features

```python
from skimage.feature import graycomatrix, graycoprops

def calculate_glcm_features(sar_vv_raster):
    """Calculate Gray-Level Co-occurrence Matrix texture features."""
    # Normalize to 0-255
    sar_normalized = ((sar_vv_raster - sar_vv_raster.min()) / 
                      (sar_vv_raster.max() - sar_vv_raster.min()) * 255).astype(np.uint8)
    
    # Calculate GLCM (1-pixel offset, 0° direction)
    glcm = graycomatrix(sar_normalized, distances=[1], angles=[0], levels=256)
    
    # Extract texture measures
    contrast = graycoprops(glcm, 'contrast')[0, 0]
    homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
    energy = graycoprops(glcm, 'energy')[0, 0]
    
    return contrast, homogeneity, energy

# Add to feature stack
texture_features = calculate_glcm_features(sar_vv)
features = np.column_stack([features, texture_features])
```

#### Example: Spectral Indices

```python
def calculate_iron_oxide_index(red, nir):
    """Calculate Ferrous Iron Index (common in alteration zones)."""
    return red / nir

def calculate_clay_index(swir1, swir2):
    """Calculate Clay Minerals Index."""
    return swir1 / swir2

# Add spectral indices
iron_index = calculate_iron_oxide_index(optical_red, optical_nir)
features = np.column_stack([features, iron_index])
```

### 3. Multi-Scale Detection

Detect anomalies at different spatial scales:

```python
from scipy.ndimage import gaussian_filter

def multi_scale_features(sar_vv, scales=[1, 5, 10]):
    """Generate features at multiple smoothing scales."""
    features_multi = []
    
    for scale in scales:
        smoothed = gaussian_filter(sar_vv, sigma=scale)
        features_multi.append(smoothed)
    
    return np.column_stack(features_multi)

# Detect both local and regional anomalies
features_ms = multi_scale_features(sar_vv)
features = np.column_stack([features, features_ms])
```

### 4. Temporal Analysis (Multi-Temporal Data)

Use time-series Sentinel data to detect changes:

```python
def temporal_anomaly_features(sar_t1, sar_t2, sar_t3):
    """Calculate temporal statistics for change detection."""
    # Mean backscatter over time
    mean_sar = np.mean([sar_t1, sar_t2, sar_t3], axis=0)
    
    # Temporal variance (stable vs. changing)
    var_sar = np.var([sar_t1, sar_t2, sar_t3], axis=0)
    
    # Trend (increasing or decreasing backscatter)
    trend = sar_t3 - sar_t1
    
    return mean_sar, var_sar, trend

# Add temporal features
features_temp = temporal_anomaly_features(sar_vv_jan, sar_vv_apr, sar_vv_jul)
features = np.column_stack([features, features_temp])
```

---

## Alternative Models

### One-Class SVM

For regions with strong geological priors:

```python
from sklearn.svm import OneClassSVM

model = OneClassSVM(
    kernel='rbf',
    gamma='auto',
    nu=0.02  # Similar to contamination
)

model.fit(features)
anomalies = model.predict(features)
```

**Pros**: Better boundary definition, kernel flexibility  
**Cons**: Slower than IsolationForest, requires parameter tuning

### Local Outlier Factor (LOF)

For density-based anomaly detection:

```python
from sklearn.neighbors import LocalOutlierFactor

model = LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.02,
    novelty=False  # Use fit_predict for training data
)

anomalies = model.fit_predict(features)
```

**Pros**: Captures local density variations  
**Cons**: Memory-intensive, slow for large tiles

### Autoencoder (Deep Learning)

For complex pattern learning (requires labeled data or transfer learning):

```python
from tensorflow import keras

# Simple autoencoder architecture
encoder = keras.Sequential([
    keras.layers.Dense(32, activation='relu', input_shape=(n_features,)),
    keras.layers.Dense(16, activation='relu'),
    keras.layers.Dense(8, activation='relu')
])

decoder = keras.Sequential([
    keras.layers.Dense(16, activation='relu', input_shape=(8,)),
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dense(n_features, activation='linear')
])

autoencoder = keras.Sequential([encoder, decoder])
autoencoder.compile(optimizer='adam', loss='mse')

# Train on "normal" data, anomalies = high reconstruction error
autoencoder.fit(features, features, epochs=50, batch_size=256)
reconstructed = autoencoder.predict(features)
anomaly_score = np.mean((features - reconstructed) ** 2, axis=1)
```

**Pros**: Learns complex patterns, state-of-the-art performance  
**Cons**: Requires GPU, longer training, needs more data

---

## Model Evaluation

### Validation Without Ground Truth

Since mineral deposits are rare, ground truth is often unavailable. Use these techniques:

#### 1. Visual Inspection

```python
import matplotlib.pyplot as plt

# Plot anomaly map
plt.imshow(anomaly_map, cmap='hot', vmin=0, vmax=1)
plt.colorbar(label='Anomaly Probability')
plt.title('Anomaly Detection Results')
plt.show()
```

**Check for**:
- Geologically plausible patterns (lineaments, circular features)
- Absence of obvious false positives (roads, fields)

#### 2. Geological Consistency

```python
# Overlay anomalies on geological map
import rasterio

with rasterio.open('geology_map.tif') as geo:
    geology = geo.read(1)

# Count anomalies by rock type
for rock_type in np.unique(geology):
    mask = geology == rock_type
    anomaly_count = np.sum(anomaly_labels[mask] == -1)
    print(f"Rock type {rock_type}: {anomaly_count} anomalies")
```

**Expected**: More anomalies in geologically favorable units

#### 3. Known Deposit Validation

```python
# Check if known deposits are detected
known_deposits = [
    (lat1, lon1),  # Deposit 1
    (lat2, lon2),  # Deposit 2
]

for lat, lon in known_deposits:
    pixel_x, pixel_y = latlon_to_pixel(lat, lon)
    is_anomaly = anomaly_labels[pixel_y, pixel_x] == -1
    print(f"Deposit at ({lat}, {lon}): {'DETECTED ✓' if is_anomaly else 'MISSED ✗'}")
```

---

## Performance Tuning

### Memory Optimization

For large tiles (>50 km²):

```python
# Process in chunks to avoid memory errors
chunk_size = 100000  # Process 100k pixels at a time
n_pixels = features.shape[0]

anomalies = np.zeros(n_pixels, dtype=int)

for i in range(0, n_pixels, chunk_size):
    chunk = features[i:i+chunk_size]
    anomalies[i:i+chunk_size] = model.predict(chunk)
```

### Speed Optimization

```python
# Use approximate nearest neighbors for faster LOF
from sklearn.neighbors import NearestNeighbors

nn = NearestNeighbors(n_neighbors=20, algorithm='ball_tree', n_jobs=-1)
nn.fit(features)
```

---

## Integration with Pipeline

### Configuration File

Edit `config/default.yaml`:

```yaml
anomaly_detection:
  algorithm: "isolation_forest"  # or "one_class_svm", "lof"
  
  isolation_forest:
    n_estimators: 200
    contamination: 0.02
    max_samples: auto
    random_state: 42
  
  feature_engineering:
    use_texture: true
    use_temporal: false  # Requires multi-date data
    use_spectral_indices: true
```

### Running with Custom Parameters

```bash
# Override contamination from command line
python scripts/process_fusion.py \
  --contamination 0.03 \
  --n-estimators 300 \
  --output data/processed/
```

---

## Future Model Enhancements

### Short-term
- [ ] Ensemble methods (combine IsolationForest + LOF + SVM)
- [ ] Hyperparameter optimization (Bayesian optimization)
- [ ] Feature selection (remove redundant features)

### Medium-term
- [ ] Supervised learning with transfer learning (pre-trained on global mineral database)
- [ ] Semi-supervised learning (active learning with user labeling)
- [ ] Graph neural networks (capture spatial relationships)

### Long-term
- [ ] Foundation models for geospatial data (e.g., Prithvi, Segment Anything)
- [ ] Multimodal learning (SAR + optical + gravity + magnetics)
- [ ] Explainable AI (SHAP values for feature importance)

---

## References

1. **Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008)**. "Isolation Forest." Proceedings of ICDM 2008.

2. **Breunig, M. M., et al. (2000)**. "LOF: Identifying Density-Based Local Outliers." Proceedings of ACM SIGMOD 2000.

3. **Schölkopf, B., et al. (2001)**. "Estimating the Support of a High-Dimensional Distribution." Neural Computation, 13(7), 1443-1471.

4. **Zuo, R., & Carranza, E. J. M. (2011)**. "Support Vector Machine: A tool for mapping mineral prospectivity." Computers & Geosciences, 37(12), 1967-1975.

---

**Last Updated**: 2024-11-15  
**Model Version**: IsolationForest v1.0  
**Scikit-learn Version**: 1.3.0+
