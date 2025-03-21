import os
import json
import pandas as pd
import logging
from typing import Dict, List, Optional, Union
import gzip
from datetime import datetime

class YelpDatasetProcessor:
    
    def __init__(self, dataset_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.dataset_path = dataset_path or os.getenv("YELP_DATASET_PATH")
        
        if self.dataset_path:
            if not os.path.isabs(self.dataset_path):        
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.dataset_path = os.path.join(base_dir, self.dataset_path.lstrip('/\\'))
                self.logger.info(f"Using Yelp dataset path: {self.dataset_path}")
        
        if not self.dataset_path or not os.path.exists(self.dataset_path):    
            potential_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'yelp_dataset'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'yelp_dataset'),
                os.path.join(os.path.expanduser('~'), 'yelp_dataset')
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    self.dataset_path = path
                    self.logger.info(f"Found Yelp dataset at fallback location: {path}")
                    break
        
        if not self.dataset_path or not os.path.exists(self.dataset_path):
            self.logger.error(f"Yelp dataset path not found: {self.dataset_path}")
            raise ValueError("Valid Yelp dataset path is required.")
        
        self.business_file = os.path.join(self.dataset_path, "yelp_academic_dataset_business.json")
        if not os.path.exists(self.business_file):    
            alt_paths = [
                os.path.join(self.dataset_path, "business.json"),
                os.path.join(self.dataset_path, "yelp_business.json"),
                os.path.join(self.dataset_path, "raw", "yelp_academic_dataset_business.json")
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    self.business_file = path
                    self.logger.info(f"Found business file at: {path}")
                    break
        
        self.review_file = os.path.join(self.dataset_path, "yelp_academic_dataset_review.json")
        if not os.path.exists(self.review_file):
            alt_paths = [
                os.path.join(self.dataset_path, "review.json"),
                os.path.join(self.dataset_path, "yelp_review.json"),
                os.path.join(self.dataset_path, "raw", "yelp_academic_dataset_review.json")
            ]
            for path in alt_paths:
                if os.path.exists(path):
                    self.review_file = path
                    self.logger.info(f"Found review file at: {path}")
                    break
        
        if not os.path.exists(self.business_file):
            self.logger.error(f"Business file not found at {self.business_file}")
            raise ValueError(f"Business file not found at {self.business_file}")
        if not os.path.exists(self.review_file):
            self.logger.error(f"Review file not found at {self.review_file}")
            raise ValueError(f"Review file not found at {self.review_file}")
        
        self.logger = logging.getLogger(__name__)
        self.vet_businesses = None
        self.processed_data_path = os.path.join(os.path.dirname(self.dataset_path), "processed")
        os.makedirs(self.processed_data_path, exist_ok=True)
        self.vet_cache_file = os.path.join(self.processed_data_path, "vet_businesses.json")
        self.reviews_cache_file = os.path.join(self.processed_data_path, "vet_reviews.json")
    
    def _read_json_file(self, file_path: str, limit: Optional[int] = None) -> List[Dict]:
        results = []
        try:
            is_gzipped = file_path.endswith('.gz')
            if is_gzipped:
                open_func = gzip.open
                mode = 'rt'  
            else:
                open_func = open
                mode = 'r'
            
            with open_func(file_path, mode, encoding='utf-8') as f:
                count = 0
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line.strip())
                            results.append(data)
                            count += 1
                            if limit and count >= limit:
                                break
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Error decoding JSON line in {file_path}: {e}")
                            continue
            
            self.logger.info(f"Read {count} records from {file_path}")
            return results
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return []
    
    def extract_vet_businesses(self, force_refresh: bool = False) -> List[Dict]:
        if os.path.exists(self.vet_cache_file) and not force_refresh:
            try:
                with open(self.vet_cache_file, 'r', encoding='utf-8') as f:
                    self.vet_businesses = json.load(f)
                self.logger.info(f"Loaded {len(self.vet_businesses)} vet businesses from cache")
                return self.vet_businesses
            except Exception as e:
                self.logger.error(f"Error loading cached vet businesses: {e}")
        
        self.logger.info(f"Processing business file: {self.business_file}")
        all_businesses = self._read_json_file(self.business_file)
        vet_keywords = ['veterinar', 'animal hospital', 'pet clinic', 'animal clinic', 'pet hospital']
        vet_categories = ['Veterinarians', 'Pet Services', 'Animal Hospitals', 'Pet Health']
        vet_businesses = []
        
        for business in all_businesses:
            categories = business.get('categories', '')
            if not categories:
                continue
                    
            if isinstance(categories, str):
                categories = [cat.strip() for cat in categories.split(',')]
            
            is_vet = False
            if any(vc.lower() in [c.lower() for c in categories] for vc in vet_categories):
                is_vet = True
                
            if not is_vet:
                name = business.get('name', '').lower()
                if any(kw in name for kw in vet_keywords):
                    is_vet = True
            
            if is_vet:
                business['source'] = 'yelp_dataset'
                vet_businesses.append(business)
        
        self.logger.info(f"Found {len(vet_businesses)} veterinary businesses in dataset")
        
        try:
            with open(self.vet_cache_file, 'w', encoding='utf-8') as f:
                json.dump(vet_businesses, f)
            self.logger.info(f"Cached vet businesses to {self.vet_cache_file}")
        except Exception as e:
            self.logger.error(f"Error caching vet businesses: {e}")
        
        self.vet_businesses = vet_businesses
        return vet_businesses
    
    def get_reviews_for_business(self, business_id: str, limit: int = 20) -> List[Dict]:
        business_reviews_file = os.path.join(self.processed_data_path, f"reviews_{business_id}.json")
        
        if os.path.exists(business_reviews_file):
            try:
                with open(business_reviews_file, 'r', encoding='utf-8') as f:
                    reviews = json.load(f)
                return reviews[:limit]
            except Exception as e:
                self.logger.error(f"Error loading cached reviews for {business_id}: {e}")

        grep_found = False
        reviews = []
        try:
            if os.name != 'nt':  
                import subprocess
                grep_cmd = f"grep -F '\"business_id\":\"{business_id}\"' {self.review_file} | head -n {limit*2}"
                result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        try:
                            review = json.loads(line.strip())
                            reviews.append(review)
                        except json.JSONDecodeError:
                            continue
                    
                    grep_found = True
                    self.logger.info(f"Found {len(reviews)} reviews for {business_id} using grep")
        except Exception as e:
            self.logger.warning(f"Error using grep to find reviews: {e}")
            grep_found = False
        
        if not grep_found:
            self.logger.info(f"Searching review file for business ID: {business_id}")
            try:
                with open(self.review_file, 'r', encoding='utf-8') as f:
                    count = 0
                    for line in f:
                        if line.strip():
                            try:
                                review = json.loads(line.strip())
                                if review.get('business_id') == business_id:
                                    reviews.append(review)
                                    count += 1
                                    if count >= limit * 2:  
                                        break
                            except json.JSONDecodeError:
                                continue
                self.logger.info(f"Found {len(reviews)} reviews for {business_id} by scanning file")
            except Exception as e:
                self.logger.error(f"Error reading reviews for {business_id}: {e}")
                return []
        
        reviews.sort(key=lambda x: x.get('date', ''), reverse=True)
        reviews = reviews[:limit]
        
        try:
            with open(business_reviews_file, 'w', encoding='utf-8') as f:
                json.dump(reviews, f)
            self.logger.info(f"Cached {len(reviews)} reviews for {business_id}")
        except Exception as e:
            self.logger.error(f"Error caching reviews for {business_id}: {e}")
            
        return reviews
    
    def get_vets_near_location(self, location: str, radius_miles: float = 10.0) -> List[Dict]:        
        if not self.vet_businesses:
            self.extract_vet_businesses()
        
        if not self.vet_businesses:
            self.logger.warning("No veterinary businesses found in Yelp dataset")
            return []
            
        location_lower = location.lower()
        city_match = None
        state_match = None
        zip_match = None
        
        if any(part.isdigit() and len(part) == 5 for part in location_lower.split()):
            for part in location_lower.split():
                if part.isdigit() and len(part) == 5:
                    zip_match = part
                    break
        
        city_parts = location_lower.split(',')
        if city_parts:
            city_match = city_parts[0].strip()
            self.logger.info(f"Extracted city: {city_match}")
        
        results = []
        for business in self.vet_businesses:
            if not business:
                continue
                
            matched = False
            city = business.get('city', '').lower() if business.get('city') else ''
            state = business.get('state', '').lower() if business.get('state') else ''
            postal_code = business.get('postal_code', '').lower() if business.get('postal_code') else ''
            address = business.get('address', '').lower() if business.get('address') else ''
            
            if city_match and (city_match in city or city in city_match):
                self.logger.info(f"City match found: {city_match} in {city}")
                matched = True
            
            if state_match and state_match.lower() == state:
                self.logger.info(f"State match found: {state_match} == {state}")
                matched = True
            
            if zip_match and zip_match == postal_code:
                self.logger.info(f"Zip match found: {zip_match} == {postal_code}")
                matched = True
            
            if city_match and city_match in address:
                self.logger.info(f"Address match found: {city_match} in {address}")
                matched = True
            
            if matched:
                try:
                    business_id = business.get('business_id')
                    reviews = []
                    if business_id:
                        try:
                            reviews = self.get_reviews_for_business(business_id)
                        except Exception as e:
                            self.logger.error(f"Error getting reviews for {business_id}: {e}")
                    
                    business_with_reviews = business.copy()
                    business_with_reviews['reviews'] = reviews
                    formatted_business = self._format_business_data(business_with_reviews)
                    results.append(formatted_business)
                    
                except Exception as e:
                    self.logger.error(f"Error processing business: {e}")
        
        self.logger.info(f"Found {len(results)} vets near {location}")
        return results
    
    def _format_business_data(self, business: Dict) -> Dict:        
        if not business:
            self.logger.warning("Attempted to format None business data")
            return {
                "id": "",
                "name": "Unknown",
                "rating": 0,
                "coordinates": {"latitude": 0, "longitude": 0},
                "source": "yelp_dataset"
            }
            
        categories = []
        if business.get('categories'):
            if isinstance(business['categories'], str):
                cat_list = [c.strip() for c in business['categories'].split(',')]
            elif isinstance(business['categories'], list):
                cat_list = business['categories']
            else:
                cat_list = []    
            categories = [{"title": cat} for cat in cat_list if cat]
        
        reviews = []
        for review in business.get('reviews', []):
            if not review:
                continue
                    
            reviews.append({
                "id": review.get('review_id', ''),
                "rating": review.get('stars', 0),
                "text": review.get('text', ''),
                "time_created": review.get('date', ''),
                "user": {
                    "name": review.get('user_id', 'Anonymous')
                }
            })
        
        coords = {
            "latitude": business.get('latitude', 0),
            "longitude": business.get('longitude', 0)
        }
        
        address1 = business.get('address', '')
        city = business.get('city', '')
        state = business.get('state', '')
        postal = business.get('postal_code', '')
        addr2 = f"{city}, {state} {postal}" if (city or state or postal) else ""
        
        location = {
            "display_address": [
                address1,
                addr2
            ] if address1 and addr2 else [address1 or addr2 or "Unknown location"]
        }
        
        return {
            "id": business.get('business_id', ''),
            "name": business.get('name', 'Unknown'),
            "rating": business.get('stars', 0),
            "review_count": business.get('review_count', 0),
            "price": business.get('attributes', {}).get('RestaurantsPriceRange2', '$$') if business.get('attributes') else '$$',
            "phone": business.get('phone', ''),
            "location": location,
            "coordinates": coords,
            "image_url": business.get('photo_url', ''),
            "url": business.get('url', ''),
            "categories": categories,
            "reviews": reviews,
            "is_closed": not business.get('is_open', True),
            "source": "yelp_dataset",
            "handles_exotic": any('exotic' in cat['title'].lower() for cat in categories) if categories else False
        }