import React, { useEffect, useRef, useState } from "react";
import { Download, Play, Loader, Settings, AlertCircle } from "lucide-react";
import { api } from "../utils/api";

const Scraper = ({ products, setProducts, stats, setStats }) => {
  const [url, setUrl] = useState("https://anveshan.farm");
  const [isScrapingActive, setIsScrapingActive] = useState(false);
  const [progress, setProgress] = useState(0);
  const [config, setConfig] = useState({ maxProducts: 100, rateLimit: 1000 });
  const [showConfig, setShowConfig] = useState(false);
  const [logs, setLogs] = useState([]);

  const pollIntervalRef = useRef(null);

  const addLog = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { timestamp, message, type }]);
  };

  // Cleanup interval
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const resetStats = () => {
    const startTime = Date.now();
    setStats({
      totalProducts: 0,
      productsPerMinute: 0,
      dataCompleteness: 0,
      startTime,
      errors: 0,
    });
    return startTime;
  };

  const handleScrape = async () => {
    if (isScrapingActive) return;

    setIsScrapingActive(true);
    setProducts([]);
    setProgress(0);
    setLogs([]);

    const startTime = resetStats();

    addLog("Starting scraping via backend API...", "info");

    try {
      // ✅ 1) Start scrape -> returns session_id immediately
      const start = await api.startScrape(url, config.maxProducts, config.rateLimit);

      if (!start?.session_id) {
        throw new Error("Backend did not return a session_id");
      }

      const sessionId = start.session_id;
      addLog(`Session started: ${sessionId}`, "info");

      // ✅ 2) Poll progress every 1 sec
      pollIntervalRef.current = setInterval(async () => {
        try {
          const prog = await api.getProgress(sessionId);

          // live stats update
          setStats((prev) => ({
            ...prev,
            totalProducts: prog.total_products ?? prev.totalProducts,
            productsPerMinute: prog.products_per_minute ?? prev.productsPerMinute,
          }));

          // approximate progress %
          const percent =
            config.maxProducts > 0
              ? Math.min((prog.total_products / config.maxProducts) * 100, 99)
              : 0;

          setProgress(percent);

          // log errors if any
          if (prog.errors && prog.errors.length > 0) {
            addLog(`Warning: ${prog.errors[prog.errors.length - 1]}`, "error");
          }

          // completed
          if (prog.status === "completed") {
            clearInterval(pollIntervalRef.current);

            setProgress(100);
            addLog("Scraping completed. Fetching results...", "success");

            // ✅ 3) Fetch final results
            const final = await api.getResults(sessionId);

            setProducts(final.products || []);

            // set final metrics
            setStats({
              totalProducts: final.total_products || 0,
              productsPerMinute: final.metrics?.products_per_minute || 0,
              dataCompleteness: final.metrics?.data_completeness || 0,
              startTime,
              errors: 0,
            });

            addLog(`✓ Total products scraped: ${final.total_products}`, "success");
            addLog(
              `✓ Speed: ${final.metrics?.products_per_minute?.toFixed(2)} products/min`,
              "success"
            );
            addLog(
              `✓ Data completeness: ${final.metrics?.data_completeness?.toFixed(2)}%`,
              "success"
            );

            setIsScrapingActive(false);
          }

          // failed
          if (prog.status === "failed") {
            clearInterval(pollIntervalRef.current);
            addLog("✗ Scraping failed (check backend logs).", "error");
            setIsScrapingActive(false);
          }
        } catch (e) {
          addLog(`✗ Progress error: ${e.message}`, "error");
          setStats((prev) => ({ ...prev, errors: prev.errors + 1 }));
        }
      }, 1000);

      addLog("Live progress tracking enabled...", "info");
    } catch (error) {
      addLog(`✗ Error: ${error.message}`, "error");
      setStats((prev) => ({ ...prev, errors: prev.errors + 1 }));
      setIsScrapingActive(false);
    }
  };

  const handleExport = async (format) => {
    if (products.length === 0) {
      addLog("No data to export", "error");
      return;
    }

    try {
      await api.exportData(products, format);
      addLog(`✓ Exported ${products.length} products as ${format.toUpperCase()}`, "success");
    } catch (error) {
      addLog(`✗ Export failed: ${error.message}`, "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
        <div className="flex gap-4 mb-4">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter Shopify store URL"
            disabled={isScrapingActive}
            className="flex-1 px-4 py-3 bg-slate-900/50 border border-purple-500/30 rounded-lg focus:outline-none focus:border-purple-500"
          />
          <button
            onClick={() => setShowConfig(!showConfig)}
            className="px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg"
          >
            <Settings size={20} />
          </button>
        </div>

        {showConfig && (
          <div className="grid grid-cols-2 gap-4 mb-4 p-4 bg-slate-900/50 rounded-lg">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Max Products</label>
              <input
                type="number"
                value={config.maxProducts}
                min={1}
                onChange={(e) =>
                  setConfig({ ...config, maxProducts: parseInt(e.target.value || "1") })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-purple-500/30 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Rate Limit (ms)</label>
              <input
                type="number"
                value={config.rateLimit}
                min={100}
                onChange={(e) =>
                  setConfig({ ...config, rateLimit: parseInt(e.target.value || "1000") })
                }
                className="w-full px-3 py-2 bg-slate-800 border border-purple-500/30 rounded-lg"
              />
            </div>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleScrape}
            disabled={isScrapingActive}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg font-medium flex items-center justify-center gap-2"
          >
            {isScrapingActive ? (
              <>
                <Loader className="animate-spin" size={20} /> Scraping...
              </>
            ) : (
              <>
                <Play size={20} /> Start Scraping
              </>
            )}
          </button>

          <button
            onClick={() => handleExport("json")}
            disabled={products.length === 0}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg flex items-center gap-2"
          >
            <Download size={20} /> JSON
          </button>

          <button
            onClick={() => handleExport("csv")}
            disabled={products.length === 0}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg flex items-center gap-2"
          >
            <Download size={20} /> CSV
          </button>
        </div>

        {isScrapingActive && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-400 mb-2">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-5 border border-purple-500/20">
          <div className="text-gray-400 text-sm">Total Products</div>
          <div className="text-3xl font-bold text-purple-400">{stats.totalProducts}</div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-5 border border-purple-500/20">
          <div className="text-gray-400 text-sm">Products/Min</div>
          <div className="text-3xl font-bold text-green-400">
            {(stats.productsPerMinute || 0).toFixed(0)}
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-5 border border-purple-500/20">
          <div className="text-gray-400 text-sm">Data Quality</div>
          <div className="text-3xl font-bold text-blue-400">
            {(stats.dataCompleteness || 0).toFixed(0)}%
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-5 border border-purple-500/20">
          <div className="text-gray-400 text-sm">Errors</div>
          <div className="text-3xl font-bold text-red-400">{stats.errors}</div>
        </div>
      </div>

      {/* Logs */}
      <div className="bg-slate-800/50 rounded-2xl p-6 border border-purple-500/20">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertCircle size={20} /> Activity Log
        </h3>

        <div className="space-y-2 max-h-60 overflow-y-auto">
          {logs.slice(-12).reverse().map((log, idx) => (
            <div
              key={idx}
              className={`text-sm flex gap-3 ${
                log.type === "error"
                  ? "text-red-400"
                  : log.type === "success"
                  ? "text-green-400"
                  : "text-gray-400"
              }`}
            >
              <span className="text-gray-500">{log.timestamp}</span>
              <span>{log.message}</span>
            </div>
          ))}

          {logs.length === 0 && (
            <div className="text-gray-500 text-center py-4">No activity yet</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Scraper;
