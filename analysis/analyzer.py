import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from .data_connector import VetDataConnector

class VetAnalyzer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_connector = VetDataConnector()
    
    def process_raw_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        self.logger.info(f"Processing {len(raw_data)} raw vet records")
        df = self.data_connector.convert_to_dataframe(raw_data)
        
        if not df.empty:
            self.logger.info(f"Processed DataFrame has {len(df)} rows and {len(df.columns)} columns")
            source_counts = df['source'].value_counts().to_dict()
            self.logger.info(f"Data sources distribution: {source_counts}")
            if 'rating' in df.columns:
                avg_rating = df['rating'].mean()
                rating_null = df['rating'].isna().sum()
                self.logger.info(f"Average rating: {avg_rating:.2f}, Missing ratings: {rating_null}")
        else:
            self.logger.warning("Processed DataFrame is empty")
            
        return df
    
    def calculate_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info("Calculating composite scores")
        scored_df = self.data_connector.calculate_composite_score(df)
        
        if 'composite_score' in scored_df.columns:
            avg_score = scored_df['composite_score'].mean()
            max_score = scored_df['composite_score'].max()
            min_score = scored_df['composite_score'].min()
            self.logger.info(f"Composite scores - Avg: {avg_score:.3f}, Min: {min_score:.3f}, Max: {max_score:.3f}")
        
        return scored_df
    
    def analyze_categories(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or 'categories' not in df.columns:
            return {'category_count': 0}
        
        all_categories = []
        for cat_list in df['categories'].dropna():
            if isinstance(cat_list, list):
                all_categories.extend([c.lower() if isinstance(c, str) else c for c in cat_list])
        
        from collections import Counter
        category_counts = Counter(all_categories)
        
        top_categories = category_counts.most_common(10)
        
        exotic_count = df['handles_exotic'].sum() if 'handles_exotic' in df.columns else 0
        exotic_percent = (exotic_count / len(df)) * 100 if len(df) > 0 else 0
        
        return {
            'category_count': len(category_counts),
            'top_categories': top_categories,
            'exotic_count': exotic_count,
            'exotic_percent': exotic_percent
        }
    
    def get_data_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {'quality_score': 0, 'completeness': 0}
        
        key_fields = ['name', 'rating', 'phone', 'address', 'latitude', 'longitude']
        completeness = {}
        
        for field in key_fields:
            if field in df.columns:
                non_empty = df[field].notna().sum()
                completeness[field] = (non_empty / len(df)) * 100
            else:
                completeness[field] = 0
        
        avg_completeness = sum(completeness.values()) / len(completeness)
        has_reviews = 'reviews' in df.columns
        review_count = 0
        
        if has_reviews:
            review_count = sum(len(reviews) if isinstance(reviews, list) else 0 
                             for reviews in df['reviews'])
        
        return {
            'quality_score': avg_completeness / 100,
            'completeness': completeness,
            'review_count': review_count,
            'avg_reviews_per_vet': review_count / len(df) if len(df) > 0 else 0
        }