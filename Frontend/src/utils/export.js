export const exportData = (products, format, addLog) => {
  if (products.length === 0) {
    addLog('No data to export', 'error');
    return;
  }

  try {
    let content, filename, type;

    if (format === 'json') {
      content = JSON.stringify(products, null, 2);
      filename = 'scraped_products.json';
      type = 'application/json';
    } else if (format === 'csv') {
      const headers = ['product_name', 'sku', 'current_price', 'category', 'availability'];
      const csvRows = [
        headers.join(','),
        ...products.map(p => 
          headers.map(h => {
            let val = p[h] || '';
            val = String(val);
            if (val.includes(',')) val = `"${val}"`;
            return val;
          }).join(',')
        )
      ];
      
      content = csvRows.join('\n');
      filename = 'scraped_products.csv';
      type = 'text/csv;charset=utf-8;';
    }

    const blob = new Blob([content], { type });
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(blobUrl);
    
    addLog(`Successfully exported ${products.length} products as ${format.toUpperCase()}`, 'success');
  } catch (error) {
    addLog(`Export failed: ${error.message}`, 'error');
  }
};