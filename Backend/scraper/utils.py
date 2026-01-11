import time
import logging
import validators
from typing import Optional
from functools import wraps


def setup_logging(log_file: str = 'logs/scraper.log', level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def validate_url(url: str) -> bool:
    """Validate if URL is valid"""
    return validators.url(url) is True


class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_request = 0
    
    def wait(self):
        """Wait appropriate time before next request"""
        current_time = time.time()
        time_since_last = current_time - self.last_request
        
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        
        self.last_request = time.time()


def retry_on_failure(max_retries: int = 3, delay: float = 2.0):
    """Decorator to retry function on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def calculate_completeness(products: list) -> dict:
    """Calculate data completeness metrics"""
    if not products:
        return {'overall': 0, 'fields': {}}
    
    essential_fields = [
        'product_name', 'product_url', 'current_price', 'sku',
        'availability', 'short_description', 'long_description', 'images'
    ]
    
    field_stats = {}
    for field in essential_fields:
        filled = sum(1 for p in products if p.get(field) and p[field] != 'N/A')
        field_stats[field] = round((filled / len(products)) * 100, 2)
    
    overall = round(sum(field_stats.values()) / len(field_stats), 2)
    
    return {
        'overall': overall,
        'fields': field_stats,
        'total_products': len(products)
    }