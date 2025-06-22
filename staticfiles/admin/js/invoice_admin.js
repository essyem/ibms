// static/admin/js/invoice_admin.js
document.addEventListener('DOMContentLoaded', function() {
    // Enable selling price fields
    document.querySelectorAll('.field-selling_price input').forEach(input => {
        input.removeAttribute('readonly');
        input.removeAttribute('disabled');
    });
    
    // Auto-fill selling price from product when selected
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-product')) {
            const row = e.target.closest('.dynamic-invoiceitem');
            const productId = e.target.value;
            const sellingPriceInput = row.querySelector('.field-selling_price input');
            
            if (productId) {
                fetch(`/admin/portal/product/${productId}/change/`)
                    .then(response => response.text())
                    .then(html => {
                        const doc = new DOMParser().parseFromString(html, 'text/html');
                        const price = doc.querySelector('#id_selling_price').value;
                        sellingPriceInput.value = price;
                    });
            }
        }
    });
});