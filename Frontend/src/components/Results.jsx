import React from 'react';

const Results = ({ products }) => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
      <h3 className="text-xl font-semibold mb-4">Scraped Products ({products.length})</h3>
      <div className="overflow-x-auto max-h-[600px]">
        {products.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No products scraped yet. Start scraping to see results.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-900 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Product</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Price</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Category</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Variants</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product, idx) => (
                <tr key={idx} className="border-t border-slate-700 hover:bg-slate-700/30">
                  <td className="px-4 py-3">
                    <div className="font-medium">{product.product_name}</div>
                    <div className="text-xs text-gray-500">{product.sku}</div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-green-400">₹{product.current_price}</div>
                    {product.original_price && product.discount_percentage > 0 && (
                      <div className="text-xs text-gray-500 line-through">₹{product.original_price}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm">{product.category}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      product.availability === 'In Stock' 
                        ? 'bg-green-600/20 text-green-400' 
                        : 'bg-red-600/20 text-red-400'
                    }`}>
                      {product.availability}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">{product.variants?.length || 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Results;