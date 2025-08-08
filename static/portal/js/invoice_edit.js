/**
 * Invoice Edit JavaScript
 * Handles all invoice editing functionality
 */

$(document).ready(function() {
    console.log('Invoice Edit Script Loaded');
    
    // Initialize variables
    let productRowTemplate = `
        <tr class="product-row">
            <td>
                <select class="form-control product-select" name="products" required>
                    <option value="">Select a product...</option>
                    {% for product in products %}
                    <option value="{{ product.id }}" 
                            data-selling-price="{{ product.unit_price }}" 
                            data-unit-price="{{ product.unit_price }}"
                            data-stock="{{ product.stock }}"
                            data-barcode="{{ product.barcode }}">
                        {{ product.name }} - QAR {{ product.unit_price }} (Stock: {{ product.stock }})
                    </option>
                    {% endfor %}
                </select>
            </td>
            <td>
                <input type="number" class="form-control quantity" name="quantity" value="1" min="1" step="1" required>
            </td>
            <td>
                <input type="number" class="form-control unit-price" name="unit_price" value="0.00" step="0.01" min="0" required>
            </td>
            <td>
                <input type="text" class="form-control total" name="total" value="0.00" readonly>
            </td>
            <td>
                <button type="button" class="btn btn-danger btn-sm remove-product">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `;
    
    // Add product row
    $('#add-product').click(function() {
        $('#product-rows').append(productRowTemplate);
    });
    
    // Remove product row
    $(document).on('click', '.remove-product', function() {
        $(this).closest('tr').remove();
        updateTotals();
    });
    
    // Product selection change
    $(document).on('change', '.product-select', function() {
        let $row = $(this).closest('tr');
        let selectedOption = $(this).find('option:selected');
        let unitPrice = selectedOption.data('unit-price') || 0;
        
        $row.find('.unit-price').val(unitPrice.toFixed(2));
        calculateRowTotal($row);
    });
    
    // Quantity or price change
    $(document).on('input', '.quantity, .unit-price', function() {
        calculateRowTotal($(this).closest('tr'));
    });
    
    // Payment mode change
    $('#payment-mode-select').change(function() {
        $('.payment-mode-details').removeClass('payment-mode-active');
        if ($(this).val() === 'split') {
            $('#split-details').addClass('payment-mode-active');
        }
    });
    
    // Tax or discount change
    $('#tax, #discount-value, #discount-type').on('input change', function() {
        updateTotals();
    });
    
    // Delete invoice confirmation
    $('#delete-invoice').click(function() {
        $('#deleteModal').modal('show');
    });
    
    // Calculate row total
    function calculateRowTotal($row) {
        let quantity = parseFloat($row.find('.quantity').val()) || 0;
        let unitPrice = parseFloat($row.find('.unit-price').val()) || 0;
        let total = quantity * unitPrice;
        
        $row.find('.total').val(total.toFixed(2));
        updateTotals();
    }
    
    // Update all totals
    function updateTotals() {
        let subtotal = 0;
        
        $('.total').each(function() {
            subtotal += parseFloat($(this).val()) || 0;
        });
        
        let tax = parseFloat($('#tax').val()) || 0;
        let discountValue = parseFloat($('#discount-value').val()) || 0;
        let discountType = $('#discount-type').val();
        let discountAmount = 0;
        
        if (discountType === 'percent') {
            discountAmount = subtotal * (discountValue / 100);
        } else {
            discountAmount = discountValue;
        }
        
        let grandTotal = subtotal + tax - discountAmount;
        
        $('#subtotal').val(subtotal.toFixed(2));
        $('#discount-amount').val(discountAmount.toFixed(2));
        $('#grand-total').val(grandTotal.toFixed(2));
        
        // Validate split payment if active
        if ($('#payment-mode-select').val() === 'split') {
            validateSplitPayment();
        }
    }
    
    // Validate split payment amounts
    function validateSplitPayment() {
        let grandTotal = parseFloat($('#grand-total').val()) || 0;
        let cashAmount = parseFloat($('input[name="cash_amount"]').val()) || 0;
        let posAmount = parseFloat($('input[name="pos_amount"]').val()) || 0;
        let otherAmount = parseFloat($('input[name="other_amount"]').val()) || 0;
        let totalSplit = cashAmount + posAmount + otherAmount;
        
        if (Math.abs(totalSplit - grandTotal) > 0.01) {
            $('#split-details').addClass('border border-danger');
            return false;
        } else {
            $('#split-details').removeClass('border border-danger');
            return true;
        }
    }
    
    // Form submission validation
    $('#invoice-form').submit(function(e) {
        // Validate at least one product
        if ($('.product-row').length === 0) {
            alert('Please add at least one product to the invoice');
            return false;
        }
        
        // Validate split payment if active
        if ($('#payment-mode-select').val() === 'split' && !validateSplitPayment()) {
            alert('Split payment amounts must equal the grand total');
            return false;
        }
        
        // Prepare items data for submission
        let items = [];
        $('.product-row').each(function() {
            let $row = $(this);
            let productId = $row.find('.product-select').val();
            let quantity = $row.find('.quantity').val();
            let unitPrice = $row.find('.unit-price').val();
            let itemId = $row.data('item-id');
            
            if (productId) {
                items.push({
                    id: itemId || null,
                    product: productId,
                    quantity: quantity,
                    unit_price: unitPrice
                });
            }
        });
        
        // Add items data to form
        $('<input>').attr({
            type: 'hidden',
            name: 'items',
            value: JSON.stringify(items)
        }).appendTo('#invoice-form');
        
        return true;
    });
    
    // Initialize totals
    updateTotals();
});