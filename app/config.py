import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-petcare-app')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    YELP_API_KEY = os.getenv('YELP_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    FOURSQUARE_API_KEY = os.getenv('FOURSQUARE_API_KEY')
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
    HERE_API_KEY = os.getenv('HERE_API_KEY')
    BING_API_KEY = os.getenv('BING_API_KEY')
    
    YELP_DATASET_PATH = os.getenv('YELP_DATASET_PATH')
    ENABLED_DATA_SOURCES = os.getenv('ENABLED_DATA_SOURCES', 'yelp_dataset,foursquare_api,tomtom_api,here_api').split(',')
    
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = 500
    CACHE_KEY_PREFIX = 'petcare_'
    CACHE_NO_NULL_WARNING = True
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '50'))
    DEFAULT_RADIUS = int(os.getenv('DEFAULT_RADIUS', '10000'))
    
    ENABLE_YELP_DATASET = os.getenv('ENABLE_YELP_DATASET', 'False').lower() in ('true', '1', 't')
    SAVE_SEARCH_RESULTS = os.getenv('SAVE_SEARCH_RESULTS', 'True').lower() in ('true', '1', 't')
    
    @classmethod
    def ensure_directories(cls):
        os.makedirs(cls.RAW_DATA_DIR, exist_ok=True)
        os.makedirs(cls.PROCESSED_DATA_DIR, exist_ok=True)

Config.ensure_directories()