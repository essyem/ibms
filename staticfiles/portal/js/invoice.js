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
        const match = optionText.match(/\$([\d.]+)/);
        return match ? match[1] : null;
    }

const productRows = document.getElementById('product-rows');
const addProductBtn = document.getElementById('add-product');
const template = document.getElementById('product-row-template');
const subtotalInput = document.getElementById('subtotal');
const taxInput = document.getElementById('tax');
const totalInput = document.getElementById('total');

// Add product row function
function addProductRow() {
    if (!template) return;
    const clone = template.content.cloneNode(true);
    productRows.appendChild(clone);
    calculateTotals();
}

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
            if (costDisplay && sellingPrice) {
                // This is temporary - adjust ratio as needed
                costDisplay.textContent = (parseFloat(sellingPrice) * 0.8).toFixed(2);
            }
        }
    }
});

// Dummy calculateTotals function to prevent errors
function calculateTotals() {
    // Implement calculation logic here if needed
}

// Initialize existing rows
document.querySelectorAll('.dynamic-invoiceitem').forEach(row => {
    const productSelect = row.querySelector('.field-product select');
    if (productSelect && productSelect.value) {
        productSelect.dispatchEvent(new Event('change'));
    }

    const costDisplay = row.querySelector('.field-cost_price div.readonly');
    if (costDisplay) {
        // This is temporary - adjust ratio as needed
        costDisplay.textContent = (parseFloat(sellingPrice) * 0.8).toFixed(2);
    }
});
