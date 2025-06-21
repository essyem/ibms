document.addEventListener('DOMContentLoaded', function() {
    const productRows = document.getElementById('product-rows');
    const addProductBtn = document.getElementById('add-product');
    const template = document.getElementById('product-row-template');
    const subtotalInput = document.getElementById('subtotal');
    const taxInput = document.getElementById('tax');
    const totalInput = document.getElementById('total');
    
    // Add first product row by default
    addProductRow();
    
    // Add product row
    addProductBtn.addEventListener('click', addProductRow);
    
    // Remove product row
    productRows.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-product') || 
            e.target.closest('.remove-product')) {
            e.target.closest('tr').remove();
            calculateTotals();
        }
    });
    
    // Handle product selection
    productRows.addEventListener('change', function(e) {
        if (e.target.classList.contains('product-select')) {
            const row = e.target.closest('tr');
            const productId = e.target.value;
            const unitPriceInput = row.querySelector('.unit-price');
            
            // Fetch product details
            fetch(`/api/products/${productId}/`)
                .then(response => response.json())
                .then(data => {
                    unitPriceInput.value = data.selling_price;
                    calculateRowTotal(row);
                    calculateTotals();
                });
        }
    });
    
    // Handle quantity/price changes
    productRows.addEventListener('input', function(e) {
        if (e.target.classList.contains('quantity') || 
            e.target.classList.contains('unit-price')) {
            const row = e.target.closest('tr');
            calculateRowTotal(row);
            calculateTotals();
        }
    });
    
    // Tax input change
    taxInput.addEventListener('input', calculateTotals);
    
    function addProductRow() {
        const clone = template.content.cloneNode(true);
        productRows.appendChild(clone);
        
        // Initialize the new row
        const newRow = productRows.lastElementChild;
        const productSelect = newRow.querySelector('.product-select');
        const unitPriceInput = newRow.querySelector('.unit-price');
        
        // Set initial price
        if (productSelect.selectedOptions[0]) {
            unitPriceInput.value = productSelect.selectedOptions[0].dataset.price;
            calculateRowTotal(newRow);
            calculateTotals();
        }
    }
    
    function calculateRowTotal(row) {
        const quantity = parseFloat(row.querySelector('.quantity').value) || 0;
        const unitPrice = parseFloat(row.querySelector('.unit-price').value) || 0;
        const totalInput = row.querySelector('.total');
        
        totalInput.value = (quantity * unitPrice).toFixed(2);
    }
    
    function calculateTotals() {
        let subtotal = 0;
        
        document.querySelectorAll('#product-rows tr').forEach(row => {
            subtotal += parseFloat(row.querySelector('.total').value) || 0;
        });
        
        const tax = parseFloat(taxInput.value) || 0;
        const total = subtotal + tax;
        
        subtotalInput.value = subtotal.toFixed(2);
        totalInput.value = total.toFixed(2);
    }
    
    // Form submission - convert dynamic rows to form data
    document.getElementById('invoice-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const form = e.target;
        const formData = new FormData(form);
        
        // Add product items to form data
        document.querySelectorAll('#product-rows tr').forEach((row, index) => {
            formData.append(`items-${index}-product`, row.querySelector('.product-select').value);
            formData.append(`items-${index}-quantity`, row.querySelector('.quantity').value);
            formData.append(`items-${index}-unit_price`, row.querySelector('.unit-price').value);
        });
        
        // Submit the form
        fetch(form.action, {
            method: form.method,
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect_url;
            }
        });
    });
});