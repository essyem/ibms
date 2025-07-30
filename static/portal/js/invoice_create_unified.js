/**
 * Unified Invoice Creation JavaScript
 * Handles all invoice creation functionality including:
 * - Product search and selection
 * - Barcode scanning
 * - Customer creation
 * - Split payment handling
 * - Form validation and submission
 */

(function($) {
    'use strict';

    console.log('🚀 Invoice Creation Unified Script v3.0 Loading...');

    // Global variables
    let invoiceManager = null;

    // Main Invoice Manager Class
    class InvoiceManager {
        constructor() {
            this.formElement = null;
            this.productRows = null;
            this.productTemplate = null;
            this.initialized = false;

            this.init();
        }

        init() {
            console.log('🔧 Initializing Invoice Manager...');
            
            // Wait for DOM to be ready
            $(document).ready(() => {
                this.findElements();
                this.bindEvents();
                this.addInitialProductRow();
                this.initialized = true;
                console.log('✅ Invoice Manager initialized successfully');
            });
        }

        findElements() {
            this.formElement = $('#invoice-form');
            this.productRows = $('#product-rows');
            this.productTemplate = $('#product-row-template');
            
            console.log('📋 Elements found:', {
                form: this.formElement.length > 0,
                rows: this.productRows.length > 0,
                template: this.productTemplate.length > 0
            });
        }

        bindEvents() {
            // Add Product Button
            $('#add-product').on('click', (e) => {
                e.preventDefault();
                this.addProductRow();
            });

            // Remove Product Button (delegated)
            $(document).on('click', '.remove-product', (e) => {
                e.preventDefault();
                this.removeProductRow($(e.target).closest('tr'));
            });

            // Product Search (delegated)
            $(document).on('input', '.product-search-input', (e) => {
                this.handleProductSearch($(e.target));
            });

            // Product Selection (delegated)
            $(document).on('change', '.product-select', (e) => {
                this.handleProductSelection($(e.target));
            });

            // Quantity Changes (delegated)
            $(document).on('input change', '.quantity', (e) => {
                this.calculateRowTotal($(e.target).closest('tr'));
            });

            // Unit Price Changes (delegated)
            $(document).on('input change', '.unit-price', (e) => {
                this.calculateRowTotal($(e.target).closest('tr'));
            });

            // Barcode Scanning (delegated)
            $(document).on('click', '.barcode-scan-btn', (e) => {
                e.preventDefault();
                this.handleBarcodeScanning($(e.target).closest('tr'));
            });

            // Payment Mode Changes
            $('#payment-mode-select').on('change', (e) => {
                this.handlePaymentModeChange($(e.target).val());
            });

            // Split Payment Validation (delegated)
            $(document).on('input', '#split-details input[type="number"]', () => {
                this.validateSplitPayment();
            });

            // Tax and Discount Changes
            $('#tax, #discount-value').on('input', () => {
                this.updateTotals();
            });

            $('#discount-type').on('change', () => {
                this.updateTotals();
            });

            // Form Submission
            this.formElement.on('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission();
            });

            // Customer Creation
            $('#add-customer-btn').on('click', (e) => {
                e.preventDefault();
                this.openCustomerModal();
            });

            // Hide search results when clicking outside
            $(document).on('click', (e) => {
                if (!$(e.target).closest('.product-search-container').length) {
                    $('.search-results').hide();
                }
            });
        }

        addProductRow() {
            console.log('➕ Adding product row...');
            
            if (!this.productTemplate.length) {
                console.error('❌ Product template not found');
                return;
            }

            let clone;
            if (this.productTemplate[0].content) {
                // Modern browsers with HTML5 template support
                clone = document.importNode(this.productTemplate[0].content, true);
            } else {
                // Fallback for older browsers
                clone = $(this.productTemplate.html())[0];
            }

            this.productRows.append(clone);
            this.updateTotals();
            console.log('✅ Product row added');
        }

        removeProductRow($row) {
            console.log('🗑️ Removing product row...');
            $row.remove();
            this.updateTotals();
        }

        addInitialProductRow() {
            // Add first product row automatically if none exist
            if (this.productRows.children().length === 0) {
                setTimeout(() => {
                    this.addProductRow();
                    console.log('🚀 Initial product row added');
                }, 100);
            }
        }

        handleProductSearch($input) {
            const query = $input.val().trim();
            const $row = $input.closest('tr');
            const $results = $row.find('.search-results');

            if (query.length < 2) {
                $results.hide();
                return;
            }

            // Check if it's a barcode (8+ digits)
            if (/^\d{8,}$/.test(query)) {
                console.log('🔍 Barcode detected:', query);
                this.lookupProductByBarcode(query, $row);
                return;
            }

            // Regular product search
            this.searchProducts(query, $row);
        }

        searchProducts(query, $row) {
            $.ajax({
                url: '/ajax/product-search/',
                method: 'GET',
                data: { q: query },
                success: (response) => {
                    this.displaySearchResults(response.products, $row);
                },
                error: (xhr) => {
                    console.error('❌ Product search error:', xhr);
                    this.showError('Product search failed');
                }
            });
        }

        displaySearchResults(products, $row) {
            const $results = $row.find('.search-results');
            $results.empty();

            if (!products || products.length === 0) {
                $results.html('<div class="no-results">No products found</div>').show();
                return;
            }

            products.forEach((product) => {
                const $item = $('<div class="search-result-item">')
                    .css({
                        'padding': '8px',
                        'border-bottom': '1px solid #eee',
                        'cursor': 'pointer',
                        'background': '#f8f9fa'
                    })
                    .hover(function() {
                        $(this).css('background', '#e9ecef');
                    }, function() {
                        $(this).css('background', '#f8f9fa');
                    })
                    .html(`${product.display_text}<br><small class="text-muted">${product.stock_text}</small>`)
                    .data('product', product)
                    .on('click', () => {
                        this.selectProduct(product, $row);
                        $results.hide();
                    });
                $results.append($item);
            });

            $results.show();
        }

        selectProduct(product, $row) {
            console.log('✅ Product selected:', product.name);

            const $select = $row.find('.product-select');
            const $searchInput = $row.find('.product-search-input');

            // Update select dropdown
            $select.val(product.id);

            // Update search input
            $searchInput.val(product.name);

            // Update price
            $row.find('.unit-price').val(product.unit_price);

            // Calculate totals
            this.calculateRowTotal($row);
        }

        handleProductSelection($select) {
            const $row = $select.closest('tr');
            const $option = $select.find('option:selected');

            if ($option.val()) {
                const unitPrice = $option.data('selling-price') || $option.data('unit-price') || 0;
                $row.find('.unit-price').val(parseFloat(unitPrice).toFixed(2));
                
                const productName = $option.text().split(' - ')[0];
                $row.find('.product-search-input').val(productName);
            } else {
                $row.find('.unit-price').val('0.00');
                $row.find('.product-search-input').val('');
            }

            this.calculateRowTotal($row);
        }

        handleBarcodeScanning($row) {
            const barcode = prompt('Enter barcode manually or scan with barcode reader:');
            if (barcode && barcode.trim()) {
                this.lookupProductByBarcode(barcode.trim(), $row);
            }
        }

        lookupProductByBarcode(barcode, $row) {
            $.ajax({
                url: '/ajax/barcode-lookup/',
                method: 'GET',
                data: { barcode: barcode },
                success: (response) => {
                    if (response.product) {
                        this.selectProduct(response.product, $row);
                        this.showSuccess(`Product found: ${response.product.name}`);
                    } else {
                        this.showError(`No product found for barcode: ${barcode}`);
                    }
                },
                error: (xhr) => {
                    console.error('❌ Barcode lookup error:', xhr);
                    this.showError('Barcode lookup failed');
                }
            });
        }

        calculateRowTotal($row) {
            const quantity = parseFloat($row.find('.quantity').val()) || 0;
            const unitPrice = parseFloat($row.find('.unit-price').val()) || 0;
            const total = quantity * unitPrice;

            $row.find('.total').val(total.toFixed(2));
            this.updateTotals();
        }

        updateTotals() {
            let subtotal = 0;
            $('.total').each(function() {
                subtotal += parseFloat($(this).val()) || 0;
            });

            const tax = parseFloat($('#tax').val()) || 0;
            const discountValue = parseFloat($('#discount-value').val()) || 0;
            const discountType = $('#discount-type').val();

            let discountAmount = 0;
            if (discountType === 'percent') {
                discountAmount = subtotal * (discountValue / 100);
            } else {
                discountAmount = discountValue;
            }

            const grandTotal = subtotal + tax - discountAmount;

            $('#subtotal').val(subtotal.toFixed(2));
            $('#discount-amount').val(discountAmount.toFixed(2));
            $('#grand-total').val(grandTotal.toFixed(2));

            // Validate split payment if active
            this.validateSplitPayment();
        }

        handlePaymentModeChange(paymentMode) {
            const $splitDetails = $('#split-details');
            
            if (paymentMode === 'split') {
                $splitDetails.removeClass('d-none');
                console.log('✅ Split payment enabled');
            } else {
                $splitDetails.addClass('d-none');
                $splitDetails.find('input[type="number"]').val('0.00');
                console.log('✅ Split payment disabled');
            }
        }

        validateSplitPayment() {
            const paymentMode = $('#payment-mode-select').val();
            if (paymentMode !== 'split') return;

            const grandTotal = parseFloat($('#grand-total').val()) || 0;
            const cashAmount = parseFloat($('input[name="cash_amount"]').val()) || 0;
            const posAmount = parseFloat($('input[name="pos_amount"]').val()) || 0;
            const otherAmount = parseFloat($('input[name="other_amount"]').val()) || 0;
            const totalSplit = cashAmount + posAmount + otherAmount;

            const $messages = $('#form-messages');
            
            if (Math.abs(totalSplit - grandTotal) > 0.01) {
                $messages.removeClass('d-none alert-success')
                    .addClass('alert-warning')
                    .text(`Split total (${totalSplit.toFixed(2)}) must equal grand total (${grandTotal.toFixed(2)})`);
            } else {
                $messages.removeClass('alert-warning').addClass('d-none');
            }
        }

        handleFormSubmission() {
            console.log('📝 Submitting invoice form...');

            // Debug: Check if form exists
            if (!this.formElement || this.formElement.length === 0) {
                console.error('❌ Form element not found');
                this.showError('Form not found');
                return false;
            }

            // Validate split payment
            const paymentMode = $('#payment-mode-select').val();
            if (paymentMode === 'split') {
                const grandTotal = parseFloat($('#grand-total').val()) || 0;
                const cashAmount = parseFloat($('input[name="cash_amount"]').val()) || 0;
                const posAmount = parseFloat($('input[name="pos_amount"]').val()) || 0;
                const otherAmount = parseFloat($('input[name="other_amount"]').val()) || 0;
                const totalSplit = cashAmount + posAmount + otherAmount;

                if (Math.abs(totalSplit - grandTotal) > 0.01) {
                    this.showError('Split payment amounts must equal the grand total');
                    return false;
                }
            }

            // Collect form data
            const formData = new FormData(this.formElement[0]);

            // Debug: Check customer value specifically
            const customerSelect = $('#customer');
            const customerValue = customerSelect.val();
            const customerText = customerSelect.find('option:selected').text();
            console.log('👤 Customer Debug:', {
                value: customerValue,
                text: customerText,
                element: customerSelect[0]
            });
            
            // Ensure customer ID is numeric
            if (customerValue && customerValue.trim() !== '') {
                const numericCustomerId = parseInt(customerValue.trim());
                if (isNaN(numericCustomerId)) {
                    console.error('❌ Invalid customer ID:', customerValue);
                    this.showError('Invalid customer selection. Please select a valid customer.');
                    return false;
                } else {
                    formData.set('customer', numericCustomerId.toString());
                    console.log('✅ Customer ID validated and set:', numericCustomerId);
                }
            }

            // Collect product items with data validation
            const items = [];
            $('#product-rows tr').each(function() {
                const $row = $(this);
                const productId = $row.find('.product-select').val();
                if (productId && productId.trim() !== '') {
                    const quantity = $row.find('.quantity').val() || '1';
                    const unitPrice = $row.find('.unit-price').val() || '0';
                    
                    // Validate product ID is numeric
                    const numericProductId = parseInt(productId.trim());
                    if (isNaN(numericProductId)) {
                        console.error('❌ Invalid product ID:', productId);
                        return; // Skip this item
                    }
                    
                    // Validate that we have numeric values
                    if (!isNaN(parseFloat(quantity)) && !isNaN(parseFloat(unitPrice))) {
                        items.push({
                            product: numericProductId.toString(),
                            quantity: quantity.trim(),
                            unit_price: unitPrice.trim(),
                            selling_price: unitPrice.trim()
                        });
                        console.log('✅ Added item:', {
                            product: numericProductId,
                            quantity: quantity.trim(),
                            unit_price: unitPrice.trim()
                        });
                    } else {
                        console.warn('⚠️ Skipping invalid item (non-numeric values):', {
                            productId,
                            quantity,
                            unitPrice
                        });
                    }
                } else {
                    console.log('ℹ️ Skipping empty product row');
                }
            });

            console.log('📋 Collected items:', items);
            
            // Validate totals before submission
            const subtotal = $('#subtotal').val() || '0';
            const grandTotal = $('#grand-total').val() || '0';
            const taxAmount = $('#tax').val() || '0';
            const discountAmount = $('#discount-amount').val() || '0';
            
            console.log('💰 Totals:', { subtotal, grandTotal, taxAmount, discountAmount });

            // Validate we have at least one item
            if (items.length === 0) {
                this.showError('Please add at least one product to the invoice');
                return false;
            }

            // Validate grand total
            const currentGrandTotal = parseFloat(grandTotal) || 0;
            if (currentGrandTotal <= 0) {
                this.showError('Invoice total must be greater than zero');
                return false;
            }

            formData.append('items', JSON.stringify(items));
            formData.append('subtotal', subtotal);
            formData.append('tax', taxAmount);
            formData.append('discount_type', $('#discount-type').val() || 'percentage');
            formData.append('discount_value', $('#discount-value').val() || '0');
            formData.append('discount_amount', discountAmount);
            formData.append('grand_total', grandTotal);

            // Submit form via AJAX
            this.submitForm(formData);
        }

        submitForm(formData) {
            // Get CSRF token from multiple possible sources
            let csrfToken = $('[name=csrfmiddlewaretoken]').val();
            
            // If not found in form, try to get from cookies
            if (!csrfToken) {
                csrfToken = this.getCSRFTokenFromCookie();
            }
            
            // If still not found, try from meta tag
            if (!csrfToken) {
                csrfToken = $('meta[name=csrf-token]').attr('content');
            }
            
            console.log('🔐 CSRF Token sources checked:');
            console.log('  From form input:', $('[name=csrfmiddlewaretoken]').val() ? 'Found' : 'Not found');
            console.log('  From cookie:', this.getCSRFTokenFromCookie() ? 'Found' : 'Not found');
            console.log('  Final token:', csrfToken ? 'Available' : 'MISSING');
            
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken);
            } else {
                console.error('❌ No CSRF token found! This will cause a 403 error.');
            }

            // Log all form data for debugging
            console.log('📋 Form Data Contents:');
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}:`, value);
            }

            const url = this.formElement.attr('action') || window.location.pathname;
            console.log('🌐 Submitting to URL:', url);

            $.ajax({
                url: url,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                beforeSend: function(xhr, settings) {
                    console.log('🚀 About to send AJAX request');
                    console.log('   URL:', settings.url);
                    console.log('   Method:', settings.type);
                },
                success: (response) => {
                    console.log('✅ Invoice submitted successfully:', response);
                    this.handleSubmissionSuccess(response);
                },
                error: (xhr, textStatus, errorThrown) => {
                    console.error('❌ Invoice submission error:');
                    console.error('   Status:', xhr.status);
                    console.error('   Status Text:', xhr.statusText);
                    console.error('   Response Text:', xhr.responseText);
                    console.error('   Text Status:', textStatus);
                    console.error('   Error Thrown:', errorThrown);
                    this.handleSubmissionError(xhr);
                }
            });
        }

        // Replace the current getCSRFTokenFromCookie() with this more robust version
        getCSRFTokenFromCookie() {
            // Try multiple methods to get CSRF token
            let token = $('[name=csrfmiddlewaretoken]').val(); // Form input
            if (!token) token = $('meta[name=csrf-token]').attr('content'); // Meta tag
            if (!token) { // Cookie fallback
                const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
                token = cookieValue ? cookieValue.pop() : '';
            }
            console.log('CSRF Token:', token ? 'Found' : 'MISSING - This will cause 403 errors');
            return token;
        }

        handleSubmissionSuccess(response) {
            if (response.success) {
                this.showSuccessModal(response);
            } else {
                this.showError('Invoice submission failed');
            }
        }

        handleSubmissionError(xhr) {
            let message = 'Invoice submission failed';
            console.error('❌ Full error details:', {
                status: xhr.status,
                statusText: xhr.statusText,
                responseText: xhr.responseText,
                responseJSON: xhr.responseJSON
            });
            
            if (xhr.responseJSON) {
                if (xhr.responseJSON.error) {
                    message = xhr.responseJSON.error;
                } else if (xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                } else if (xhr.responseJSON.errors) {
                    message = Object.values(xhr.responseJSON.errors).flat().join(', ');
                }
            } else if (xhr.responseText) {
                // Try to extract meaningful error from HTML response
                const errorMatch = xhr.responseText.match(/<title>(.*?)<\/title>/);
                if (errorMatch) {
                    message = errorMatch[1];
                }
            }
            
            this.showError(message);
        }

        showSuccessModal(response) {
            // Implementation for success modal with action buttons
            const invoiceId = response.invoice_id;
            const modalHtml = `
                <div class="modal fade" id="successModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header bg-success text-white">
                                <h5 class="modal-title">Invoice Created Successfully!</h5>
                            </div>
                            <div class="modal-body text-center">
                                <p>Invoice #${response.invoice_number || invoiceId} has been created successfully.</p>
                                <div class="d-grid gap-2">
                                    <a href="/invoices/${invoiceId}/" class="btn btn-primary">View Invoice</a>
                                    <a href="/invoices/${invoiceId}/pdf/" class="btn btn-info">Download PDF</a>
                                    <button onclick="window.open('/invoices/${invoiceId}/pdf/', '_blank')" class="btn btn-secondary">Print Invoice</button>
                                    <a href="/invoices/" class="btn btn-outline-primary">Invoice List</a>
                                    <button onclick="location.reload()" class="btn btn-success">Create Another</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            $('body').append(modalHtml);
            $('#successModal').modal('show');
        }

        openCustomerModal() {
            console.log('👤 Opening customer creation modal...');
            // Implementation for customer modal
            // This would create and show the customer creation modal
        }

        showSuccess(message) {
            console.log('✅', message);
            // You can implement a toast notification here
        }

        showError(message) {
            console.error('🚨 Showing error to user:', message);
            // Show detailed error in console and alert
            alert('ERROR: ' + message + '\n\nCheck browser console for more details.');
        }
    }

    // Initialize when document is ready
    $(document).ready(function() {
        console.log('📄 DOM ready, initializing Invoice Manager...');
        invoiceManager = new InvoiceManager();
    });

    // Export for global access if needed
    window.InvoiceManager = InvoiceManager;

})(jQuery);