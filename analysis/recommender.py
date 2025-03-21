import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from .data_connector import VetDataConnector

class VetRecommender:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_connector = VetDataConnector()
    
    def recommend(self, df: pd.DataFrame, user_location: Optional[Tuple[float, float]] = None,
                 pet_type: str = None, price_preference: str = None, 
                 max_distance: float = None, specialties: List[str] = None,
                 service_types: List[str] = None, facility_features: List[str] = None,
                 business_attributes: List[str] = None,
                 top_n: int = 5) -> pd.DataFrame:
        if df.empty:
            self.logger.warning("Empty DataFrame provided to recommender")
            return pd.DataFrame()
        
        self.logger.info(f"Generating recommendations with criteria: pet_type={pet_type}, "
                        f"specialties={specialties}, max_distance={max_distance}")
        
        scored_df = self.data_connector.calculate_composite_score(df)
        filtered_df = self.data_connector.filter_by_criteria(
            df=scored_df,
            user_location=user_location,
            pet_type=pet_type,
            price_preference=price_preference,
            max_distance=max_distance,
            specialties=specialties,
            service_types=service_types,
            facility_features=facility_features,
            business_attributes=business_attributes
        )
        
        if not filtered_df.empty:
            recommendations = filtered_df.head(top_n)
            self.logger.info(f"Returning {len(recommendations)} recommendations")
            return recommendations
        else:
            self.logger.warning("No vets matched the criteria after filtering")
            return pd.DataFrame()
    
    def get_recommendation_details(self, recommendations: pd.DataFrame) -> List[Dict]:
        if recommendations.empty:
            return []
        
        details = []
        
        for _, row in recommendations.iterrows():
            detail = {
                'id': row.get('id', ''),
                'name': row.get('name', ''),
                'rating': row.get('rating', 0),
                'review_count': row.get('review_count', 0),
                'price': row.get('price', '$$'),
                'phone': row.get('phone', ''),
                'address': row.get('address', ''),
                'coordinates': {
                    'latitude': row.get('latitude', 0),
                    'longitude': row.get('longitude', 0)
                },
                'image_url': row.get('image_url', ''),
                'url': row.get('url', ''),
                'distance': row.get('distance', 0),
                'composite_score': row.get('composite_score', 0),
                'handles_exotic': row.get('handles_exotic', False),
                'source': row.get('source', 'unknown'),
                'recommendation_reasons': row.get('recommendation_reasons', [])
            }
            
            
            reviews = row.get('reviews', [])
            if reviews:
                
                detail['reviews'] = reviews[:3]
            else:
                detail['reviews'] = []
            
            details.append(detail)
        
        return details