import requests
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .data_extractor import DataExtractor
from .utils import validate_url, RateLimiter

logger = logging.getLogger(__name__)


class ShopifyScraper:
    """Scraper specifically designed for Shopify-based e-commerce stores"""

    def __init__(self, base_url: str, rate_limit: float = 1.0):
        """
        Initialize the Shopify scraper

        Args:
            base_url: Base URL of the Shopify store
            rate_limit: Delay between requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = RateLimiter(rate_limit)
        self.extractor = DataExtractor()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json,text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def scrape_products(
        self,
        max_products: Optional[int] = None,
        categories: Optional[List[str]] = None,
        progress_callback=None,
    ) -> List[Dict]:
        """
        Scrape products from the Shopify store

        Args:
            max_products: Maximum number of products to scrape
            categories: Specific categories to scrape
            progress_callback: Callback function for progress updates

        Returns:
            List of product dictionaries
        """
        logger.info(f"Starting scrape of {self.base_url}")
        all_products = []

        try:
            # Use Shopify's products.json API
            page = 1
            limit = 250  # Shopify's max limit per page

            while True:
                if max_products and len(all_products) >= max_products:
                    break

                self.rate_limiter.wait()

                products_url = f"{self.base_url}/products.json?limit={limit}&page={page}"
                logger.info(f"Fetching page {page}: {products_url}")

                try:
                    response = self.session.get(products_url, timeout=30)
                    response.raise_for_status()

                    data = response.json()
                    products = data.get("products", [])

                    if not products:
                        logger.info("No more products found")
                        break

                    # Process each product
                    for product in products:
                        if max_products and len(all_products) >= max_products:
                            break

                        processed_product = self._process_product(product)
                        all_products.append(processed_product)

                        # Call progress callback
                        if progress_callback:
                            progress_callback(len(all_products), processed_product)

                    logger.info(f"Scraped {len(products)} products from page {page}")
                    page += 1

                except requests.RequestException as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    break

        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise

        logger.info(f"Scraping completed. Total products: {len(all_products)}")
        return all_products

    # ✅ NEW FUNCTION ADDED
    def _normalize_tags(self, tags):
        """Normalize tags: supports list or comma-separated string"""
        if not tags:
            return []

        # if already list
        if isinstance(tags, list):
            return [str(t).strip() for t in tags if str(t).strip()]

        # if string
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",") if t.strip()]

        return []

    def _process_product(self, product_data: Dict) -> Dict:
        """Process and enrich product data"""

        # Get first variant for pricing
        first_variant = product_data.get("variants", [{}])[0]

        # Calculate discount
        compare_price = first_variant.get("compare_at_price")
        current_price = first_variant.get("price")
        discount = 0

        if compare_price and current_price:
            try:
                compare_float = float(compare_price)
                current_float = float(current_price)
                if compare_float > current_float:
                    discount = round(
                        ((compare_float - current_float) / compare_float) * 100, 2
                    )
            except (ValueError, TypeError):
                pass

        # Process product data
        processed = {
            # Essential Fields
            "product_name": product_data.get("title", "N/A"),
            "product_url": f"{self.base_url}/products/{product_data.get('handle', '')}",
            "sku": first_variant.get("sku") or product_data.get("id", "N/A"),
            "current_price": float(current_price) if current_price else None,
            "original_price": float(compare_price) if compare_price else None,
            "discount_percentage": discount,
            "currency": "INR",  # Default, can be extracted from shop data
            "availability": "In Stock"
            if first_variant.get("available", False)
            else "Out of Stock",
            "short_description": self._clean_html(product_data.get("body_html", ""))[
                :200
            ],
            "long_description": self._clean_html(product_data.get("body_html", "")),

            # Images
            "images": [img.get("src") for img in product_data.get("images", [])],
            "featured_image": product_data.get("image", {}).get("src"),

            # Additional Fields
            "category": product_data.get("product_type", "Uncategorized"),

            # ✅ FIXED TAGS (NO MORE SPLIT ERROR)
            "tags": self._normalize_tags(product_data.get("tags")),

            "vendor": product_data.get("vendor", "N/A"),
            "product_id": product_data.get("id"),
            "handle": product_data.get("handle"),

            # Variants
            "variants": self._process_variants(product_data.get("variants", [])),
            "variant_count": len(product_data.get("variants", [])),

            # Options (size, color, etc.)
            "options": self._process_options(product_data.get("options", [])),

            # Metadata
            "created_at": product_data.get("created_at"),
            "updated_at": product_data.get("updated_at"),
            "published_at": product_data.get("published_at"),
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),

            # Additional extracted fields
            "weight": self._extract_weight(first_variant),
            "barcode": first_variant.get("barcode"),
            "requires_shipping": first_variant.get("requires_shipping", True),
            "taxable": first_variant.get("taxable", True),

            # SEO
            "meta_title": product_data.get("title"),
            "meta_description": self._clean_html(product_data.get("body_html", ""))[
                :160
            ],
        }

        # Try to extract additional fields from description
        description = product_data.get("body_html", "")
        processed.update(self.extractor.extract_from_description(description))

        return processed

    def _process_variants(self, variants: List[Dict]) -> List[Dict]:
        """Process product variants"""
        processed_variants = []
        for variant in variants:
            processed_variants.append(
                {
                    "id": variant.get("id"),
                    "title": variant.get("title"),
                    "option1": variant.get("option1"),
                    "option2": variant.get("option2"),
                    "option3": variant.get("option3"),
                    "sku": variant.get("sku"),
                    "price": float(variant.get("price")) if variant.get("price") else None,
                    "compare_at_price": float(variant.get("compare_at_price"))
                    if variant.get("compare_at_price")
                    else None,
                    "available": variant.get("available", False),
                    "inventory_quantity": variant.get("inventory_quantity"),
                    "weight": variant.get("weight"),
                    "weight_unit": variant.get("weight_unit"),
                    "barcode": variant.get("barcode"),
                }
            )
        return processed_variants

    def _process_options(self, options: List[Dict]) -> List[Dict]:
        """Process product options"""
        return [
            {"name": option.get("name"), "position": option.get("position"), "values": option.get("values", [])}
            for option in options
        ]

    def _extract_weight(self, variant: Dict) -> str:
        """Extract weight information"""
        weight = variant.get("weight")
        weight_unit = variant.get("weight_unit", "kg")
        if weight:
            return f"{weight}{weight_unit}"
        return "N/A"

    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags and clean text"""
        if not html_text:
            return ""
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())  # Remove extra whitespace

    def get_collections(self) -> List[Dict]:
        """Get all collections/categories from the store"""
        try:
            url = f"{self.base_url}/collections.json"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("collections", [])
        except Exception as e:
            logger.error(f"Error fetching collections: {e}")
            return []
