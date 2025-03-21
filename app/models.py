
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
import json
import os
from datetime import datetime

@dataclass
class Coordinates:
    latitude: float
    longitude: float

@dataclass
class Category:
    alias: str
    title: str

@dataclass
class Review:
    id: str
    rating: float
    text: str
    time_created: str
    user_name: str
    source: str = "unknown"
    sentiment_score: float = 0.0
    
    @classmethod
    def from_yelp_review(cls, yelp_review: Dict) -> 'Review':
        return cls(
            id=yelp_review.get('id', ''),
            rating=yelp_review.get('rating', 0.0),
            text=yelp_review.get('text', ''),
            time_created=yelp_review.get('time_created', ''),
            user_name=yelp_review.get('user', {}).get('name', 'Anonymous'),
            source="yelp"
        )
    
    @classmethod
    def from_google_review(cls, google_review: Dict) -> 'Review':
        return cls(
            id=str(google_review.get('time', '')),  
            rating=google_review.get('rating', 0.0),
            text=google_review.get('text', ''),
            time_created=datetime.fromtimestamp(
                google_review.get('time', 0)
            ).isoformat(),
            user_name=google_review.get('author_name', 'Anonymous'),
            source="google"
        )

@dataclass
class Vet:
    id: str
    name: str
    coordinates: Coordinates
    rating: float = 0.0
    review_count: int = 0
    price: str = ""
    phone: str = ""
    display_address: List[str] = field(default_factory=list)
    image_url: str = ""
    url: str = ""
    categories: List[Category] = field(default_factory=list)
    reviews: List[Review] = field(default_factory=list)
    distance: Optional[float] = None
    sentiment_score: float = 0.0
    composite_score: float = 0.0
    recommendation_reasons: List[str] = field(default_factory=list)
    handles_exotic: bool = False
    source: str = "unknown"
    
    @classmethod
    def from_yelp_data(cls, yelp_data: Dict) -> 'Vet':        
        coords = yelp_data.get('coordinates', {})
        coordinates = Coordinates(
            latitude=coords.get('latitude', 0.0),
            longitude=coords.get('longitude', 0.0)
        )

        categories = [
            Category(alias=cat.get('alias', ''), title=cat.get('title', ''))
            for cat in yelp_data.get('categories', [])
        ]
                
        reviews = [
            Review.from_yelp_review(review)
            for review in yelp_data.get('reviews', [])
        ]
        
        return cls(
            id=yelp_data.get('id', ''),
            name=yelp_data.get('name', ''),
            coordinates=coordinates,
            rating=yelp_data.get('rating', 0.0),
            review_count=yelp_data.get('review_count', 0),
            price=yelp_data.get('price', ''),
            phone=yelp_data.get('phone', ''),
            display_address=yelp_data.get('location', {}).get('display_address', []),
            image_url=yelp_data.get('image_url', ''),
            url=yelp_data.get('url', ''),
            categories=categories,
            reviews=reviews,
            distance=yelp_data.get('distance'),
            source="yelp"
        )
    
    @classmethod
    def from_google_data(cls, google_data: Dict) -> 'Vet':

        coords = google_data.get('geometry', {}).get('location', {})
        coordinates = Coordinates(
            latitude=coords.get('lat', 0.0),
            longitude=coords.get('lng', 0.0)
        )
        
        categories = [Category(alias="veterinary_care", title="Veterinarian")]
        reviews = [
            Review.from_google_review(review)
            for review in google_data.get('reviews', [])
        ]
        
        price_level = google_data.get('price_level', 2)
        price = '$' * price_level if price_level else '$$'
        
        return cls(
            id=google_data.get('place_id', ''),
            name=google_data.get('name', ''),
            coordinates=coordinates,
            rating=google_data.get('rating', 0.0),
            review_count=len(reviews),
            price=price,
            phone=google_data.get('formatted_phone_number', ''),
            display_address=[google_data.get('formatted_address', '')],
            image_url=google_data.get('photos', [{}])[0].get('photo_reference', '') if google_data.get('photos') else '',
            url=google_data.get('website', ''),
            categories=categories,
            reviews=reviews,
            source="google"
        )
    
    def to_dict(self) -> Dict:

        return {
            'id': self.id,
            'name': self.name,
            'coordinates': {
                'latitude': self.coordinates.latitude,
                'longitude': self.coordinates.longitude
            },
            'rating': self.rating,
            'review_count': self.review_count,
            'price': self.price,
            'phone': self.phone,
            'address': ' '.join(self.display_address),
            'image_url': self.image_url,
            'url': self.url,
            'categories': [cat.title for cat in self.categories],
            'reviews': [
                {
                    'id': rev.id,
                    'rating': rev.rating,
                    'text': rev.text,
                    'time_created': rev.time_created,
                    'user_name': rev.user_name,
                    'source': rev.source,
                    'sentiment_score': rev.sentiment_score
                }
                for rev in self.reviews[:3]  
            ],
            'distance': self.distance,
            'sentiment_score': self.sentiment_score,
            'composite_score': self.composite_score,
            'recommendation_reasons': self.recommendation_reasons,
            'handles_exotic': self.handles_exotic,
            'source': self.source
        }

@dataclass
class SearchResult:
    query: str
    location: str
    timestamp: str
    vets: List[Vet] = field(default_factory=list)
    
    def save_to_file(self, filename: str):
        data = {
            'query': self.query,
            'location': self.location,
            'timestamp': self.timestamp,
            'vets': [vet.to_dict() for vet in self.vets]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'SearchResult':
        with open(filename, 'r') as f:
            data = json.load(f)
        
        result = cls(
            query=data.get('query', ''),
            location=data.get('location', ''),
            timestamp=data.get('timestamp', '')
        )
        
        for vet_dict in data.get('vets', []):    
            coords = vet_dict.get('coordinates', {})
            coordinates = Coordinates(
                latitude=coords.get('latitude', 0.0),
                longitude=coords.get('longitude', 0.0)
            )
            
            categories = [
                Category(alias=cat.lower().replace(' ', '_'), title=cat)
                for cat in vet_dict.get('categories', [])
            ]
            
            reviews = []
            for rev_dict in vet_dict.get('reviews', []):
                review = Review(
                    id=rev_dict.get('id', ''),
                    rating=rev_dict.get('rating', 0.0),
                    text=rev_dict.get('text', ''),
                    time_created=rev_dict.get('time_created', ''),
                    user_name=rev_dict.get('user_name', 'Anonymous'),
                    source=rev_dict.get('source', 'unknown'),
                    sentiment_score=rev_dict.get('sentiment_score', 0.0)
                )
                reviews.append(review)
            
            vet = Vet(
                id=vet_dict.get('id', ''),
                name=vet_dict.get('name', ''),
                coordinates=coordinates,
                rating=vet_dict.get('rating', 0.0),
                review_count=vet_dict.get('review_count', 0),
                price=vet_dict.get('price', ''),
                phone=vet_dict.get('phone', ''),
                display_address=[vet_dict.get('address', '')],
                image_url=vet_dict.get('image_url', ''),
                url=vet_dict.get('url', ''),
                categories=categories,
                reviews=reviews,
                distance=vet_dict.get('distance'),
                sentiment_score=vet_dict.get('sentiment_score', 0.0),
                composite_score=vet_dict.get('composite_score', 0.0),
                recommendation_reasons=vet_dict.get('recommendation_reasons', []),
                handles_exotic=vet_dict.get('handles_exotic', False),
                source=vet_dict.get('source', 'unknown')
            )
            
            result.vets.append(vet)
        
        return result