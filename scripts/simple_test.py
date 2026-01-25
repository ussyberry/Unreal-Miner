#!/usr/bin/env python3
"""
Simple connectivity test for Copernicus APIs
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_connectivity():
    """Test basic connectivity to Copernicus APIs"""
    print("Testing Copernicus API connectivity...")
    
    # Test URLs
    test_urls = [
        "https://scihub.copernicus.eu/dhus/search?q=*",
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    ]
    
    for url in test_urls:
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Connection successful")
                if "catalogue.dataspace.copernicus.eu" in url:
                    # Try to get some basic data
                    data = response.json()
                    print(f"Response type: {type(data)}")
                    if isinstance(data, dict) and 'value' in data:
                        print(f"Found {len(data['value'])} products in listing")
            else:
                print(f"✗ Connection failed: {response.text[:100]}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Test OAuth with our credentials
    print(f"\n\nTesting OAuth authentication...")
    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')
    
    if client_id and client_secret:
        print(f"Client ID: {client_id[:20]}...")
        
        # Try the new OAuth endpoint
        token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'cdse-scihub'
        }
        
        try:
            response = requests.post(token_url, data=payload, timeout=30)
            print(f"OAuth status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                print("✓ OAuth authentication successful!")
                print(f"Token expires in: {token_data.get('expires_in', 'unknown')} seconds")
                return True
            else:
                print(f"OAuth failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"OAuth error: {e}")
    else:
        print("No OAuth credentials found")
    
    return False

if __name__ == '__main__':
    test_connectivity()