// static/admin/js/invoice_admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Parse product prices from data attribute
    function getProductPrices(selectElement) {
        const priceData = selectElement.getAttribute('data-prices');
        const prices = {};
        priceData.split('|').forEach(item => {
            const [id, selling, cost] = item.split(',');
            prices[id] = { selling, cost };
        });
        return prices;
    }
    // Function to extract price from option text
    function extractPrice(optionText) {
        const match = optionText.match(/QAR\s+([\d.]+)|QAR([\d.]+)/);
        return match ? (match[1] || match[2]) : null;
    }

    // Handle product selection changes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-product')) {
            const row = e.target.closest('.dynamic-invoiceitem');
            const selectedOption = e.target.options[e.target.selectedIndex];
            const sellingPrice = extractPrice(selectedOption.text);
            
            if (sellingPrice) {
                const sellingInput = row.querySelector('.field-selling_price input');
                if (sellingInput) {
                    sellingInput.value = sellingPrice;
                    sellingInput.dispatchEvent(new Event('change'));
                }
                
                // For cost price, we'll use a ratio (or fetch via API if needed)
                const costDisplay = row.querySelector('.field-cost_price div.readonly');
                if (costDisplay) {
                    // This is temporary - adjust ratio as needed
                    costDisplay.textContent = (parseFloat(sellingPrice) * 0.8).toFixed(2);
                }
            }
        }
    });

    // Initialize existing rows
    document.querySelectorAll('.dynamic-invoiceitem').forEach(row => {
        const productSelect = row.querySelector('.field-product select');
        if (productSelect && productSelect.value) {
            productSelect.dispatchEvent(new Event('change'));
        }
    });
});