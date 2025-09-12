/**
 * Unified Invoice Creation JavaScript v3.1
 * Updated with:
 * - Manual unit price editing
 * - Direct customer creation link
 * - Fixed status saving
 * - Enhanced form handling
 */

(function($) {
    'use strict';

    console.log('🚀 Invoice Creation Unified Script v3.1 Loading...');

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
            console.log('🔗 Binding events...');
            
            // Check if customer search elements exist
            const customerSearchInput = $('.customer-search-input');
            const customerSearchContainer = $('.customer-search-container');
            const customerSearchResults = $('.customer-search-results');
            
            console.log('🔍 Customer search elements:', {
                input: customerSearchInput.length,
                container: customerSearchContainer.length,
                results: customerSearchResults.length
            });
            
            // Add Product Button
            $('#add-product').on('click', (e) => {
                e.preventDefault();
                this.addProductRow();
            });

            // Remove Product Button
            $(document).on('click', '.remove-product', (e) => {
                e.preventDefault();
                this.removeProductRow($(e.target).closest('tr'));
            });

            // Product Search
            $(document).on('input', '.product-search-input', (e) => {
                this.handleProductSearch($(e.target));
            });

            // Product Selection
            $(document).on('change', '.product-select', (e) => {
                this.handleProductSelection($(e.target));
            });

            // Quantity or unit price change
            $(document).on('input', '.quantity, .unit-price', (e) => {
                this.calculateRowTotal($(e.target).closest('tr'));
            });
            
            // Price override checkbox
            $(document).on('change', '.use-product-price', (e) => {
                const $checkbox = $(e.target);
                const $row = $checkbox.closest('tr');
                const $unitPriceInput = $row.find('.unit-price');
                
                if ($checkbox.is(':checked')) {
                    // Reset to product price
                    const $select = $row.find('.product-select');
                    const $option = $select.find('option:selected');
                    if ($option.val()) {
                        const productPrice = $option.data('unit-price') || $option.data('selling-price') || 0;
                        $unitPriceInput.val(parseFloat(productPrice).toFixed(2));
                        $unitPriceInput.prop('readonly', true);
                    }
                } else {
                    // Allow manual editing
                    $unitPriceInput.prop('readonly', false);
                    $unitPriceInput.focus();
                }
                
                this.calculateRowTotal($row);
            });            // Unit Price Changes (delegated)
            $(document).on('input change', '.unit-price', (e) => {
                this.calculateRowTotal($(e.target).closest('tr'));
            });

            // Unit Price Focus/Blur for better UX
            $(document).on('focus', '.unit-price', (e) => {
                $(e.target).addClass('editing-price').attr('title', 'Editing unit price - Enter to save');
            });

            $(document).on('blur', '.unit-price', (e) => {
                $(e.target).removeClass('editing-price').attr('title', 'Click to edit unit price');
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

            // Split Payment Validation
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

            // Hide search results when clicking outside
            $(document).on('click', (e) => {
                if (!$(e.target).closest('.product-search-container').length) {
                    $('.search-results').hide();
                }
            });

            // Customer Search
            $(document).on('input', '.customer-search-input', (e) => {
                console.log('🔍 Customer search input event triggered:', e.target.value);
                this.handleCustomerSearch($(e.target));
            });

            // Customer Selection (delegated)
            $(document).on('click', '.customer-search-result-item', (e) => {
                e.preventDefault();
                this.selectCustomer($(e.target).closest('.customer-search-result-item'));
            });

            // Hide customer search results when clicking outside
            $(document).on('click', (e) => {
                if (!$(e.target).closest('.customer-search-container').length) {
                    $('.customer-search-results').hide();
                }
            });
        }

        handleCustomerSearch($input) {
            const query = $input.val().trim();
            const $results = $input.closest('.customer-search-container').find('.customer-search-results');
            
            console.log('🔍 handleCustomerSearch called:', {
                query: query,
                inputElement: $input.length,
                resultsElement: $results.length
            });

            if (query.length < 2) {
                console.log('❌ Query too short, hiding results');
                $results.hide();
                return;
            }

            console.log('📡 Making AJAX request to /ajax/customer-search/');
            $.ajax({
                url: '/ajax/customer-search/',
                method: 'GET',
                data: { q: query },
                success: (response) => {
                    console.log('✅ AJAX success:', response);
                    this.displayCustomerSearchResults(response.customers, $results);
                },
                error: (xhr) => {
                    console.error('❌ Customer search error:', xhr);
                    console.error('Status:', xhr.status, 'Text:', xhr.statusText);
                    console.error('Response:', xhr.responseText);
                    this.showError('Customer search failed');
                }
            });
        }

    displayCustomerSearchResults(customers, $results) {
        console.log('📋 displayCustomerSearchResults called:', {
            customers: customers,
            customersCount: customers ? customers.length : 0,
            resultsElement: $results.length
        });
        
        $results.empty();

        if (!customers || customers.length === 0) {
            console.log('❌ No customers found, showing message');
            $results.html('<div class="no-results">No customers found</div>').show();
            return;
        }

        console.log('✅ Displaying', customers.length, 'customers');
        customers.forEach((customer) => {
            const $item = $('<div class="customer-search-result-item customer-item">')
                .html(`
                    <strong>${customer.display_text}</strong><br>
                    <small style="color: #94a3b8;">${customer.phone || 'No phone'}</small>
                `)
                .data('customer', customer)
                .on('click', (e) => {
                    e.preventDefault();
                    this.selectCustomer($(e.currentTarget));
                    $results.hide();
                });
            $results.append($item);
        });

        $results.show();
    }

    selectCustomer($item) {
        const customer = $item.data('customer');
        console.log('✅ Customer selected:', customer.display_text);

        // Update hidden customer ID field
        $('#customer-id').val(customer.id);

        // Update search input
        $('.customer-search-input').val(customer.display_text);

        // Update customer details
        $('#phone').val(customer.phone || '');
        $('#tax_number').val(customer.tax_number || '');
        $('#address').val(customer.address || '');
    }

    addProductRow() {
        console.log('➕ Adding product row...');

        if (!this.productTemplate.length) {
            console.error('❌ Product template not found');
            return;
            }

            let clone;
            if (this.productTemplate[0].content) {
                clone = document.importNode(this.productTemplate[0].content, true);
            } else {
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

            if (/^\d{8,}$/.test(query)) {
                console.log('🔍 Barcode detected:', query);
                this.lookupProductByBarcode(query, $row);
                return;
            }

            this.searchProducts(query, $row);
        }

        searchProducts(query, $row) {
            console.log('🔍 Searching products for:', query);
            $.ajax({
                url: '/ajax/product-search/',
                method: 'GET',
                data: { q: query },
                success: (response) => {
                    console.log('✅ Product search success:', response);
                    this.displaySearchResults(response.products, $row);
                },
                error: (xhr) => {
                    console.error('❌ Product search error:', xhr);
                    console.error('Status:', xhr.status, 'Text:', xhr.statusText);
                    console.error('Response:', xhr.responseText);
                    this.showError('Product search failed');
                }
            });
        }

        displaySearchResults(products, $row) {
            const $results = $row.find('.search-results');
            $results.empty();

            if (!products || products.length === 0) {
                $results.html('<div class="no-results p-2" style="color: #94a3b8;">No products found</div>').show();
                return;
            }

            console.log('✅ Displaying', products.length, 'products');
            products.forEach((product) => {
                const $item = $('<div class="search-result-item product-item">')
                    .html(`${product.display_text}<br><small style="color: #94a3b8;">${product.stock_text}</small>`)
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
            const $unitPriceInput = $row.find('.unit-price');

            $select.val(product.id);
            $searchInput.val(product.name);
            
            // Set unit price with option to override
            const productPrice = parseFloat(product.unit_price || 0);
            $unitPriceInput.val(productPrice.toFixed(2));
            
            // Add price override controls if they don't exist
            if (!$row.find('.price-override-controls').length) {
                const $priceCell = $unitPriceInput.closest('td');
                $priceCell.append(`
                    <div class="price-override-controls mt-1">
                        <small>
                            <label class="form-check-label" style="color: #94a3b8;">
                                <input type="checkbox" class="form-check-input use-product-price" checked> 
                                Use product price (QAR ${productPrice.toFixed(2)})
                            </label>
                        </small>
                    </div>
                `);
            }
            
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
            console.log('🔍 Looking up product by barcode:', barcode);
            $.ajax({
                url: '/ajax/barcode-lookup/',
                method: 'GET',
                data: { barcode: barcode },
                success: (response) => {
                    console.log('✅ Barcode lookup success:', response);
                    if (response.product) {
                        this.selectProduct(response.product, $row);
                        this.showSuccess(`Product found: ${response.product.name}`);
                    } else {
                        this.showError(`No product found for barcode: ${barcode}`);
                    }
                },
                error: (xhr) => {
                    console.error('❌ Barcode lookup error:', xhr);
                    console.error('Status:', xhr.status, 'Text:', xhr.statusText);
                    console.error('Response:', xhr.responseText);
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

            this.validateSplitPayment();
        }

        handlePaymentModeChange(paymentMode) {
            const $splitDetails = $('#split-details');
            
            if (paymentMode === 'split') {
                $splitDetails.removeClass('d-none');
            } else {
                $splitDetails.addClass('d-none');
                $splitDetails.find('input[type="number"]').val('0.00');
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

            // Get and validate status
            const status = $('#status').val();
            formData.append('status', status);
            console.log('📌 Invoice status being submitted:', status);

            // Collect product items
            const items = [];
            $('#product-rows tr').each(function() {
                const $row = $(this);
                const productId = $row.find('.product-select').val();
                const productName = $row.find('.product-select option:selected').text().split(' - ')[0] || 'Custom Item';
                const quantity = $row.find('.quantity').val() || '1';
                const unitPrice = $row.find('.unit-price').val() || '0';
                const description = $row.find('.product-search-input').val() || productName;

                if (productId && productId.trim() !== '') {
                    items.push({
                        product: productId.trim(),
                        product_name: productName,
                        quantity: quantity.trim(),
                        unit_price: unitPrice.trim(),
                        selling_price: unitPrice.trim()
                    });
                } else if (quantity > 0 && unitPrice > 0) {
                    items.push({
                        product: null,
                        product_name: description,
                        quantity: quantity.trim(),
                        unit_price: unitPrice.trim(),
                        selling_price: unitPrice.trim(),
                        is_custom: true
                    });
                }
            });

            console.log('📋 Collected items:', items);
            
            // Validate we have at least one item
            if (items.length === 0) {
                this.showError('Please add at least one product to the invoice');
                return false;
            }

            // Add items and totals to form data
            formData.append('items', JSON.stringify(items));
            formData.append('subtotal', $('#subtotal').val() || '0');
            formData.append('tax', $('#tax').val() || '0');
            formData.append('discount_type', $('#discount-type').val() || 'percentage');
            formData.append('discount_value', $('#discount-value').val() || '0');
            formData.append('discount_amount', $('#discount-amount').val() || '0');
            formData.append('grand_total', $('#grand-total').val() || '0');

            // Submit form via AJAX
            this.submitForm(formData);
        }

        submitForm(formData) {
            const csrfToken = this.getCSRFToken();
            if (csrfToken) {
                formData.append('csrfmiddlewaretoken', csrfToken);
            }

            const url = this.formElement.attr('action') || window.location.pathname;
            
            $.ajax({
                url: url,
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                success: (response) => {
                    console.log('✅ Invoice submitted successfully:', response);
                    this.handleSubmissionSuccess(response);
                },
                error: (xhr) => {
                    console.error('❌ Invoice submission error:', xhr);
                    this.handleSubmissionError(xhr);
                }
            });
        }

        getCSRFToken() {
            let token = $('[name=csrfmiddlewaretoken]').val();
            if (!token) token = $('meta[name=csrf-token]').attr('content');
            if (!token) {
                const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
                token = cookieValue ? cookieValue.pop() : '';
            }
            return token;
        }

        handleSubmissionSuccess(response) {
            if (response.success) {
                this.showSuccessModal(response);
            } else {
                this.showError(response.message || 'Invoice submission failed');
            }
        }

        handleSubmissionError(xhr) {
            let message = 'Invoice submission failed';
            
            if (xhr.responseJSON) {
                if (xhr.responseJSON.error) {
                    message = xhr.responseJSON.error;
                } else if (xhr.responseJSON.message) {
                    message = xhr.responseJSON.message;
                } else if (xhr.responseJSON.errors) {
                    message = Object.values(xhr.responseJSON.errors).flat().join(', ');
                }
            } else if (xhr.responseText) {
                const errorMatch = xhr.responseText.match(/<title>(.*?)<\/title>/);
                if (errorMatch) message = errorMatch[1];
            }
            
            this.showError(message);
        }

        showSuccessModal(response) {
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

        showSuccess(message) {
            console.log('✅', message);
        }

        showError(message) {
            console.error('🚨 Error:', message);
            alert('ERROR: ' + message + '\n\nCheck browser console for more details.');
        }
    }

    // Initialize when document is ready
    $(document).ready(function() {
        console.log('📄 DOM ready, initializing Invoice Manager...');
        window.invoiceManager = new InvoiceManager();
    });

})(jQuery);