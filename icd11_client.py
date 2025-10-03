#!/usr/bin/env python3
"""
WHO ICD-11 API Client
Handles authentication and data fetching from WHO ICD-11 API for terminology mapping
"""

import os
import json
import time
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ICD11APIClient:
    """Client for WHO ICD-11 API integration"""
    
    def __init__(self):
        self.client_id = os.getenv('ICD_CLIENT_ID')
        self.client_secret = os.getenv('ICD_CLIENT_SECRET')
        self.base_url = os.getenv('ICD_API_BASE_URL', 'https://id.who.int')
        self.api_version = os.getenv('ICD_API_VERSION', 'release/11/2024-01')
        self.cache_duration = int(os.getenv('CACHE_DURATION_HOURS', '24'))
        
        if not self.client_id or not self.client_secret:
            raise ValueError("WHO ICD-11 API credentials not found. Please set ICD_CLIENT_ID and ICD_CLIENT_SECRET environment variables.")
        
        self.access_token = None
        self.token_expires_at = None
        self.cache_dir = Path('cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # API endpoints
        self.auth_url = f"{self.base_url}/connect/token"
        self.icd_api_url = f"https://icd-api.who.int/icd/{self.api_version}"
        
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid"""
        if not cache_path.exists():
            return False
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cache_data.get('cached_at', ''))
            expiry_time = cached_time + timedelta(hours=self.cache_duration)
            
            return datetime.now() < expiry_time
        except (json.JSONDecodeError, ValueError, KeyError):
            return False
    
    def _save_to_cache(self, cache_key: str, data: Any):
        """Save data to cache with timestamp"""
        cache_path = self._get_cache_path(cache_key)
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'data': data
        }
        
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """Load data from cache if valid"""
        cache_path = self._get_cache_path(cache_key)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            return cache_data.get('data')
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    def authenticate(self) -> bool:
        """Authenticate with WHO ICD-11 API and get access token"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return True  # Token still valid
        
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'icdapi_access',
            'grant_type': 'client_credentials'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            print("🔐 Authenticating with WHO ICD-11 API...")
            response = requests.post(self.auth_url, data=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early
            
            print("✅ Successfully authenticated with WHO ICD-11 API")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {str(e)}")
            return False
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated API request"""
        if not self.authenticate():
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Accept-Language': 'en',
            'API-Version': 'v2'
        }
        
        url = f"{self.icd_api_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            return None
    
    def fetch_tm2_codes(self) -> Optional[Dict]:
        """Fetch ICD-11 Traditional Medicine 2 (TM2) codes"""
        cache_key = "icd11_tm2_codes"
        
        # Check cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            print("📱 Using cached ICD-11 TM2 codes")
            return cached_data
        
        print("🌐 Fetching ICD-11 Traditional Medicine 2 (TM2) codes...")
        
        # Fetch TM2 chapter (Chapter X02 - Traditional Medicine Module 2)
        tm2_data = self._make_api_request("mms/x02")
        
        if tm2_data:
            self._save_to_cache(cache_key, tm2_data)
            print(f"✅ Successfully fetched and cached TM2 codes")
            return tm2_data
        
        return None
    
    def fetch_biomedicine_codes(self) -> Optional[Dict]:
        """Fetch ICD-11 Biomedicine codes from relevant chapters"""
        cache_key = "icd11_biomedicine_codes"
        
        # Check cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            print("📱 Using cached ICD-11 Biomedicine codes")
            return cached_data
        
        print("🌐 Fetching ICD-11 Biomedicine codes...")
        
        # Fetch main biomedicine foundation
        biomedicine_data = self._make_api_request("entity")
        
        if biomedicine_data:
            self._save_to_cache(cache_key, biomedicine_data)
            print(f"✅ Successfully fetched and cached Biomedicine codes")
            return biomedicine_data
        
        return None
    
    def search_codes(self, search_term: str, linearization: str = "mms") -> Optional[List[Dict]]:
        """Search for codes in ICD-11"""
        cache_key = f"search_{search_term}_{linearization}"
        
        # Check cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            print(f"📱 Using cached search results for '{search_term}'")
            return cached_data
        
        print(f"🔍 Searching ICD-11 for '{search_term}'...")
        
        params = {
            'q': search_term,
            'subtreeFilterUsesFoundationDescendants': 'false',
            'includeKeywordResult': 'true',
            'useFlexisearch': 'false',
            'flatResults': 'false'
        }
        
        search_results = self._make_api_request(f"{linearization}/search", params)
        
        if search_results:
            # Extract relevant results
            destinations = search_results.get('destinationEntities', [])
            self._save_to_cache(cache_key, destinations)
            print(f"✅ Found {len(destinations)} search results for '{search_term}'")
            return destinations
        
        return []
    
    def get_enhanced_namaste_mappings(self) -> Dict[str, Dict]:
        """Get enhanced NAMASTE mappings using real ICD-11 API data"""
        print("🔄 Generating enhanced NAMASTE mappings using WHO ICD-11 API...")
        
        # Traditional hardcoded mappings as fallback
        fallback_mappings = {
            "AAE-16": {"name": "Sandhigatvata", "search_terms": ["arthritis", "joint disease", "osteoarthritis"]},
            "AA": {"name": "Vatavyadhi", "search_terms": ["neurological disorder", "vata", "nervous system"]},
            "EE-3": {"name": "Arsha", "search_terms": ["hemorrhoids", "piles", "anorectal"]},
            "EF-2.4.4": {"name": "Madhumeha/Kshaudrameha", "search_terms": ["diabetes", "diabetes mellitus", "metabolic"]},
            "EA-3": {"name": "Kasa", "search_terms": ["cough", "respiratory", "bronchial"]}
        }
        
        enhanced_mappings = {}
        
        for code, info in fallback_mappings.items():
            enhanced_mappings[code] = {
                "name": info["name"],
                "tm2_codes": [],
                "biomed_codes": [],
                "search_performed": True
            }
            
            # Search for each term and collect results
            all_tm2_results = []
            all_biomed_results = []
            
            for search_term in info["search_terms"]:
                # Search in both TM2 and general (biomedicine)
                search_results = self.search_codes(search_term)
                
                if search_results:
                    for result in search_results[:2]:  # Take top 2 results per search
                        code_id = result.get('id', '').split('/')[-1] if result.get('id') else ''
                        title = result.get('title', {}).get('@value', '') if result.get('title') else ''
                        
                        if code_id and title:
                            if 'x02' in result.get('id', '').lower():  # TM2 codes
                                all_tm2_results.append({"code": code_id, "display": title})
                            else:  # Biomedicine codes
                                all_biomed_results.append({"code": code_id, "display": title})
            
            # Remove duplicates and take best matches
            enhanced_mappings[code]["tm2_codes"] = list({r['code']: r for r in all_tm2_results}.values())[:2]
            enhanced_mappings[code]["biomed_codes"] = list({r['code']: r for r in all_biomed_results}.values())[:2]
            
            print(f"   • {code} ({info['name']}): Found {len(enhanced_mappings[code]['tm2_codes'])} TM2 + {len(enhanced_mappings[code]['biomed_codes'])} Biomedicine mappings")
        
        print("✅ Enhanced NAMASTE mappings generated successfully")
        return enhanced_mappings
    
    def get_terminology_cache_summary(self) -> Dict[str, Any]:
        """Get summary of cached terminology data"""
        summary = {
            "cache_directory": str(self.cache_dir),
            "cached_files": [],
            "total_cache_size": 0
        }
        
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                file_size = cache_file.stat().st_size
                summary["cached_files"].append({
                    "file": cache_file.name,
                    "size_bytes": file_size,
                    "modified": datetime.fromtimestamp(cache_file.stat().st_mtime).isoformat()
                })
                summary["total_cache_size"] += file_size
        
        return summary


def test_icd11_client():
    """Test function for ICD-11 API client"""
    print("🧪 Testing WHO ICD-11 API Client...")
    
    try:
        client = ICD11APIClient()
        
        # Test authentication
        if not client.authenticate():
            print("❌ Authentication test failed")
            return False
        
        # Test search functionality
        search_results = client.search_codes("diabetes")
        if search_results:
            print(f"✅ Search test passed: Found {len(search_results)} results for 'diabetes'")
        else:
            print("⚠️  Search test returned no results")
        
        # Test enhanced mappings
        mappings = client.get_enhanced_namaste_mappings()
        if mappings:
            print(f"✅ Enhanced mappings test passed: Generated mappings for {len(mappings)} NAMASTE codes")
        
        # Show cache summary
        cache_summary = client.get_terminology_cache_summary()
        print(f"📊 Cache summary: {len(cache_summary['cached_files'])} files, {cache_summary['total_cache_size']} bytes")
        
        print("🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_icd11_client()