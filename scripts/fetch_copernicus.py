#!/usr/bin/env python3
"""
Unreal Miner - Copernicus Data Fetcher

Downloads satellite data from Copernicus Open Access Hub using OAuth authentication.
Supports Sentinel-1, Sentinel-2, and DEM data.

Usage:
    python scripts/fetch_copernicus.py --sensor S1 --bbox "xmin,ymin,xmax,ymax" --start-date 2024-01-01 --end-date 2024-01-31
    python scripts/fetch_copernicus.py --sensor S2 --bbox "xmin,ymin,xmax,ymax" --start-date 2024-01-01 --end-date 2024-01-31 --max-cloud 20
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
import requests
import json
from pathlib import Path
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class CopernicusFetcher:
    def __init__(self):
        # Use the new Copernicus Data Space Infrastructure
        self.base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        self.session = requests.Session()
        
        # OAuth credentials
        self.client_id = os.getenv('COPERNICUS_CLIENT_ID')
        self.client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')
        
        # Fallback credentials
        self.username = os.getenv('COPERNICUS_USER')
        self.password = os.getenv('COPERNICUS_PASSWORD')
        
        self.access_token = None
        self.token_expires = None
        
        # Authenticate
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Copernicus Open Access Hub"""
        if self.client_id and self.client_secret:
            print("Using OAuth authentication...")
            self.authenticate_oauth()
        elif self.username and self.password:
            print("Using username/password authentication...")
            self.authenticate_basic()
        else:
            raise ValueError("No valid credentials found in .env file")
    
    def authenticate_oauth(self):
        """Authenticate using OAuth client credentials for Copernicus Data Space Infrastructure"""
        # Use the new Copernicus Data Space Infrastructure endpoint
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        try:
            print(f"Trying OAuth endpoint: {token_url}")
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'cdse'
            }
            
            response = self.session.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'] - 60)
            
            # Set authorization header
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            print("OAuth authentication successful")
            return
            
        except requests.exceptions.RequestException as e:
            print(f"OAuth authentication failed: {e}")
            print("Falling back to basic authentication...")
            self.authenticate_basic()
    
    def authenticate_basic(self):
        """Authenticate using basic authentication"""
        if not self.username or not self.password:
            raise ValueError("Username/password not available for fallback authentication")
        
        self.session.auth = (self.username, self.password)
        print("Basic authentication configured")
    
    def check_token_expiry(self):
        """Check if token needs refresh"""
        if self.access_token and self.token_expires and datetime.now() >= self.token_expires:
            print("Refreshing OAuth token...")
            self.authenticate_oauth()
    
    def search_data(self, sensor, bbox, start_date, end_date, max_cloud=None):
        """Search for satellite data using OData API"""
        self.check_token_expiry()
        
        # Parse bounding box
        try:
            xmin, ymin, xmax, ymax = map(float, bbox.split(','))
        except ValueError:
            raise ValueError("Bounding box must be in format: xmin,ymin,xmax,ymax")
        
        # Build OData filter for new Copernicus Data Space Infrastructure
        platform_name = self.get_platform_name(sensor)
        
        # Create footprint filter for OData
        footprint_filter = f"geography'ST Polygon((({xmin} {ymin}, {xmax} {ymin}, {xmax} {ymax}, {xmin} {ymax}, {xmin} {ymin})))'"
        
        filters = [
            f"Name eq '{platform_name}'",
            f"ContentDate/Start ge {start_date}T00:00:00.000Z",
            f"ContentDate/Start le {end_date}T23:59:59.999Z",
            f"footprint intersect {footprint_filter}"
        ]
        
        if max_cloud and sensor == 'S2':
            filters.append(f"CloudCoverPercentage le {max_cloud}")
        
        odata_filter = " and ".join(filters)
        
        # OData query
        url = f"{self.base_url}?$filter={odata_filter}&$top=100"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('value', [])
            
            print(f"Found {len(results)} {sensor} products")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"Search failed: {e}")
            return []
    
    def get_platform_name(self, sensor):
        """Get platform name for sensor type"""
        if sensor == 'S1':
            return "Sentinel-1"
        elif sensor == 'S2':
            return "Sentinel-2"
        else:
            raise ValueError(f"Unsupported sensor: {sensor}")
    
    def download_product(self, product_id, output_dir):
        """Download a specific product"""
        self.check_token_expiry()
        
        # For OData API, we need to get the download link first
        try:
            # Get product details to find download link
            product_url = f"{self.base_url}({product_id})"
            response = self.session.get(product_url)
            response.raise_for_status()
            
            product_data = response.json()
            
            # Find the download link (usually in 'Online' resources)
            download_url = None
            for link in product_data.get('Resources', {}).get('value', []):
                if link.get('Type') == 'Online':
                    download_url = link.get('AccessURL')
                    break
            
            if not download_url:
                print(f"No download link found for product {product_id}")
                return None
            
            output_path = output_dir / f"{product_id}.zip"
            
            print(f"Downloading {product_id}...")
            
            with self.session.get(download_url, stream=True) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Show progress
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                print(f"\rProgress: {progress:.1f}%", end='')
                
                print(f"\nDownloaded: {output_path}")
                return output_path
                
        except requests.exceptions.RequestException as e:
            print(f"\nDownload failed: {e}")
            return None
    
    def fetch_data(self, sensor, bbox, start_date, end_date, output_dir, max_cloud=None):
        """Main fetch method"""
        print(f"Fetching {sensor} data...")
        print(f"Area: {bbox}")
        print(f"Date range: {start_date} to {end_date}")
        
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Search for data
        products = self.search_data(sensor, bbox, start_date, end_date, max_cloud)
        
        if not products:
            print("No products found")
            return
        
        # Download products
        downloaded_count = 0
        for product in products:
            product_id = product.get('id')
            if product_id:
                result = self.download_product(product_id, output_dir)
                if result:
                    downloaded_count += 1
                
                # Rate limiting
                time.sleep(1)
        
        print(f"\nDownload complete: {downloaded_count}/{len(products)} products downloaded")

def main():
    parser = argparse.ArgumentParser(description='Download satellite data from Copernicus')
    
    parser.add_argument('--sensor', required=True, choices=['S1', 'S2'],
                       help='Satellite sensor (S1 for Sentinel-1, S2 for Sentinel-2)')
    
    parser.add_argument('--bbox', required=True,
                       help='Bounding box in format: xmin,ymin,xmax,ymax (WGS84)')
    
    parser.add_argument('--start-date', required=True,
                       help='Start date in format: YYYY-MM-DD')
    
    parser.add_argument('--end-date', required=True,
                       help='End date in format: YYYY-MM-DD')
    
    parser.add_argument('--output-dir', default='./data/raw',
                       help='Output directory for downloaded data')
    
    parser.add_argument('--max-cloud', type=int,
                       help='Maximum cloud cover percentage (S2 only)')
    
    parser.add_argument('--limit', type=int, default=10,
                       help='Maximum number of products to download')
    
    args = parser.parse_args()
    
    try:
        fetcher = CopernicusFetcher()
        fetcher.fetch_data(
            sensor=args.sensor,
            bbox=args.bbox,
            start_date=args.start_date,
            end_date=args.end_date,
            output_dir=args.output_dir,
            max_cloud=args.max_cloud
        )
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()