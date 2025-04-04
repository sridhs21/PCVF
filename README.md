# PetCare Vet Finder

A veterinary clinic search and recommendation system that aggregates data from multiple sources to help pet owners find the best vet for their needs.

![PetCare Logo](assets/images/logo.png)

## 📋 Overview

PetCare Vet Finder is a system designed to help pet owners find the ideal veterinary clinic for their pets. It aggregates data from multiple API sources and datasets, analyzes this data to provide meaningful recommendations, and presents results based on specific criteria such as location, pet type, desired services, and more.

## ✨ Key Features

- **Multi-source Data Aggregation**: Combines vet clinic data from:
  - Yelp Dataset
  - Foursquare API
  - TomTom API
  - HERE API
  
- **Intelligent Recommendations**: 
  - Scoring algorithms for clinic ranking
  - Sentiment analysis of reviews
  - Personalized recommendations based on user preferences

- **Advanced Filtering**:
  - Pet type (including exotic pet specialists)
  - Specialty services (emergency, dental, surgery, etc.)
  - Location and distance
  - Price ranges
  
- **Data Processing**:
  - Deduplication of clinics across data sources
  - Standardization of data formats
  - Composite scoring based on ratings and review counts
  
- **Web Interface**:
  - Simple search experience
  - Detailed view of recommended veterinarians

## 🛠️ Technical Architecture

### Core Components

1. **API Manager**: Interfaces with external APIs to collect vet data
2. **Data Connector**: Standardizes and processes raw data into usable formats
3. **Vet Analyzer**: Analyzes vet data for quality, categories, and other metrics
4. **Recommender**: Applies filtering criteria and generates ranked recommendations
5. **Sentiment Analyzer**: Processes review text to extract sentiment and keywords
6. **Web Application**: Flask-based interface for searching and viewing results

### Data Flow

```
External Sources → API Manager → Data Connector → DataFrame
                                                 ↓
User Input → Web App → Recommender ← Vet Analyzer
                 ↑          ↓
                 └── Results Display
```

## 🔧 Installation

### Prerequisites

- Python 3.8+
- Pip package manager
- API keys for:
  - Foursquare
  - TomTom
  - HERE
  - (Optional) Yelp dataset

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/sridhs21/PCVF.git
   cd petcare-vet-finder
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   FOURSQUARE_API_KEY=your_foursquare_key
   TOMTOM_API_KEY=your_tomtom_key
   HERE_API_KEY=your_here_key
   YELP_DATASET_PATH=path/to/yelp_dataset
   ENABLE_YELP_DATASET=True
   ```

4. Run the application:
   ```
   python run.py
   ```

## 📊 Usage

### Web Interface

1. Navigate to `http://localhost:5000` in your browser
2. Enter your location and search criteria
3. View recommendations and detailed information about each vet
4. Filter results based on your specific requirements

### API Usage

```python
# Example of using the API programmatically
from api import APIManager
from analysis import VetAnalyzer, VetRecommender

# Initialize components
api_manager = APIManager(
    foursquare_api_key='your_key',
    tomtom_api_key='your_key',
    here_api_key='your_key'
)

# Get vet data for a location
vets_data = api_manager.get_combined_data(
    location='New York, NY',
    max_results_per_source=10
)

# Process and analyze data
analyzer = VetAnalyzer()
processed_data = analyzer.process_raw_data(vets_data)

# Get recommendations
recommender = VetRecommender()
recommendations = recommender.recommend(
    df=processed_data,
    pet_type='dog',
    specialties=['dental', 'emergency'],
    max_distance=5
)

# Get detailed information
result_details = recommender.get_recommendation_details(recommendations)
```

## 🧩 Code Structure

```
petcare-vet-finder/
├── api/                      # API integration modules
│   ├── __init__.py
│   ├── api_manager.py        # Manages multiple API sources
│   ├── foursquare_api.py     # Foursquare API client
│   ├── here_api.py           # HERE API client
│   ├── tomtom_api.py         # TomTom API client
│   └── yelp_dataset.py       # Yelp dataset processor
├── analysis/                 # Data analysis modules
│   ├── __init__.py
│   ├── analyzer.py           # Vet data analysis
│   ├── data_connector.py     # Data standardization
│   ├── recommender.py        # Recommendation engine
│   └── sentiment_analyzer.py # Review sentiment analysis
├── app/                      # Web application
│   ├── __init__.py
│   ├── config.py             # Application configuration
│   ├── routes.py             # Web routes and API endpoints
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JS, and images
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── api_utils.py          # API request utilities
│   └── geocoding.py          # Location geocoding
├── .env                      # Environment variables
├── run.py                    # Application entry point
└── requirements.txt          # Dependencies
```

## 🚀 Future Enhancements

- **Mobile Application**: Native iOS and Android apps for searches
- **User Accounts**: Saved preferences and favorite vets
- **Appointment Booking**: Direct integration with vet scheduling systems
- **Pet Health Records**: Store and manage your pet's health information
- **Review System**: Allow users to submit reviews of vet experiences
- **Emergency Vet Alerts**: Notifications for nearby emergency vet services

## 📝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.