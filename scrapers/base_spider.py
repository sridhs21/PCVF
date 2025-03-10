import scrapy
import json
import os
from datetime import datetime
import logging

class BaseVetSpider(scrapy.Spider):
    #this is the base spider class that all vet review spiders should inherit from

    name = "base_vet_spider"
    allowed_domains = []
    start_urls = []

    def __init__(self, location=None, *args, **kwargs):
        super(BaseVetSpider, self).__init__(*args, **kwargs)
        self.location = location or "New York"
        self.logger.info(f"Initializing spider for location: {self.location}")

        os.makedirs("data/raw", exist_ok=True)

        self.output_file = f"data/raw/{self.name}_{self.location.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.json"

    def parse(self, response):
        #this method should be implemented by child classes
        raise NotImplementedError("Subclasses must implement parse method")

    def save_results(self, results):
        #save scraped results to a JSON file
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        self.logger.info(f"Saved {len(results)} results to {self.output_file}")

    def clean_text(self, text):
        #clean scraped text by removing extra whitespace
        if text is None:
            return ""
        return " ".join(text.strip().split())

    def extract_rating(self, rating_text):
        #extract numerical rating from text
        if not rating_text:
            return None

        import re
        match = re.search(r'(\d+(\.\d+)?)', rating_text)
        if match:
            return float(match.group(1))
        return None

    def get_current_time(self):
        #return current timestamp in ISO format
        return datetime.now().isoformat()