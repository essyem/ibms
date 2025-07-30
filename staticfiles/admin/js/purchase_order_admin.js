// Purchase Order Admin JavaScript
(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Auto-calculate totals when inline items change
        function calculateTotal(row) {
            var quantity = parseFloat(row.find('.quantity-input').val()) || 0;
            var unitCost = parseFloat(row.find('.unit-cost-input').val()) || 0;
            var total = quantity * unitCost;
            row.find('input[name*="total"]').val(total.toFixed(2));
        }
        
        // Handle changes in quantity or unit cost
        $(document).on('change', '.quantity-input, .unit-cost-input', function() {
            calculateTotal($(this).closest('tr'));
        });
        
        // Auto-fill unit cost based on product selection
        $(document).on('change', 'select[name*="product"]', function() {
            var productSelect = $(this);
            var row = productSelect.closest('tr');
            var unitCostInput = row.find('.unit-cost-input');
            
            // If unit cost is empty, try to set it from product cost price
            if (!unitCostInput.val() || unitCostInput.val() == '0.00') {
                // This would need to be populated from the product data
                // For now, we'll let the admin handle it server-side
            }
        });
        
        // Calculate totals on page load for existing items
        $('.dynamic-form tr').each(function() {
            if ($(this).find('.quantity-input').length > 0) {
                calculateTotal($(this));
            }
        });
        
        console.log('Purchase Order admin JavaScript loaded');
    });
})(django.jQuery);
