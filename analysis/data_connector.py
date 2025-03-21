import logging
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

class VetDataConnector:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_to_dataframe(self, vet_data: List[Dict]) -> pd.DataFrame:
        if not vet_data:
            self.logger.warning("No vet data to convert to DataFrame")
            return pd.DataFrame()
        
        standardized_records = []
        
        for vet in vet_data:
            try:
                
                record = {
                    'id': vet.get('id', ''),
                    'name': vet.get('name', ''),
                    'rating': float(vet.get('rating', 0)),
                    'review_count': int(vet.get('review_count', 0)),
                    'price': vet.get('price', '$$'),
                    'phone': vet.get('phone', ''),
                    'address': vet.get('address', ''),
                    'image_url': vet.get('image_url', ''),
                    'url': vet.get('url', ''),
                    'source': vet.get('source', 'unknown')
                }
                
                coordinates = vet.get('coordinates', {})
                record['latitude'] = coordinates.get('latitude', 0)
                record['longitude'] = coordinates.get('longitude', 0)
                record['categories'] = vet.get('categories', [])
                record['handles_exotic'] = bool(vet.get('handles_exotic', False))
                record['distance'] = float(vet.get('distance', 0))
                record['reviews'] = vet.get('reviews', [])
                record['sources'] = vet.get('sources', [vet.get('source', 'unknown')])
                standardized_records.append(record)
                
            except Exception as e:
                self.logger.error(f"Error standardizing vet data: {e}", exc_info=True)
                self.logger.debug(f"Problematic vet data: {vet}")

        try:
            df = pd.DataFrame(standardized_records)
            self.logger.info(f"Successfully converted {len(df)} vet records to DataFrame")
            return df
        except Exception as e:
            self.logger.error(f"Error creating DataFrame: {e}", exc_info=True)
            return pd.DataFrame()
    
    def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        scored_df = df.copy()
        scored_df['rating_norm'] = (scored_df['rating'] - 1) / 4
        scored_df.loc[scored_df['review_count'] < 3, 'rating_norm'] = scored_df.loc[scored_df['review_count'] < 3, 'rating_norm'] * 0.5

        if scored_df['review_count'].max() > 0:
            scored_df['review_count_norm'] = scored_df['review_count'].apply(
                lambda x: np.log1p(x) / np.log1p(scored_df['review_count'].max())
            )
        else:
            scored_df['review_count_norm'] = 0
        
        scored_df['composite_score'] = (
            0.7 * scored_df['rating_norm'] +
            0.3 * scored_df['review_count_norm']
        )

        scored_df['composite_score'] = scored_df['composite_score'].clip(0, 1)
        scored_df['recommendation_reasons'] = scored_df.apply(self._generate_recommendation_reasons, axis=1)
        
        return scored_df
        
    def _generate_recommendation_reasons(self, row: pd.Series) -> List[str]:
        reasons = []
        
        if row['rating'] >= 4.5:
            reasons.append(f"Excellent rating of {row['rating']}/5 stars")
        elif row['rating'] >= 4.0:
            reasons.append(f"Very good rating of {row['rating']}/5 stars")
        
        if row['review_count'] > 100:
            reasons.append(f"Highly reviewed with {row['review_count']} customer ratings")
        elif row['review_count'] > 50:
            reasons.append(f"Well-reviewed with {row['review_count']} customer ratings")

        if 'distance' in row and row['distance'] > 0:
            reasons.append(f"Located {row['distance']:.1f} miles from you")
        
        if row.get('handles_exotic', False):
            reasons.append("Handles exotic pets")
        
        sources = row.get('sources', [])
        if len(sources) > 1:
            reasons.append(f"Information verified across {len(sources)} different sources")

        if not reasons:
            reasons.append("Veterinary clinic in your area")
            
        return reasons
    
    def filter_by_criteria(self, df: pd.DataFrame, 
                          user_location: Optional[Tuple[float, float]] = None,
                          pet_type: Optional[str] = None,
                          price_preference: Optional[str] = None,
                          max_distance: Optional[float] = None,
                          specialties: Optional[List[str]] = None,
                          service_types: Optional[List[str]] = None,
                          facility_features: Optional[List[str]] = None,
                          business_attributes: Optional[List[str]] = None) -> pd.DataFrame:
        
        if df.empty:
            return df
            
        filtered_df = df.copy()
        if pet_type and pet_type.lower() == 'exotic':
            filtered_df = filtered_df[filtered_df['handles_exotic'] == True]
        
        if price_preference:
            filtered_df = filtered_df[
                filtered_df['price'].str.len() <= len(price_preference)
            ]
        
        if user_location and max_distance and max_distance > 0:
            if 'distance' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['distance'] <= max_distance]
            else:
                from geopy.distance import geodesic
                
                user_lat, user_lng = user_location
                
                def calculate_distance(row):
                    vet_lat = row['latitude']
                    vet_lng = row['longitude']
                    if vet_lat and vet_lng:
                        return geodesic((user_lat, user_lng), (vet_lat, vet_lng)).miles
                    return float('inf')
                
                filtered_df['distance'] = filtered_df.apply(calculate_distance, axis=1)
                filtered_df = filtered_df[filtered_df['distance'] <= max_distance]
                filtered_df = filtered_df.sort_values('distance')
        
        specialty_filter_needed = False
        if specialties and len(specialties) > 0:
            if len(specialties) == 1 and specialties[0] == 'general':
                self.logger.info("General specialty requested, showing all veterinary clinics")
            else:
                non_general_specialties = [s for s in specialties if s != 'general']
                if non_general_specialties:
                    specialty_filter_needed = True
                    specialty_filter = filtered_df['categories'].apply(
                        lambda cats: any(specialty.lower() in ' '.join(str(cat).lower() for cat in cats) 
                                      for specialty in non_general_specialties)
                        if isinstance(cats, list) else False
                    )
                    filtered_df = filtered_df[specialty_filter]
        
        if 'composite_score' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('composite_score', ascending=False)
        elif 'rating' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('rating', ascending=False)
        
        self.logger.info(f"Filtering complete: {len(filtered_df)} results after applying criteria")
        return filtered_df