"""
eBay API Integration Module.
Provides functions to interact with eBay's Finding and Browse APIs.
"""

import requests
import json
import base64
import os
from typing import List, Dict, Optional
from datetime import datetime


class eBayAPIClient:
    """Client for interacting with eBay APIs."""
    
    # eBay API endpoints
    FINDING_API_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
    OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    BROWSE_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    
    CONFIG_FILE = "ebay_config.json"
    
    def __init__(self):
        """Initialize the eBay API client."""
        self.app_id = None
        self.cert_id = None
        self.access_token = None
        self.load_credentials()
    
    def load_credentials(self) -> bool:
        """Load eBay API credentials from config file."""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                self.app_id = config.get('app_id', '')
                
                # Decode cert_id
                encoded_cert = config.get('cert_id', '')
                if encoded_cert:
                    self.cert_id = base64.b64decode(encoded_cert).decode('utf-8')
                
                return bool(self.app_id and self.cert_id)
        except Exception as e:
            print(f"Error loading credentials: {e}")
        
        return False
    
    def get_access_token(self) -> Optional[str]:
        """Get OAuth access token for eBay API."""
        if not self.app_id or not self.cert_id:
            return None
        
        try:
            # Create authorization header
            credentials = f"{self.app_id}:{self.cert_id}"
            encoded_creds = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_creds}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(self.OAUTH_URL, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                return self.access_token
            else:
                print(f"OAuth error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def search_completed_items(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search for completed/sold items using eBay Finding API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of sold item dictionaries
        """
        if not self.app_id:
            return []
        
        try:
            params = {
                'OPERATION-NAME': 'findCompletedItems',
                'SERVICE-VERSION': '1.0.0',
                'SECURITY-APPNAME': self.app_id,
                'RESPONSE-DATA-FORMAT': 'JSON',
                'REST-PAYLOAD': '',
                'keywords': query,
                'paginationInput.entriesPerPage': str(max_results),
                'itemFilter(0).name': 'SoldItemsOnly',
                'itemFilter(0).value': 'true',
                'sortOrder': 'EndTimeSoonest'
            }
            
            response = requests.get(self.FINDING_API_URL, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                search_result = data.get('findCompletedItemsResponse', [{}])[0]
                items = search_result.get('searchResult', [{}])[0].get('item', [])
                
                # Parse and format results
                results = []
                for item in items:
                    try:
                        result = {
                            'title': item.get('title', [''])[0],
                            'price': float(item.get('sellingStatus', [{}])[0]
                                         .get('currentPrice', [{}])[0]
                                         .get('__value__', 0)),
                            'currency': item.get('sellingStatus', [{}])[0]
                                       .get('currentPrice', [{}])[0]
                                       .get('@currencyId', 'USD'),
                            'condition': item.get('condition', [{}])[0]
                                        .get('conditionDisplayName', [''])[0],
                            'sold_date': item.get('listingInfo', [{}])[0]
                                        .get('endTime', [''])[0],
                            'url': item.get('viewItemURL', [''])[0],
                            'image_url': item.get('galleryURL', [''])[0],
                            'shipping': float(item.get('shippingInfo', [{}])[0]
                                            .get('shippingServiceCost', [{}])[0]
                                            .get('__value__', 0)),
                            'source': 'eBay Sold Items'
                        }
                        results.append(result)
                    except (KeyError, IndexError, ValueError) as e:
                        continue
                
                return results
                
        except Exception as e:
            print(f"Error searching completed items: {e}")
        
        return []
    
    def search_active_listings(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search for active listings using eBay Browse API.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of active listing dictionaries
        """
        # Get access token if not already available
        if not self.access_token:
            self.get_access_token()
        
        if not self.access_token:
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            params = {
                'q': query,
                'limit': str(max_results)
            }
            
            response = requests.get(self.BROWSE_API_URL, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('itemSummaries', [])
                
                # Parse and format results
                results = []
                for item in items:
                    try:
                        result = {
                            'title': item.get('title', ''),
                            'price': float(item.get('price', {}).get('value', 0)),
                            'currency': item.get('price', {}).get('currency', 'USD'),
                            'condition': item.get('condition', ''),
                            'url': item.get('itemWebUrl', ''),
                            'image_url': item.get('image', {}).get('imageUrl', ''),
                            'seller': item.get('seller', {}).get('username', ''),
                            'location': item.get('itemLocation', {}).get('country', ''),
                            'source': 'eBay Active Listings'
                        }
                        results.append(result)
                    except (KeyError, ValueError) as e:
                        continue
                
                return results
                
            elif response.status_code == 401:
                # Token expired, try to get a new one
                self.get_access_token()
                return []
                
        except Exception as e:
            print(f"Error searching active listings: {e}")
        
        return []
    
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.app_id and self.cert_id)


def get_simulated_terapeak_data(query: str) -> List[Dict]:
    """
    Generate simulated Terapeak-style market research data.
    This is used as a fallback when eBay API is not configured.
    
    Args:
        query: Search query string
        
    Returns:
        List of simulated market data dictionaries
    """
    import random
    
    # Base conditions and their price multipliers
    conditions = {
        'New': 1.0,
        'Open box': 0.85,
        'Certified Refurbished': 0.75,
        'Used - Like New': 0.70,
        'Used - Very Good': 0.60,
        'Used - Good': 0.50,
        'Used - Acceptable': 0.40,
        'For parts or not working': 0.25
    }
    
    results = []
    base_price = random.uniform(50, 500)
    
    for condition, multiplier in conditions.items():
        avg_price = base_price * multiplier
        price_variance = avg_price * 0.15
        
        result = {
            'condition': condition,
            'avg_sold_price': round(avg_price + random.uniform(-price_variance, price_variance), 2),
            'min_price': round(avg_price * 0.7, 2),
            'max_price': round(avg_price * 1.3, 2),
            'total_sold': random.randint(50, 500),
            'sell_through_rate': round(random.uniform(0.45, 0.95), 2),
            'avg_days_to_sell': random.randint(3, 45),
            'source': 'Terapeak Simulation'
        }
        results.append(result)
    
    return results
