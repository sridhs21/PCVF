import scrapy
import re
import json
from datetime import datetime
from urllib.parse import urljoin, quote
from .base_spider import BaseVetSpider

class YelpVetSpider(BaseVetSpider):
    name = "yelp_vet_spider"
    allowed_domains = ["yelp.com"]

    def __init__(self, location=None, *args, **kwargs):
        super(YelpVetSpider, self).__init__(location, *args, **kwargs)

        location_param = quote(self.location)
        self.start_urls = [
            f"https://www.yelp.com/search?find_desc=Veterinarians&find_loc={location_param}"
        ]

        self.results = []

    def parse(self, response):
        #parse the search results page

        business_listings = response.css('div.businessName__09f24__RAYQ2')

        self.logger.info(f"Found {len(business_listings)} business listings on page")

        if not business_listings:

            business_listings = response.css('div[data-testid="serp-ia-card"]')

            if not business_listings:
                self.logger.warning("Business listings not found. Yelp may have changed their HTML structure.")

                with open('yelp_debug.html', 'w') as f:
                    f.write(response.text)

        for business in business_listings:

            name = business.css('a.css-19v1rkv::text').get()
            if not name:
                name = business.css('span.css-1egxyvc::text').get()

            business_url = business.css('a.css-19v1rkv::attr(href)').get()
            if business_url:
                full_url = urljoin(response.url, business_url)
                yield scrapy.Request(full_url, callback=self.parse_business_page,
                                   meta={'name': name})

        next_page = response.css('a.next-link::attr(href)').get()
        if not next_page:
            next_page = response.css('a[aria-label="Next page"]::attr(href)').get()

        if next_page:
            next_url = urljoin(response.url, next_page)
            self.logger.info(f"Following next page: {next_url}")
            yield scrapy.Request(next_url, callback=self.parse)
        else:
            self.logger.info("No more pages to follow")
            self.save_results(self.results)

    def parse_business_page(self, response):
        #parse individual business page
        business_name = response.meta.get('name')

        if not business_name:
            business_name = response.css('h1.css-1se8maq::text').get()

        self.logger.info(f"Parsing business page for: {business_name}")

        rating_text = response.css('div[aria-label*="star rating"]::attr(aria-label)').get()
        rating = self.extract_rating(rating_text)

        review_count_text = response.css('a[href*="reviews"] span::text').get()
        if review_count_text:
            review_count = re.search(r'(\d+)', review_count_text)
            review_count = int(review_count.group(1)) if review_count else 0
        else:
            review_count = 0

        address_elements = response.css('address p::text').getall()
        address = ', '.join([self.clean_text(elem) for elem in address_elements]) if address_elements else None

        phone = response.css('p[data-testid="phone-number"]::text').get()
        phone = self.clean_text(phone) if phone else None

        website = response.css('a[href*="biz_redir"]::attr(href)').get()
        if website:
            website = re.search(r'url=(.*?)&', website)
            website = website.group(1) if website else None

        services = response.css('span.css-1fdy0l5::text').getall()
        services = [self.clean_text(service) for service in services] if services else []

        reviews = []
        review_elements = response.css('div.review__09f24__oHr9V')

        for review_element in review_elements:
            reviewer_name = review_element.css('a.css-19v1rkv::text').get()

            review_rating_elem = review_element.css('div[aria-label*="star rating"]::attr(aria-label)').get()
            review_rating = self.extract_rating(review_rating_elem)

            date_text = review_element.css('span.css-chan6m::text').get()
            date = None
            if date_text:
                try:
                    date = datetime.strptime(date_text.strip(), '%m/%d/%Y')
                    date = date.strftime('%Y-%m-%d')
                except ValueError:
                    date = date_text.strip()

            content = ' '.join(review_element.css('span.css-16lklrv span::text').getall())
            content = self.clean_text(content)

            if content and reviewer_name:  
                reviews.append({
                    'reviewer': reviewer_name,
                    'rating': review_rating,
                    'date': date,
                    'content': content
                })

        result = {
            'name': business_name,
            'rating': rating,
            'review_count': review_count,
            'address': address,
            'phone': phone,
            'website': website,
            'services': services,
            'reviews': reviews,
            'source': 'yelp',
            'url': response.url,
            'location': self.location,
            'scraped_at': self.get_current_time()
        }

        self.results.append(result)

        next_review_page = response.css('a.next-link::attr(href)').get()
        if not next_review_page:
            next_review_page = response.css('a[aria-label="Next page"]::attr(href)').get()

        if next_review_page and len(reviews) > 0:  
            next_url = urljoin(response.url, next_review_page)
            self.logger.info(f"Following next review page for {business_name}: {next_url}")
            yield scrapy.Request(
                next_url, 
                callback=self.parse_more_reviews,
                meta={'business_index': len(self.results) - 1}
            )

    def parse_more_reviews(self, response):
        #parse additional review pages
        business_index = response.meta.get('business_index')
        business_name = self.results[business_index]['name']

        self.logger.info(f"Parsing additional reviews for: {business_name}")

        review_elements = response.css('div.review__09f24__oHr9V')

        for review_element in review_elements:
            reviewer_name = review_element.css('a.css-19v1rkv::text').get()

            review_rating_elem = review_element.css('div[aria-label*="star rating"]::attr(aria-label)').get()
            review_rating = self.extract_rating(review_rating_elem)

            date_text = review_element.css('span.css-chan6m::text').get()
            date = None
            if date_text:
                try:
                    date = datetime.strptime(date_text.strip(), '%m/%d/%Y')
                    date = date.strftime('%Y-%m-%d')
                except ValueError:
                    date = date_text.strip()

            content = ' '.join(review_element.css('span.css-16lklrv span::text').getall())
            content = self.clean_text(content)

            if content and reviewer_name:  
                self.results[business_index]['reviews'].append({
                    'reviewer': reviewer_name,
                    'rating': review_rating,
                    'date': date,
                    'content': content
                })

        next_review_page = response.css('a.next-link::attr(href)').get()
        if not next_review_page:
            next_review_page = response.css('a[aria-label="Next page"]::attr(href)').get()

        if next_review_page:
            next_url = urljoin(response.url, next_review_page)
            self.logger.info(f"Following next review page for {business_name}: {next_url}")
            yield scrapy.Request(
                next_url, 
                callback=self.parse_more_reviews,
                meta={'business_index': business_index}
            )
        else:

            self.save_results(self.results)