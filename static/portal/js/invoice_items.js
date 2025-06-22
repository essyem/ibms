document.addEventListener('DOMContentLoaded', function() {
    // Handle product selection change
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-product')) {
            const row = e.target.closest('.dynamic-form');
            const productId = e.target.value;
            const sellingPriceField = row.querySelector('.field-selling_price input');
            
            if (productId) {
                fetch(`/admin/portal/product/${productId}/change/?_popup=1`)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const sellingPrice = doc.querySelector('#id_selling_price').value;
                        sellingPriceField.value = sellingPrice;
                        
                        // Trigger change event to recalculate total
                        const event = new Event('change');
                        sellingPriceField.dispatchEvent(event);
                    });
            }
        }
        
        // Recalculate total when quantity or price changes
        function calculateDiscount() {
            const discountType = document.querySelector('#id_discount_type').value;
            const discountValue = parseFloat(document.querySelector('#id_discount_value').value) || 0;
            const subtotal = parseFloat(document.querySelector('#id_subtotal').textContent) || 0;
            const tax = parseFloat(document.querySelector('#id_tax').value) || 0;
    
            let discountAmount = 0;
            if (discountType === 'percent') {
                discountAmount = (subtotal + tax) * (discountValue / 100);
            } else {
                discountAmount = Math.min(discountValue, subtotal + tax);
            }
    
            const grandTotal = (subtotal + tax) - discountAmount;
    
            document.querySelector('#id_discount_amount').textContent = discountAmount.toFixed(2);
            document.querySelector('#id_grand_total').textContent = grandTotal.toFixed(2);
        }

// Add event listeners for discount fields
        document.querySelector('#id_discount_type').addEventListener('change', calculateDiscount);
        document.querySelector('#id_discount_value').addEventListener('input', calculateDiscount);
        document.querySelector('#id_tax').addEventListener('input', calculateDiscount);
        if (e.target.classList.contains('field-quantity') || 
            e.target.classList.contains('field-selling_price')) {
            const row = e.target.closest('.dynamic-form');
            const quantity = row.querySelector('.field-quantity input').value || 0;
            const price = row.querySelector('.field-selling_price input').value || 0;
            const totalField = row.querySelector('.field-total div.readonly');
            
            if (totalField) {
                totalField.textContent = (quantity * price).toFixed(2);
            }
        }
    });
});

// Add to existing invoice_items.js
