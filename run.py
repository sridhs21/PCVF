import os
import sys
from dotenv import load_dotenv
from app import app

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=port)