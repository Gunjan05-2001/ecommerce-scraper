const API_URL = "http://localhost:5000/api";

export const api = {
  // ✅ Start scraping (returns session_id)
  async startScrape(url, maxProducts = 100, rateLimit = 1000) {
    const response = await fetch(`${API_URL}/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        max_products: maxProducts,
        rate_limit: rateLimit,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Scraping start failed");
    }

    return data; // contains session_id
  },

  // ✅ Get scraping progress
  async getProgress(sessionId) {
    const response = await fetch(`${API_URL}/progress/${sessionId}`);

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Progress fetch failed");
    }

    return data;
  },

  // ✅ Get final results after completed
  async getResults(sessionId) {
    const response = await fetch(`${API_URL}/results/${sessionId}`);

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Results fetch failed");
    }

    return data;
  },

  // ✅ Export JSON/CSV/Excel
  async exportData(products, format = "json") {
    const response = await fetch(`${API_URL}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ products, format }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || "Export failed");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;

    // ✅ correct file extension
    if (format === "excel") a.download = "products.xlsx";
    else if (format === "csv") a.download = "products.csv";
    else a.download = "products.json";

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    window.URL.revokeObjectURL(url);
  },
};
