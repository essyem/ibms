document.addEventListener('DOMContentLoaded', function() {
    // Product selection handler
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-product')) {
            const row = e.target.closest('.dynamic-invoiceitem');
            const productId = e.target.value;
            const sellingPriceInput = row.querySelector('.field-selling_price input');
            
            if (productId) {
                fetch(`/admin/portal/product/${productId}/change/?_popup=1`)
                    .then(response => response.text())
                    .then(html => {
                        const doc = new DOMParser().parseFromString(html, 'text/html');
                        const sellingPrice = doc.querySelector('#id_selling_price').value;
                        const costPrice = doc.querySelector('#id_cost_price').value;
                        
                        // Update fields
                        if (sellingPriceInput) {
                            sellingPriceInput.value = sellingPrice;
                            sellingPriceInput.dispatchEvent(new Event('change'));
                        }
                        
                        // Update cost price display
                        const costPriceDisplay = row.querySelector('.field-cost_price div.readonly');
                        if (costPriceDisplay) {
                            costPriceDisplay.textContent = costPrice;
                        }
                    });
            }
        }
    });

    // Price/quantity change handler
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-quantity') || 
            e.target.classList.contains('field-selling_price')) {
            const row = e.target.closest('.dynamic-invoiceitem');
            const quantity = parseFloat(row.querySelector('.field-quantity input').value) || 0;
            const price = parseFloat(row.querySelector('.field-selling_price input').value) || 0;
            const totalDisplay = row.querySelector('.field-total div.readonly');
            
            if (totalDisplay) {
                totalDisplay.textContent = (quantity * price).toFixed(2);
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