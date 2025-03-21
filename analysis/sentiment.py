
import re
import nltk
from typing import Dict, List, Union, Optional
import logging

class SentimentAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        try:    
            try:
                nltk.data.find('vader_lexicon')
            except LookupError:
                nltk.download('vader_lexicon', quiet=True)
                nltk.download('punkt', quiet=True)
            
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            self.analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            self.logger.error(f"Error initializing VADER sentiment analyzer: {e}")
            self.analyzer = None
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        if not text or not self.analyzer:
            return {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
            
        cleaned_text = self._clean_text(text)
        if not cleaned_text:
            return {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
            
        try:
            return self.analyzer.polarity_scores(cleaned_text)
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0}
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
            
        text = str(text)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_reviews(self, reviews: List[Dict]) -> Dict:
        
        if not reviews:
            return {
                'average': {'neg': 0.0, 'neu': 1.0, 'pos': 0.0, 'compound': 0.0},
                'distribution': {'positive': 0, 'neutral': 100, 'negative': 0},
                'review_sentiments': []
            }
        
        review_sentiments = []
        for review in reviews:
            text = review.get('text', '')
            sentiment = self.analyze_text(text)
            review_sentiments.append({
                'review_id': review.get('id', ''),
                'sentiment': sentiment,
                'category': self._categorize_sentiment(sentiment['compound'])
            })
        
        avg_neg = sum(s['sentiment']['neg'] for s in review_sentiments) / len(review_sentiments)
        avg_neu = sum(s['sentiment']['neu'] for s in review_sentiments) / len(review_sentiments)
        avg_pos = sum(s['sentiment']['pos'] for s in review_sentiments) / len(review_sentiments)
        avg_compound = sum(s['sentiment']['compound'] for s in review_sentiments) / len(review_sentiments)
        
        categories = [s['category'] for s in review_sentiments]
        positive_pct = (categories.count('positive') / len(categories)) * 100
        neutral_pct = (categories.count('neutral') / len(categories)) * 100
        negative_pct = (categories.count('negative') / len(categories)) * 100
        
        return {
            'average': {
                'neg': avg_neg,
                'neu': avg_neu,
                'pos': avg_pos,
                'compound': avg_compound
            },
            'distribution': {
                'positive': positive_pct,
                'neutral': neutral_pct,
                'negative': negative_pct
            },
            'review_sentiments': review_sentiments
        }
    
    def _categorize_sentiment(self, compound_score: float) -> str:
        if compound_score >= 0.05:
            return 'positive'
        elif compound_score <= -0.05:
            return 'negative'
        else:
            return 'neutral'
            
    def extract_pet_keywords(self, text: str) -> List[str]:
        if not text:
            return []
        
        
        pet_keywords = {
            'dog': ['dog', 'puppy', 'puppies', 'canine', 'k9', 'pooch', 'doggy', 'hound', 'pup'],
            'cat': ['cat', 'kitten', 'kitty', 'feline', 'tabby', 'tomcat'],
            'bird': ['bird', 'parrot', 'parakeet', 'budgie', 'finch', 'canary', 'avian', 'feathered'],
            'exotic': ['exotic', 'reptile', 'snake', 'lizard', 'turtle', 'hamster', 'gerbil', 'rabbit', 
                      'guinea pig', 'ferret', 'rat', 'mouse', 'hedgehog', 'chinchilla', 'bearded dragon',
                      'iguana', 'chameleon', 'gecko', 'tortoise', 'frog', 'toad', 'newt', 'salamander']
        }
        
        text_lower = text.lower()  
        found_keywords = []
        for pet_type, keywords in pet_keywords.items():
            for keyword in keywords:
                
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    if pet_type not in found_keywords:
                        found_keywords.append(pet_type)
        
        return found_keywords
    
    def extract_specialty_keywords(self, text: str) -> List[str]:
        if not text:
            return []
        
        specialty_keywords = {
            'emergency': ['emergency', 'urgent', 'critical', 'after hours', 'crisis', 'accident', 'trauma'],
            'surgery': ['surgery', 'surgical', 'operation', 'procedure', 'incision', 'anesthesia'],
            'dental': ['dental', 'teeth', 'tooth', 'gum', 'oral', 'mouth', 'dentistry'],
            'dermatology': ['skin', 'allergies', 'itching', 'scratching', 'dermatology', 'rash', 'allergy'],
            'oncology': ['cancer', 'tumor', 'oncology', 'mass', 'growth', 'chemotherapy', 'radiation'],
            'cardiology': ['heart', 'cardiac', 'murmur', 'cardiology', 'cardiovascular'],
            'neurology': ['seizure', 'neurological', 'spine', 'brain', 'nerve', 'seizures', 'paralysis'],
            'orthopedic': ['bone', 'joint', 'fracture', 'hip', 'leg', 'limp', 'orthopedic', 'lameness'],
            'behavior': ['behavior', 'training', 'anxiety', 'aggression', 'behavioral'],
            'holistic': ['holistic', 'alternative', 'acupuncture', 'herbal', 'homeopathy', 'natural']
        }
        
        text_lower = text.lower()
        found_specialties = []
        for specialty, keywords in specialty_keywords.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    if specialty not in found_specialties:
                        found_specialties.append(specialty)
        
        return found_specialties
    
    def analyze_vet_sentiment_by_pet_type(self, reviews: List[Dict]) -> Dict[str, Dict]:
        if not reviews:
            return {}
            
        pet_types = ['dog', 'cat', 'bird', 'exotic']
        results = {}
        
        for pet_type in pet_types:
            relevant_reviews = []
            for review in reviews:
                text = review.get('text', '')
                if not text:
                    continue
                    
                extracted_types = self.extract_pet_keywords(text)
                if pet_type in extracted_types:
                    relevant_reviews.append(review)
            
            if relevant_reviews:
                results[pet_type] = self.analyze_reviews(relevant_reviews)
            else:
                results[pet_type] = None
                
        return results