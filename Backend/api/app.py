from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import json
import time
import pandas as pd
from datetime import datetime
import sys
import threading
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.shopify_scraper import ShopifyScraper
from scraper.utils import setup_logging, validate_url, calculate_completeness

app = Flask(__name__)
CORS(app)

# Setup folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
OUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

setup_logging(os.path.join(LOG_DIR, "api.log"))
logger = logging.getLogger(__name__)

# Store active scraping sessions
active_sessions = {}


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "✅ Backend Running", "time": datetime.now().isoformat()})


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


def run_scraping_job(session_id, url, max_products, rate_limit):
    """
    Background scraping job
    """
    try:
        logger.info(f"[{session_id}] Scraping started for {url}")

        progress_data = active_sessions[session_id]
        scraper = ShopifyScraper(url, rate_limit=rate_limit)

        def progress_callback(count, product):
            progress_data["total"] = count
            progress_data["latest_product"] = product
            progress_data["products"].append(product)

        products = scraper.scrape_products(
            max_products=max_products,
            progress_callback=progress_callback
        )

        progress_data["status"] = "completed"
        progress_data["products"] = products
        progress_data["end_time"] = time.time()

        # Metrics
        elapsed_time = progress_data["end_time"] - progress_data["start_time"]
        products_per_minute = (len(products) / elapsed_time) * 60 if elapsed_time > 0 else 0
        completeness = calculate_completeness(products)

        progress_data["metrics"] = {
            "elapsed_time_seconds": round(elapsed_time, 2),
            "products_per_minute": round(products_per_minute, 2),
            "data_completeness": completeness["overall"],
            "field_completeness": completeness["fields"],
        }

        # Save output json
        output_file = os.path.join(OUT_DIR, f"scraped_data_{session_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products, f, indent=2, ensure_ascii=False)

        progress_data["output_file"] = output_file
        logger.info(f"[{session_id}] Scraping completed. Total products: {len(products)}")

    except Exception as e:
        logger.error(f"[{session_id}] Scraping failed: {e}")
        active_sessions[session_id]["status"] = "failed"
        active_sessions[session_id]["errors"].append(str(e))
        active_sessions[session_id]["end_time"] = time.time()


@app.route("/api/scrape", methods=["POST"])
def scrape():
    """
    Start scrape in background thread (non-blocking)
    """
    try:
        data = request.json or {}
        url = data.get("url")
        max_products = int(data.get("max_products", 100))
        rate_limit = float(data.get("rate_limit", 1000)) / 1000  # ms -> sec

        # Validate URL
        if not url or not validate_url(url):
            return jsonify({"error": "Invalid URL provided"}), 400

        session_id = str(uuid.uuid4())

        # Create session object
        active_sessions[session_id] = {
            "session_id": session_id,
            "url": url,
            "total": 0,
            "products": [],
            "latest_product": None,
            "status": "running",
            "start_time": time.time(),
            "end_time": None,
            "metrics": None,
            "output_file": None,
            "errors": [],
        }

        # Start thread
        t = threading.Thread(
            target=run_scraping_job,
            args=(session_id, url, max_products, rate_limit),
            daemon=True
        )
        t.start()

        return jsonify({
            "session_id": session_id,
            "status": "running",
            "message": "Scraping started in background"
        })

    except Exception as e:
        logger.error(f"Request error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/<session_id>", methods=["GET"])
def get_progress(session_id):
    """
    Return live progress
    """
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404

    session_data = active_sessions[session_id]
    elapsed = time.time() - session_data["start_time"]
    products_per_minute = (session_data["total"] / elapsed) * 60 if elapsed > 0 else 0

    return jsonify({
        "session_id": session_id,
        "url": session_data["url"],
        "status": session_data["status"],
        "total_products": session_data["total"],
        "products_per_minute": round(products_per_minute, 2),
        "elapsed_time": round(elapsed, 2),
        "latest_product": session_data["latest_product"],
        "errors": session_data["errors"],
        "metrics": session_data["metrics"],
        "output_file": session_data["output_file"]
    })


@app.route("/api/results/<session_id>", methods=["GET"])
def get_results(session_id):
    """
    Return final scraped products after completion
    """
    if session_id not in active_sessions:
        return jsonify({"error": "Session not found"}), 404

    session_data = active_sessions[session_id]

    if session_data["status"] != "completed":
        return jsonify({"error": "Scraping not completed yet", "status": session_data["status"]}), 400

    return jsonify({
        "session_id": session_id,
        "total_products": len(session_data["products"]),
        "products": session_data["products"],
        "metrics": session_data["metrics"]
    })


@app.route("/api/export", methods=["POST"])
def export_data():
    """
    Export scraped products in json/csv/excel
    """
    try:
        data = request.json or {}
        products = data.get("products", [])
        format_type = data.get("format", "json")

        if not products:
            return jsonify({"error": "No products provided"}), 400

        timestamp = int(time.time())

        if format_type == "json":
            filename = os.path.join(OUT_DIR, f"products_{timestamp}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            return send_file(filename, as_attachment=True)

        elif format_type == "csv":
            df = pd.json_normalize(products)
            filename = os.path.join(OUT_DIR, f"products_{timestamp}.csv")
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            return send_file(filename, as_attachment=True)

        elif format_type == "excel":
            df = pd.json_normalize(products)
            filename = os.path.join(OUT_DIR, f"products_{timestamp}.xlsx")
            df.to_excel(filename, index=False, engine="openpyxl")
            return send_file(filename, as_attachment=True)

        return jsonify({"error": "Invalid format type"}), 400

    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/validate-url", methods=["POST"])
def validate_url_endpoint():
    """
    Validate if URL is scrapable + shopify check
    """
    try:
        data = request.json or {}
        url = data.get("url")

        if not url:
            return jsonify({"valid": False, "error": "No URL provided"}), 400

        if not validate_url(url):
            return jsonify({"valid": False, "error": "Invalid URL format"}), 400

        # shopify check
        try:
            import requests
            response = requests.get(f"{url}/products.json?limit=1", timeout=10)
            is_shopify = response.status_code == 200 and "products" in response.json()
        except:
            is_shopify = False

        return jsonify({
            "valid": True,
            "is_shopify": is_shopify,
            "message": "URL valid" + (" (Shopify detected)" if is_shopify else "")
        })

    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
