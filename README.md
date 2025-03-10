# PetCare Vet Finder

An application that scrapes reviews from multiple sources to find and recommend the best veterinary clinics for your pet's needs.

## Features

- **Web Scraping**: Collects reviews from popular platforms like Yelp and Google Maps
- **Sentiment Analysis**: Analyzes review text to understand customer satisfaction
- **Pet-Specific Recommendations**: Customized recommendations based on pet type (dog, cat, bird, exotic)
- **Location-Based Search**: Find the best vets in your area
- **Responsive Web Interface**: Easy-to-use application for desktop and mobile

## Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pet-vet-finder.git
   cd pet-vet-finder
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download NLTK data:
   ```python
   python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
   ```

## Usage

### Running the Application

1. Start the Flask web server:
   ```bash
   python run.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

### Collecting Fresh Data

To trigger a new scraping run for a specific location:

1. Click the "Update Data" button in the web interface, or
2. Run the following command:
   ```bash
   python -m scrapers.runner --location "New York"
   ```

### Command Line Interface

You can also use the application from the command line:

```bash
# Get top recommendations for dogs in Manhattan
python -c "from analysis.analyzer import VetReviewAnalyzer; analyzer = VetReviewAnalyzer('data/processed/vet_reviews.json'); recommendations = analyzer.get_recommendations(location='Manhattan', pet_type='dog'); print(recommendations)"
```

## How It Works

1. **Data Collection**: Web scrapers collect veterinary clinic information and reviews from multiple online sources
2. **Data Processing**: Reviews are processed and analyzed for sentiment and pet-specific content
3. **Scoring Algorithm**: Each clinic receives scores based on:
   - Overall rating
   - Review sentiment
   - Review recency
   - Specialization for specific pet types
4. **Recommendation Engine**: Users receive tailored recommendations based on their location and pet type

## Extending the Application

### Adding New Data Sources

To add a new review source:

1. Create a new spider in the `scrapers` directory
2. Implement the required parsing methods
3. Add the spider to the runner configuration

### Customizing the Scoring Algorithm

Modify the `calculate_overall_score` method in `analysis/analyzer.py` to adjust the weights of different factors.

## Legal Considerations

This application is for educational purposes only. When scraping websites:

- Always review and respect the Terms of Service of target websites
- Consider using official APIs when available
- Implement appropriate rate limiting to avoid overloading servers
- Be mindful of data privacy and copyright issues

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.