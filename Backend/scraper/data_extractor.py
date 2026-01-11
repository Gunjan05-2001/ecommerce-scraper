import re
from typing import Dict
from bs4 import BeautifulSoup


class DataExtractor:
    """Extract additional data fields from product descriptions and HTML"""
    
    def extract_from_description(self, html_description: str) -> Dict:
        """
        Extract structured data from product description HTML
        
        Args:
            html_description: HTML description text
            
        Returns:
            Dictionary with extracted fields
        """
        extracted = {
            'ingredients': None,
            'nutritional_info': {},
            'certifications': [],
            'features': [],
            'specifications': {},
        }
        
        if not html_description:
            return extracted
        
        soup = BeautifulSoup(html_description, 'html.parser')
        text = soup.get_text().lower()
        
        # Extract ingredients
        ingredients_match = re.search(r'ingredients?:?\s*([^\n.]+)', text, re.IGNORECASE)
        if ingredients_match:
            extracted['ingredients'] = ingredients_match.group(1).strip()
        
        # Extract certifications
        cert_keywords = ['organic', 'usda', 'fda', 'certified', 'iso', 'halal', 'kosher', 'non-gmo']
        for keyword in cert_keywords:
            if keyword in text:
                extracted['certifications'].append(keyword.upper())
        
        # Extract nutritional info (basic)
        nutrition_patterns = {
            'calories': r'(\d+)\s*cal(?:ories)?',
            'protein': r'(\d+\.?\d*)\s*g?\s*protein',
            'carbs': r'(\d+\.?\d*)\s*g?\s*carb(?:ohydrate)?s?',
            'fat': r'(\d+\.?\d*)\s*g?\s*fat',
            'fiber': r'(\d+\.?\d*)\s*g?\s*fiber',
        }
        
        for nutrient, pattern in nutrition_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['nutritional_info'][nutrient] = match.group(1)
        
        # Extract features (bullet points)
        features = []
        for li in soup.find_all('li'):
            feature = li.get_text(strip=True)
            if feature and len(feature) > 5:
                features.append(feature)
        extracted['features'] = features[:10]  # Limit to 10 features
        
        # Extract specifications from tables
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        extracted['specifications'][key] = value
        
        return extracted
    
    def extract_reviews_data(self, soup: BeautifulSoup) -> Dict:
        """Extract review data from product page HTML"""
        reviews_data = {
            'rating': None,
            'review_count': 0,
            'reviews': []
        }
        
        # Common patterns for ratings (adjust based on actual site)
        rating_patterns = [
            r'(\d+\.?\d*)\s*out of\s*5',
            r'rating[:\s]*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*stars?',
        ]
        
        page_text = soup.get_text()
        for pattern in rating_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    reviews_data['rating'] = float(match.group(1))
                    break
                except ValueError:
                    pass
        
        # Review count
        review_count_patterns = [
            r'(\d+)\s*reviews?',
            r'(\d+)\s*ratings?',
        ]
        
        for pattern in review_count_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    reviews_data['review_count'] = int(match.group(1))
                    break
                except ValueError:
                    pass
        
        return reviews_data