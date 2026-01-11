import React from 'react';
import { BarChart3 } from 'lucide-react';

const Analytics = ({ products, stats }) => {
  return (
    <div className="space-y-6">
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <BarChart3 size={24} />
          Performance Analytics
        </h3>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="text-sm text-gray-400 mb-3">Data Field Coverage</h4>
            <div className="space-y-2">
              {products.length > 0 ? Object.keys(products[0]).slice(0, 10).map((field, idx) => {
                const filled = products.filter(p => p[field] && p[field] !== 'N/A').length;
                const percent = Math.round((filled / products.length) * 100);
                return (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">{field}</span>
                      <span className="text-purple-400">{percent}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              }) : (
                <div className="text-gray-500 text-center py-4">No data available</div>
              )}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm text-gray-400 mb-3">Scraping Summary</h4>
            <div className="space-y-3">
              <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                <span className="text-gray-400">Total Time</span>
                <span className="font-semibold">
                  {stats.startTime ? Math.round((Date.now() - stats.startTime) / 1000) : 0}s
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                <span className="text-gray-400">Avg Time/Product</span>
                <span className="font-semibold">
                  {stats.totalProducts > 0 && stats.startTime
                    ? ((Date.now() - stats.startTime) / 1000 / stats.totalProducts).toFixed(2)
                    : 0}s
                </span>
              </div>
              <div className="flex justify-between p-3 bg-slate-900/50 rounded-lg">
                <span className="text-gray-400">Success Rate</span>
                <span className="font-semibold text-green-400">
                  {stats.totalProducts > 0
                    ? Math.round(((stats.totalProducts - stats.errors) / stats.totalProducts) * 100)
                    : 100}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;