from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime
import os
import logging
import json
from api.api_manager import APIManager
from analysis.analyzer import VetAnalyzer
from analysis.recommender import VetRecommender
from app.models import SearchResult
from app import cache


main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)
api_manager = None
analyzer = None
recommender = None

def init_components():
    global api_manager, analyzer, recommender
    if api_manager is None:
        api_manager = APIManager(
            foursquare_api_key=current_app.config.get('FOURSQUARE_API_KEY'),
            tomtom_api_key=current_app.config.get('TOMTOM_API_KEY'),
            here_api_key=current_app.config.get('HERE_API_KEY'),
            yelp_dataset_path=current_app.config.get('YELP_DATASET_PATH'),
            enable_yelp_dataset=current_app.config.get('ENABLE_YELP_DATASET', False)
        )
        
    if analyzer is None:
        analyzer = VetAnalyzer()
        
    if recommender is None:
        recommender = VetRecommender()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/api/search', methods=['POST'])
def search_vets():
    init_components()
     
    data = request.json
    location = data.get('location', '')
    pet_type = data.get('pet_type')
    price_preference = data.get('price')
    max_distance = data.get('max_distance')
    specialties = data.get('specialties', [])
    logger.info(f"Search request: location={location}, pet_type={pet_type}, specialties={specialties}")
    user_lat = data.get('latitude')
    user_lng = data.get('longitude')
    user_location = (user_lat, user_lng) if user_lat and user_lng else None
    
    try:    
        all_data = api_manager.get_combined_data(
            location=location,
            max_results_per_source=15,
            pet_type=pet_type,
            specialties=specialties
        )
        
        logger.info(f"Retrieved data from {len(api_manager.enabled_apis)} sources with {len(all_data)} total results")
        if not all_data:
            return jsonify({
                'recommendations': [],
                'count': 0,
                'query': {
                    'location': location,
                    'pet_type': pet_type,
                    'price': price_preference,
                    'specialties': specialties
                },
                'data_sources': api_manager.enabled_apis,
                'timestamp': datetime.now().isoformat(),
                'message': "No veterinarians found matching your criteria. Try a different location or broaden your search."
            })
        
        processed_df = analyzer.process_raw_data(all_data)
        recommendations_df = recommender.recommend(
            df=processed_df,
            user_location=user_location,
            pet_type=pet_type,
            price_preference=price_preference,
            max_distance=max_distance,
            specialties=specialties
        )
        
        result_records = recommender.get_recommendation_details(recommendations_df)
        response = {
            'recommendations': result_records if result_records else [],
            'count': len(result_records),
            'query': {
                'location': location,
                'pet_type': pet_type,
                'price': price_preference,
                'specialties': specialties
            },
            'data_sources': api_manager.enabled_apis,
            'timestamp': datetime.now().isoformat()
        }

        if result_records:
            logger.info(f"First recommendation: {result_records[0]['name']} in {result_records[0].get('address', 'Unknown location')}")
        else:
            logger.info(f"No recommendations found for {location}")
        
        if current_app.config.get('SAVE_SEARCH_RESULTS', False):
            filename = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(current_app.config['PROCESSED_DATA_DIR'], filename)    
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response, f, default=str)
            
            logger.info(f"Saved search results to {filepath}")
            
        response_obj = jsonify(response)
        response_obj.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response_obj.headers['Pragma'] = 'no-cache'
        response_obj.headers['Expires'] = '0'
        
        return response_obj
        
    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request',
            'message': str(e),
            'count': 0,
            'recommendations': []
        }), 500

@main.route('/api/pet-specialties')
def get_specialties():
    specialties = [
        {"id": "general", "name": "General Practice", "category": "services"},
        {"id": "emergency", "name": "Emergency & Critical Care", "category": "services"},
        {"id": "surgery", "name": "Surgery", "category": "services"},
        {"id": "dental", "name": "Dental", "category": "services"},
        {"id": "dermatology", "name": "Dermatology", "category": "services"},
        {"id": "exotic", "name": "Exotic Animals", "category": "pet_type"},
        {"id": "birds", "name": "Birds", "category": "pet_type"},
        {"id": "reptiles", "name": "Reptiles", "category": "pet_type"},
        {"id": "small_mammals", "name": "Small Mammals", "category": "pet_type"}
    ]
    return jsonify(specialties)

@main.route('/api/filter-categories')
def get_filter_categories():
    categories = [
        {
            "id": "services",
            "name": "Services",
            "description": "Type of veterinary services offered"
        },
        {
            "id": "pet_type",
            "name": "Pet Types",
            "description": "Types of animals treated"
        }
    ]
    return jsonify(categories)

@main.route('/api/data-sources')
def get_data_sources():
    init_components()
    return jsonify({
        'enabled_sources': api_manager.enabled_apis
    })

@main.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    cache.clear()
    return jsonify({'status': 'Cache cleared'})