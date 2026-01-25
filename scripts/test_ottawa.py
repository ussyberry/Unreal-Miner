#!/usr/bin/env python3
"""
Test script to download a single satellite image of Ottawa
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ottawa central coordinates approximately
OTTAWA_BBOX = "-75.8,45.2,-75.4,45.4"  # Central Ottawa area
# Try a more recent date with better satellite coverage
DATE = "2024-08-15"

def test_download():
    """Test downloading satellite data for Ottawa"""
    print("Testing Copernicus OAuth authentication...")
    print(f"Target area: Ottawa Central")
    print(f"Date: {DATE}")
    print(f"Bounding box: {OTTAWA_BBOX}")
    print()
    
    # Check credentials
    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET not found in .env")
        return False
    
    print(f"Client ID: {client_id[:20]}...")
    print("Credentials configured ✓")
    
    # Try to import and test the fetcher
    try:
        sys.path.append('.')
        from scripts.fetch_copernicus import CopernicusFetcher
        
        print("Creating fetcher...")
        fetcher = CopernicusFetcher()
        
        print("Searching for Sentinel-2 data...")
        products = fetcher.search_data(
            sensor='S2',
            bbox=OTTAWA_BBOX,
            start_date=DATE,
            end_date=DATE,
            max_cloud=20  # Maximum 20% cloud cover
        )
        
        if products:
            print(f"Found {len(products)} products")
            
            # Download the first product
            if products:
                product_id = products[0].get('id')
                if product_id:
                    print(f"Downloading product: {product_id}")
                    
                    output_dir = Path('./data/test_ottawa')
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    result = fetcher.download_product(product_id, output_dir)
                    
                    if result:
                        print(f"Successfully downloaded: {result}")
                        print("Test completed successfully! ✓")
                        return True
                    else:
                        print("Download failed")
                        return False
        else:
            print("No products found for the specified criteria")
            print("This could be due to:")
            print("- No satellite coverage on that date")
            print("- Cloud cover restrictions")
            print("- Data availability in the archive")
            return False
            
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == '__main__':
    success = test_download()
    sys.exit(0 if success else 1)