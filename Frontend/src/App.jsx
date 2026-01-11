import React, { useEffect, useState } from "react";
import Scraper from "./components/Scraper";
import Results from "./components/Results";
import Analytics from "./components/Analytics";

const App = () => {
  const [activeTab, setActiveTab] = useState("scraper");
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState({
    totalProducts: 0,
    productsPerMinute: 0,
    dataCompleteness: 0,
    startTime: null,
    errors: 0,
  });

  // ✅ Auto-switch to Results tab when scraping finishes
  useEffect(() => {
    if (products.length > 0) {
      setActiveTab("results");
    }
  }, [products]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Title */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            E-commerce Product Scraper
          </h1>
          <p className="text-gray-400">
            Extract comprehensive product data from Shopify stores
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {["scraper", "results", "analytics"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeTab === tab
                  ? "bg-purple-600 text-white"
                  : "bg-slate-800 text-gray-400 hover:bg-slate-700"
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === "scraper" && (
          <Scraper
            products={products}
            setProducts={setProducts}
            stats={stats}
            setStats={setStats}
          />
        )}

        {activeTab === "results" && <Results products={products} />}

        {activeTab === "analytics" && (
          <Analytics products={products} stats={stats} />
        )}
      </div>
    </div>
  );
};

export default App;
