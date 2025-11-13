# Unreal Miner - Data Policy and Usage Restrictions

## Table of Contents

1. [Data Sources and Licensing](#data-sources-and-licensing)
2. [Repository Data Guidelines](#repository-data-guidelines)
3. [Copernicus Data Usage](#copernicus-data-usage)
4. [DEM Data](#dem-data)
5. [Acceptable Use](#acceptable-use)
6. [Prohibited Use](#prohibited-use)
7. [Citation Requirements](#citation-requirements)
8. [Privacy and Compliance](#privacy-and-compliance)

---

## Data Sources and Licensing

### Sentinel-1 and Sentinel-2 Data

**Source**: European Space Agency (ESA) Copernicus Programme

**License**: Free and open access under the [Copernicus Sentinel Data Terms and Conditions](https://scihub.copernicus.eu/twiki/do/view/SciHubWebPortal/TermsConditions)

**Key Terms**:
- ✅ Free for commercial and non-commercial use
- ✅ Redistribution allowed with proper attribution
- ✅ Modification and derivative works permitted
- ❌ No warranty provided
- ❌ ESA liability limited

**Required Attribution**:
```
Contains modified Copernicus Sentinel data [Year]
```

### SNAP Toolbox

**Source**: European Space Agency (ESA)

**License**: GNU General Public License v3.0 (GPL-3.0)

**Terms**: Open source software, free to use and modify under GPL-3.0 terms

### GDAL Library

**License**: X/MIT License

**Terms**: Permissive open source license

### Python Libraries

All Python dependencies (rasterio, scikit-learn, etc.) use open source licenses compatible with this project. See `requirements.txt` for specific packages.

---

## Repository Data Guidelines

### What Not to Commit

**🚫 NEVER commit these files**:

1. **Raw Satellite Data**:
   - Sentinel-1 GRD products (`.SAFE` directories, typically 1-5 GB each)
   - Sentinel-2 L2A products (`.SAFE` directories, typically 0.5-2 GB each)
   - Full DEM tiles (can be hundreds of MB)

2. **Processed Intermediate Files**:
   - Large GeoTIFF files (>10 MB)
   - Uncompressed rasters
   - Temporary processing files

3. **Credentials and Secrets**:
   - `.env` files with API keys
   - Copernicus credentials
   - Cesium ion tokens
   - Any authentication tokens

4. **Personal Information**:
   - User data
   - Project-specific coordinates of sensitive sites
   - Any personally identifiable information (PII)

### What You May Commit

**✅ Acceptable files**:

1. **Small Sample Data** (<10 MB):
   - Representative tiles for testing
   - Downsampled examples
   - Already included in `data/sample_tile/`

2. **Metadata**:
   - JSON metadata files
   - Configuration files (without secrets)
   - Processing logs (sanitized)

3. **Code and Documentation**:
   - Python scripts
   - Markdown documentation
   - Jupyter notebooks (without large outputs)

### Using Git LFS

For files between 10-100 MB, use Git Large File Storage (LFS):

```bash
git lfs install
git lfs track "*.tif"
git lfs track "*.tiff"
git add .gitattributes
```

### Alternative Storage Solutions

For large datasets, use:

1. **Cloud Storage**:
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage

2. **Scientific Data Repositories**:
   - Zenodo
   - Figshare
   - Dataverse

3. **Direct Download Scripts**:
   - Include scripts that download data on-demand
   - See `scripts/fetch_copernicus.sh`

---

## Copernicus Data Usage

### Access and Registration

1. **Registration Required**: Create free account at https://scihub.copernicus.eu/dhus/#/self-registration

2. **Credentials Storage**:
   ```bash
   # Store in .env file (NEVER commit this file)
   COPERNICUS_USER=your_username
   COPERNICUS_PASSWORD=your_password
   ```

3. **Rate Limits**: 
   - Max 2 concurrent downloads
   - Respect download quotas
   - Use API responsibly

### Download Guidelines

**Best Practices**:
- Download only what you need
- Use specific date ranges and AOI
- Cache downloads locally
- Don't repeatedly download same data

**Example Download Script**:
```bash
#!/bin/bash
# Download Sentinel-1 for specific area and date
./scripts/fetch_copernicus.sh \
    --product S1A_GRD \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --bbox "37.0,-122.5,38.0,-121.5"
```

### Redistribution Rules

**You MAY**:
- Share processed results and derivative products
- Publish analysis outputs
- Include processed data in publications

**You MUST**:
- Include Copernicus attribution
- Provide source data information
- Link to original data source

**You MUST NOT**:
- Redistribute raw Sentinel data without attribution
- Claim ownership of Copernicus data
- Violate ESA terms and conditions

---

## DEM Data

### SRTM (Shuttle Radar Topography Mission)

**Source**: NASA/USGS

**License**: Public domain (U.S. government data)

**Resolution**: 30m (1 arc-second) or 90m (3 arc-second)

**Access**: Via USGS Earth Explorer or SNAP auto-download

**Attribution**: "SRTM data courtesy of USGS"

### ALOS World 3D

**Source**: JAXA (Japan Aerospace Exploration Agency)

**License**: Free for research, license required for commercial use

**Resolution**: 30m

**Terms**: Must register and agree to JAXA terms

### EU-DEM

**Source**: European Environment Agency

**License**: EEA standard re-use policy

**Coverage**: Europe only

**Attribution Required**: Yes

---

## Acceptable Use

### ✅ Permitted Activities

1. **Research and Education**:
   - Academic research
   - Educational projects
   - Scientific publications
   - Student theses

2. **Commercial Use**:
   - Mineral exploration (with proper licenses)
   - Environmental consulting
   - Agriculture monitoring
   - Infrastructure planning
   
3. **Open Source Development**:
   - Contributing to this project
   - Creating derivative tools
   - Sharing methodologies

4. **Visualization and Analysis**:
   - Creating maps and visualizations
   - Statistical analysis
   - Machine learning research
   - Unreal Engine applications

### Citation in Publications

When using Unreal Miner in research, cite as:

```bibtex
@software{unreal_miner_2024,
  author = {Kadiri, Usman Alex},
  title = {Unreal Miner: SAR Satellite Data to Unreal Engine for Virtual Mineral Exploration},
  year = {2024},
  url = {https://github.com/ussyberry/Unreal-Miner},
  note = {Contains modified Copernicus Sentinel data}
}
```

Additionally cite:
- Copernicus Sentinel data
- SNAP Toolbox
- Relevant scientific papers

---

## Prohibited Use

### ❌ NOT Permitted

1. **Illegal Activities**:
   - Unauthorized land access
   - Environmental violations
   - Trespassing
   - Any illegal mining or exploration

2. **Harmful Applications**:
   - Military targeting (without proper authorization)
   - Surveillance of individuals
   - Privacy violations
   - Discriminatory practices

3. **Terms of Service Violations**:
   - Circumventing API rate limits
   - Sharing credentials
   - Automated bulk downloads without authorization
   - Violating ESA/NASA terms

4. **Misrepresentation**:
   - Claiming ownership of Copernicus data
   - Removing attribution
   - Misrepresenting data sources
   - False accuracy claims

### Ethical Guidelines

**Do**:
- Respect indigenous land rights
- Consider environmental impact
- Follow local regulations
- Validate results with ground truth
- Acknowledge limitations

**Don't**:
- Use for unauthorized exploration
- Ignore local communities
- Make unverified claims about mineral deposits
- Skip proper permitting processes

---

## Citation Requirements

### Mandatory Citations

**In Code/Scripts**:
```python
"""
Data Source: Contains modified Copernicus Sentinel data [2024]
Processing: ESA SNAP Toolbox, GDAL
Tool: Unreal Miner (https://github.com/ussyberry/Unreal-Miner)
"""
```

**In Publications**:
- Copernicus Sentinel data (with year)
- SNAP Toolbox version
- Unreal Miner software
- Any ML models/algorithms used

**In Presentations**:
Include slide with:
- Data sources
- Processing tools
- Acknowledgments

### Sample Acknowledgments Section

```
This research used Sentinel-1 and Sentinel-2 data from the European 
Space Agency's Copernicus Programme. Processing was performed using 
the ESA SNAP Toolbox and the Unreal Miner pipeline. DEM data courtesy 
of NASA SRTM. We acknowledge the open-source geospatial community for 
GDAL, rasterio, and related tools.
```

---

## Privacy and Compliance

### Personal Data

**This project does NOT**:
- Collect personal information
- Track user activity
- Share data with third parties
- Require personal information beyond Copernicus credentials

**Copernicus Credentials**:
- Stored locally only
- Never committed to repository
- User's responsibility to protect

### GDPR Compliance

For users in EU:
- No personal data processing by Unreal Miner
- Copernicus registration subject to ESA privacy policy
- Users responsible for their own data handling

### Export Control

**Users are responsible for**:
- Compliance with export control laws
- Obtaining necessary licenses
- Following local regulations
- Respecting international sanctions

**Note**: Satellite data analysis may be subject to export controls in some jurisdictions.

---

## Data Retention

### Local Storage

**User Responsibility**:
- Manage your own data storage
- Delete data when no longer needed
- Secure sensitive results
- Follow institutional policies

**Recommendations**:
- Keep processed results, delete raw data
- Use compression for long-term storage
- Document data provenance
- Backup important results

### Cloud Storage

If using cloud storage:
- Review cloud provider's terms
- Consider data residency requirements
- Encrypt sensitive data
- Set appropriate access controls

---

## Updates to This Policy

This policy may be updated to reflect:
- Changes in data source terms
- New data providers
- Legal requirements
- Community feedback

**Version**: 1.0
**Last Updated**: 2024-01-15
**Effective Date**: 2024-01-15

---

## Questions and Contact

For questions about data usage:

- **General Questions**: Open a GitHub issue
- **Legal/Compliance**: usman.kadiri@gmail.com
- **Copernicus Data**: https://scihub.copernicus.eu/
- **ESA SNAP**: https://step.esa.int/main/

---

## Disclaimer

**IMPORTANT**: 

This software is a proof-of-concept research tool. Anomaly detection results should be:
- Validated with ground truth data
- Reviewed by qualified geologists
- Used as preliminary screening only
- NOT used as sole basis for exploration decisions

The developers assume no liability for:
- Accuracy of results
- Commercial losses
- Regulatory violations
- Misuse of the software

**Always consult qualified professionals and obtain proper permits before any exploration activities.**

---

## License Summary

| Component | License | Commercial Use | Attribution Required |
|-----------|---------|----------------|---------------------|
| Unreal Miner Code | MIT | ✅ Yes | ✅ Yes |
| Copernicus Data | Free & Open | ✅ Yes | ✅ Yes |
| SNAP Toolbox | GPL-3.0 | ✅ Yes | ✅ Yes |
| GDAL | X/MIT | ✅ Yes | ✅ Yes |
| Python Libraries | Various OSS | ✅ Yes | ✅ Yes (per library) |
| SRTM DEM | Public Domain | ✅ Yes | ⚠️  Recommended |

---

**For full legal text of licenses, see the LICENSE file and respective component documentation.**
