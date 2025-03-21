import os
import requests
import logging
import time
from typing import Dict, List, Optional, Union
from utils.api_utils import make_api_request

class FoursquareAPI:

    BASE_URL = "https://api.foursquare.com/v3"
    SEARCH_ENDPOINT = "/places/search"
    DETAILS_ENDPOINT = "/places/{}"
    PHOTOS_ENDPOINT = "/places/{}/photos"
    TIPS_ENDPOINT = "/places/{}/tips"  
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FOURSQUARE_API_KEY")
        if not self.api_key:
            raise ValueError("Foursquare API key is required. Set FOURSQUARE_API_KEY environment variable or pass as parameter.")
        
        
        self.headers = {
            "Accept": "application/json",
            "Authorization": self.api_key  
        }
        
        self.logger = logging.getLogger(__name__)
    
    def search_vets(self, location: str, radius: int = 10000, limit: int = 50) -> Dict:
        if "," in location and len(location.split(",")) == 2:
            try:
                lat, lng = map(float, location.split(","))
                
                params = {
                    "ll": f"{lat},{lng}",
                    "radius": radius,
                    "query": "veterinarian",
                    "limit": min(limit, 50),  
                    "categories": "19032",    
                    "sort": "RELEVANCE",
                    "fields": "fsq_id,name,location,geocodes,photos,hours,rating,stats,price,website,tel,categories"
                }
            except ValueError:
                
                params = {
                    "near": location,
                    "query": "veterinarian", 
                    "limit": min(limit, 50),
                    "categories": "19032",
                    "sort": "RELEVANCE",
                    "fields": "fsq_id,name,location,geocodes,photos,hours,rating,stats,price,website,tel,categories"
                }
        else:
            
            params = {
                "near": location,
                "query": "veterinarian",
                "limit": min(limit, 50),
                "categories": "19032",
                "sort": "RELEVANCE",
                "fields": "fsq_id,name,location,geocodes,photos,hours,rating,stats,price,website,tel,categories"
            }
        
        self.logger.info(f"Searching Foursquare with params: {params}")
        result = make_api_request(
            url=f"{self.BASE_URL}{self.SEARCH_ENDPOINT}",
            method="get",
            params=params,
            headers=self.headers,
            logger=self.logger
        )
        
        if "error" in result:
            self.logger.error(f"Error searching Foursquare API: {result['error']}")
            return {"error": result["error"]}
        
        return result

    def get_place_details(self, place_id: str) -> Dict:
        params = {
            "fields": "fsq_id,name,location,geocodes,photos,hours,rating,stats,price,website,tel,categories,description"
        }
        
        result = make_api_request(
            url=f"{self.BASE_URL}{self.DETAILS_ENDPOINT.format(place_id)}",
            method="get",
            params=params,
            headers=self.headers,
            logger=self.logger
        )
        
        if "error" in result:
            self.logger.error(f"Error getting place details from Foursquare API: {result['error']}")
            return {"error": result["error"]}
        
        return result

    def get_place_tips(self, place_id: str, limit: int = 20) -> Dict:

        params = {
            "limit": min(limit, 50),  
            "sort": "POPULAR"
        }
        
        result = make_api_request(
            url=f"{self.BASE_URL}{self.TIPS_ENDPOINT.format(place_id)}",
            method="get",
            params=params,
            headers=self.headers,
            logger=self.logger
        )
        
        if "error" in result:
            self.logger.error(f"Error getting place tips from Foursquare API: {result['error']}")
            return {"error": result["error"]}
        
        return result
    
    def get_all_vets_with_details(self, location: str, max_results: int = 20) -> List[Dict]:
        all_vets = []
        search_results = self.search_vets(location=location, limit=max_results)
        
        if "error" in search_results:
            self.logger.error(f"Error in Foursquare search: {search_results['error']}")
            return []
            
        places = search_results.get("results", [])
        for place in places:
            place_id = place.get("fsq_id")
            if not place_id:
                continue
            
            time.sleep(0.2)
            tips_data = self.get_place_tips(place_id)
            formatted_place = self._format_place_data(place, tips_data)
            all_vets.append(formatted_place)
            
            if len(all_vets) >= max_results:
                break
                
        return all_vets
    
    def _format_place_data(self, place: Dict, tips_data: Dict) -> Dict:
        
        geocodes = place.get("geocodes", {}).get("main", {})
        coordinates = {
            "latitude": geocodes.get("latitude", 0),
            "longitude": geocodes.get("longitude", 0)
        }        
        
        location = place.get("location", {})
        address_parts = [
            location.get("address", ""),
            location.get("locality", ""),
            location.get("region", ""),
            location.get("postcode", "")
        ]
        display_address = [part for part in address_parts if part]
        
        categories = []
        for category in place.get("categories", []):
            categories.append({"title": category.get("name", "")})
        
        photo_url = ""
        photos = place.get("photos", [])
        if photos:
            prefix = photos[0].get("prefix", "")
            suffix = photos[0].get("suffix", "")
            if prefix and suffix:
                photo_url = f"{prefix}original{suffix}"
        
        reviews = []
        for tip in tips_data.get("results", []):
            reviews.append({
                "id": tip.get("id", ""),
                "rating": place.get("rating", 0) / 2,  
                "text": tip.get("text", ""),
                "time_created": tip.get("created_at", ""),
                "user": {
                    "name": tip.get("user", {}).get("name", "Anonymous")
                }
            })
        
        price_tier = place.get("price", 0)
        price = "$" * price_tier if price_tier else "$$"
        
        return {
            "id": place.get("fsq_id", ""),
            "name": place.get("name", ""),
            "rating": place.get("rating", 0) / 2 if place.get("rating") else 0,  
            "review_count": place.get("stats", {}).get("total_tips", 0),
            "price": price,
            "phone": place.get("tel", ""),
            "location": {"display_address": display_address},
            "coordinates": coordinates,
            "image_url": photo_url,
            "url": place.get("website", ""),
            "categories": categories,
            "reviews": reviews,
            "source": "foursquare"
        }