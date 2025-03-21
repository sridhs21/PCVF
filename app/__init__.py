import os
import logging
from datetime import datetime
from flask import Flask, request, g
from flask_caching import Cache
from .config import Config


cache = Cache(config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300,  
    'CACHE_THRESHOLD': 100,        
    'CACHE_KEY_PREFIX': 'petcare_'  
})

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    setup_logging(app)
    cache.init_app(app)
    logger = logging.getLogger('app')
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now().strftime('%Y%m%d%H%M%S')}
    
    @app.after_request
    def add_no_cache_headers(response):
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response
    
    from app.routes import main
    app.register_blueprint(main)
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}    
    return app

def setup_logging(app):
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('app')
    logger.setLevel(log_level)
    
    if not app.debug and not logger.handlers:    
        log_dir = os.path.join(os.path.dirname(app.instance_path), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
        
    return logger

app = create_app()