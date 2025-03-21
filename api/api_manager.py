import os
import logging
from typing import Dict, List, Optional, Tuple
import time
from utils.geocoding import geocode_location
import random
from datetime import datetime, timedelta
        

class APIManager:
    
    def __init__(self, 
                 foursquare_api_key: Optional[str] = None,
                 tomtom_api_key: Optional[str] = None,
                 here_api_key: Optional[str] = None,
                 yelp_dataset_path: Optional[str] = None,
                 enable_yelp_dataset: bool = True):

        self.logger = logging.getLogger(__name__)
        self.enabled_apis = []
        
        if yelp_dataset_path and enable_yelp_dataset:
            try:
                from .yelp_dataset import YelpDatasetProcessor
                self.yelp_dataset = YelpDatasetProcessor(dataset_path=yelp_dataset_path)
                self.enabled_apis.append("yelp_dataset")
                self.logger.info(f"Yelp Dataset enabled with path: {yelp_dataset_path}")
            except Exception as e:
                self.logger.warning(f"Yelp Dataset initialization failed: {e}")
        
        if foursquare_api_key:
            try:
                from .foursquare_api import FoursquareAPI
                self.foursquare_api = FoursquareAPI(api_key=foursquare_api_key)
                self.enabled_apis.append("foursquare_api")
                self.logger.info("Foursquare API enabled")
            except Exception as e:
                self.logger.warning(f"Foursquare API initialization failed: {e}")
        
        if tomtom_api_key:
            try:
                from .tomtom_api import TomTomAPI
                self.tomtom_api = TomTomAPI(api_key=tomtom_api_key)
                self.enabled_apis.append("tomtom_api")
                self.logger.info("TomTom API enabled")
            except Exception as e:
                self.logger.warning(f"TomTom API initialization failed: {e}")
        
        if here_api_key:
            try:
                from .here_api import HereAPI
                self.here_api = HereAPI(api_key=here_api_key)
                self.enabled_apis.append("here_api")
                self.logger.info("HERE API enabled")
            except Exception as e:
                self.logger.warning(f"HERE API initialization failed: {e}")
        
        if not self.enabled_apis:
            self.logger.warning("No APIs configured. Application will have limited functionality.")
    
    def get_combined_data(self, location: str, max_results_per_source: int = 10,
                         pet_type: Optional[str] = None,
                         specialties: Optional[List[str]] = None) -> List[Dict]:

        self.logger.info(f"Searching for vets near {location}")        
        try:
            lat, lng = geocode_location(location)
            location_coords = f"{lat},{lng}"
            self.logger.info(f"Geocoded {location} to coordinates: {location_coords}")
        except Exception as e:
            self.logger.warning(f"Could not geocode location: {e}")
            location_coords = None
        
        all_data = []
        successful_sources = []
         
        if "yelp_dataset" in self.enabled_apis:
            try:
                yelp_results = self.yelp_dataset.get_vets_near_location(
                    location, radius_miles=10)[:max_results_per_source]
                
                if yelp_results:
                    self.logger.info(f"Found {len(yelp_results)} results from Yelp dataset")
                    
                    for item in yelp_results:
                        item["source"] = "yelp_dataset"
                    all_data.extend(yelp_results)
                    successful_sources.append("yelp_dataset")
            except Exception as e:
                self.logger.error(f"Error getting Yelp dataset data: {e}")
        
        if "foursquare_api" in self.enabled_apis:
            try:
                foursquare_results = self.foursquare_api.get_all_vets_with_details(
                    location, max_results=max_results_per_source)
                
                if foursquare_results:
                    self.logger.info(f"Found {len(foursquare_results)} results from Foursquare API")
                    
                    for item in foursquare_results:
                        item["source"] = "foursquare_api"
                    all_data.extend(foursquare_results)
                    successful_sources.append("foursquare_api")
            except Exception as e:
                self.logger.error(f"Error getting Foursquare data: {e}")
        
        if "tomtom_api" in self.enabled_apis:
            try:
                tomtom_results = self.tomtom_api.get_all_vets_with_details(
                    location_coords or location, max_results=max_results_per_source)
                
                if tomtom_results:
                    self.logger.info(f"Found {len(tomtom_results)} results from TomTom API")
                    
                    for item in tomtom_results:
                        item["source"] = "tomtom_api"
                    all_data.extend(tomtom_results)
                    successful_sources.append("tomtom_api")
            except Exception as e:
                self.logger.error(f"Error getting TomTom data: {e}")
        
        if "here_api" in self.enabled_apis:
            try:
                here_results = self.here_api.get_all_vets_with_details(
                    location_coords or location, max_results=max_results_per_source)
                
                if here_results:
                    self.logger.info(f"Found {len(here_results)} results from HERE API")
                    
                    for item in here_results:
                        item["source"] = "here_api"
                    all_data.extend(here_results)
                    successful_sources.append("here_api")
            except Exception as e:
                self.logger.error(f"Error getting HERE data: {e}")
         
        self.logger.info(f"Retrieved data from {len(successful_sources)} sources: {', '.join(successful_sources)}")
        self.logger.info(f"Total raw results: {len(all_data)}")
        
        if not all_data:
            self.logger.warning(f"No data found from any source for {location}. Using mock data.")
            mock_data = self._get_mock_data(location, max_results=max_results_per_source)
            all_data.extend(mock_data)
        
        normalized_data = self._normalize_data_fields(all_data)   
        deduplicated_data = self._deduplicate_vet_data(normalized_data)
        self.logger.info(f"Combined and deduplicated to {len(deduplicated_data)} unique vets")
        
        return deduplicated_data
    
    def _normalize_data_fields(self, vet_data: List[Dict]) -> List[Dict]:
        normalized_results = []
        
        for vet in vet_data:
            if not vet:
                continue
                 
            normalized_vet = {
                "id": vet.get("id", ""),
                "name": vet.get("name", ""),
                "source": vet.get("source", "unknown"),
            }
            
            if "coordinates" in vet and isinstance(vet["coordinates"], dict):
                normalized_vet["coordinates"] = {
                    "latitude": vet["coordinates"].get("latitude", 0),
                    "longitude": vet["coordinates"].get("longitude", 0)
                }
            else:
                
                lat = None
                lng = None
                
                if "position" in vet:
                    lat = vet["position"].get("lat")
                    lng = vet["position"].get("lng")
                elif "geometry" in vet and "location" in vet["geometry"]:
                    lat = vet["geometry"]["location"].get("lat")
                    lng = vet["geometry"]["location"].get("lng")
                
                normalized_vet["coordinates"] = {
                    "latitude": lat or 0,
                    "longitude": lng or 0
                }
            
            if "location" in vet and isinstance(vet["location"], dict) and "display_address" in vet["location"]:
                normalized_vet["address"] = ", ".join(vet["location"]["display_address"])
            elif "address" in vet:
                normalized_vet["address"] = vet["address"]
            elif "formatted_address" in vet:
                normalized_vet["address"] = vet["formatted_address"]
            else:
                normalized_vet["address"] = ""
            
            if "rating" in vet:   
                rating = vet["rating"]
                if rating > 5:
                    rating = rating / 2
                normalized_vet["rating"] = rating
            else:
                normalized_vet["rating"] = 0
             
            normalized_vet["review_count"] = vet.get("review_count", 0)
            
            if "price" in vet:
                normalized_vet["price"] = vet["price"]
            else:
                normalized_vet["price"] = "$$"  
            
            normalized_vet["phone"] = vet.get("phone", "")
            normalized_vet["image_url"] = vet.get("image_url", "")
            normalized_vet["url"] = vet.get("url", vet.get("website", ""))
            
            categories = []
            if "categories" in vet:
                cat_list = vet["categories"]
                if isinstance(cat_list, list):
                    for cat in cat_list:
                        if isinstance(cat, dict) and "title" in cat:
                            categories.append(cat["title"])
                        elif isinstance(cat, str):
                            categories.append(cat)
                elif isinstance(cat_list, str):
                    categories = [c.strip() for c in cat_list.split(',')]
            normalized_vet["categories"] = categories
            
            if "reviews" in vet and isinstance(vet["reviews"], list):
                normalized_vet["reviews"] = vet["reviews"]
            else:
                normalized_vet["reviews"] = []
            
            exotic_keywords = ["exotic", "bird", "reptile", "avian", "amphibian", "zoo"]
            categories_text = " ".join(categories).lower()
            has_exotic = any(keyword in categories_text for keyword in exotic_keywords)
            normalized_vet["handles_exotic"] = has_exotic or vet.get("handles_exotic", False)
            
            if "distance" in vet:
                
                distance = vet["distance"]
                if distance > 100:  
                    distance = distance / 1609.34  
                normalized_vet["distance"] = round(distance, 1)
            
            normalized_results.append(normalized_vet)
        return normalized_results
    
    def _deduplicate_vet_data(self, vet_data: List[Dict]) -> List[Dict]:
        if not vet_data:
            return []
        
        vet_groups = {}
        for vet in vet_data:
            name = vet.get("name", "").lower()
            coordinates = vet.get("coordinates", {})
            latitude = coordinates.get("latitude")
            longitude = coordinates.get("longitude")
            
            if not name or not latitude or not longitude:
                continue
        
            rounded_lat = round(latitude, 4) 
            rounded_lng = round(longitude, 4)
            location_key = f"{rounded_lat},{rounded_lng}"
            name_parts = name.split()
            name_key = name
            
            if any(term in name for term in ["animal hospital", "vet", "veterinary"]):    
                simplified_name = name
                for term in ["animal", "hospital", "vet", "veterinary", "clinic", "care"]:
                    simplified_name = simplified_name.replace(term, "")
                
                simplified_name = " ".join(simplified_name.split())
                if simplified_name:  
                    name_key = simplified_name
            
            match_found = False
            for existing_key in list(vet_groups.keys()):
                existing_name, existing_location = existing_key.split("|||")
                if existing_location == location_key:    
                    if (existing_name in name_key or name_key in existing_name or
                        self._get_name_similarity(existing_name, name_key) > 0.7):
                        vet_groups[existing_key].append(vet)
                        match_found = True
                        break
            
            if not match_found:
                group_key = f"{name_key}|||{location_key}"
                vet_groups[group_key] = [vet]
        
        deduplicated_vets = []
        for group_key, vets in vet_groups.items():
            if len(vets) == 1:
                deduplicated_vets.append(vets[0])
            else:
                merged_vet = self._merge_vet_entries(vets)
                deduplicated_vets.append(merged_vet)
        
        return deduplicated_vets
    
    def _get_name_similarity(self, name1: str, name2: str) -> float:
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        common_words = {"the", "and", "of", "for", "a", "&"}
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def _merge_vet_entries(self, entries: List[Dict]) -> Dict:
        def score_entry(entry):
            score = 0
            
            if entry.get("reviews"):
                score += len(entry.get("reviews", [])) * 2
            
            for field in ["rating", "review_count", "price", "phone", "image_url", "url"]:
                if entry.get(field):
                    score += 1
            
            source_priority = {
                "yelp_dataset": 5,
                "foursquare_api": 3,
                "here_api": 2,
                "tomtom_api": 1
            }
            score += source_priority.get(entry.get("source", ""), 0)
            
            return score
        
        entries.sort(key=score_entry, reverse=True)
        base_entry = entries[0].copy()
        all_reviews = []
        all_sources = []
        
        for entry in entries:
            reviews = entry.get("reviews", [])
            if reviews:
                for review in reviews:
                    if "source" not in review and entry.get("source"):
                        review["source"] = entry.get("source")
                    all_reviews.append(review)
            
            source = entry.get("source", "unknown")
            if source and source not in all_sources:
                all_sources.append(source)    
            
            for field in ["rating", "review_count", "price", "phone", "image_url", "url"]:
                if not base_entry.get(field) and entry.get(field):
                    base_entry[field] = entry.get(field)
            
            if entry.get("categories"):
                if "categories" not in base_entry:
                    base_entry["categories"] = []
                
                for category in entry.get("categories", []):
                    if category not in base_entry["categories"]:
                        base_entry["categories"].append(category)
        
        base_entry["reviews"] = all_reviews
        base_entry["sources"] = all_sources
        
        if (not base_entry.get("review_count") or base_entry["review_count"] == 0) and all_reviews:
            base_entry["review_count"] = len(all_reviews)
        
        return base_entry
    
    def _get_mock_data(self, location: str, max_results: int = 10) -> List[Dict]:
        self.logger.info(f"Generating mock data for location: {location}")
        lat, lng = 40.7128, -74.0060  
        
        try:
            actual_lat, actual_lng = geocode_location(location)
            if actual_lat and actual_lng:
                lat, lng = actual_lat, actual_lng
                self.logger.info(f"Using actual coordinates for mock data: {lat}, {lng}")
        except Exception:
            pass
        
        location_parts = location.split(',')
        city = location_parts[0].strip() if location_parts else "Unknown City"
        mock_vets = []
        name_prefixes = ["", city + " ", "Downtown ", "Uptown ", "West ", "East ", "North ", "South "]
        name_cores = ["Animal Hospital", "Veterinary Clinic", "Pet Hospital", "Vet Center", 
                      "Animal Clinic", "Pet Care", "Animal Care", "Veterinary Hospital"]
        
        for i in range(max_results):
            prefix = random.choice(name_prefixes)
            core = random.choice(name_cores)
            name = f"{prefix}{core}"
            if prefix == "":  
                name = f"{city} {core}"
            
            vet_lat = lat + (random.random() - 0.5) * 0.02  
            vet_lng = lng + (random.random() - 0.5) * 0.02
            name_hash = sum(ord(c) for c in name) % 100  
            rating_base = 3.2 + (name_hash / 56)  
            rating = round(rating_base + random.uniform(-0.2, 0.2), 1)
            rating = min(max(rating, 3.0), 5.0)  
            review_count = int(20 + (rating - 3) * 50 + random.randint(-10, 15))
            review_count = max(5, review_count)  
            
            review_templates = [
                "Great vet clinic with caring staff. They took excellent care of our {pet}.",
                "Dr. {name} was amazing with our nervous {pet}. Highly recommended!",
                "Clean facility with professional staff. Reasonable prices for {pet} care.",
                "Been taking our {pet} here for years. They're always thorough and compassionate.",
                "The staff is so gentle with our {pet}. They make what could be a stressful visit much easier.",
                "Very knowledgeable doctors and friendly staff. Our {pet} actually enjoys going there!",
                "{pet} had surgery here last month and they did an excellent job with the follow-up care.",
                "The prices are reasonable, and they really seem to care about the animals."
            ]
            
            pet_types = ["dog", "cat", "pet", "puppy", "kitten"]
            doctor_names = ["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson", "Johnson", "Lee", "Garcia"]
            
            review_text = random.choice(review_templates)
            review_text = review_text.format(
                pet=random.choice(pet_types),
                name=random.choice(doctor_names)
            )
            
            review_rating = min(5, max(3, round(rating + random.uniform(-0.5, 0.5))))

            review = {
                "id": f"mock-review-{i}",
                "rating": review_rating,
                "text": review_text,
                "time_created": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                "user": {"name": f"MockUser{random.randint(100, 999)}"}
            }
            
            base_categories = ["Veterinarian"]
            possible_specialties = ["Animal Hospital", "Pet Care", "Emergency Vet", 
                                   "Surgery Center", "Dental Services", "Exotic Pets", 
                                   "Avian Care", "Holistic Medicine", "Pet Rehabilitation"]
            
            num_specialties = min(3, max(0, int((rating - 3) * 2)))
            if num_specialties > 0:
                specialties = random.sample(possible_specialties, num_specialties)
                base_categories.extend(specialties)
            
            if rating >= 4.7:
                price = "$$$"
            elif rating >= 4.0:
                price = "$$"
            else:
                price = "$"
                
            base_distance = random.uniform(0.5, 5.0)
            distance_adjustment = (5 - rating) / 2  
            adjusted_distance = base_distance * (1 + distance_adjustment)
            distance = round(adjusted_distance, 1)
            reasons = []
            
            if rating >= 4.7:
                reasons.append(f"Excellent rating of {rating}/5 stars")
            elif rating >= 4.3:
                reasons.append(f"Very good rating of {rating}/5 stars")
            elif rating >= 3.8:
                reasons.append(f"Good rating of {rating}/5 stars")

            if review_count > 100:
                reasons.append(f"Highly reviewed with {review_count} customer ratings")
            elif review_count > 50:
                reasons.append(f"Well-reviewed with {review_count} customer ratings")
                
            if distance <= 2.0:
                reasons.append(f"Only {distance} miles from you")
            else:
                reasons.append(f"{distance} miles from your location")
                
            if "Exotic Pets" in base_categories or "Avian Care" in base_categories:
                reasons.append("Handles exotic pets")
                
            if num_specialties > 1:
                reasons.append(f"Offers {num_specialties} specialty services")
                
            if "Emergency Vet" in base_categories:
                reasons.append("Provides emergency services")
               
            mock_vet = {
                "id": f"mock-{i}",
                "name": name,
                "coordinates": {"latitude": vet_lat, "longitude": vet_lng},
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "phone": f"+1{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}",
                "address": f"{random.randint(100, 9999)} Main St, {city}",
                "image_url": "",
                "url": f"https://example.com/{name.lower().replace(' ', '-')}",
                "categories": base_categories,
                "reviews": [review],
                "source": "mock_data",
                "handles_exotic": "Exotic Pets" in base_categories or "Avian Care" in base_categories,
                "distance": distance,
                "recommendation_reasons": reasons
            }
               
            mock_vets.append(mock_vet)
        
        return mock_vets