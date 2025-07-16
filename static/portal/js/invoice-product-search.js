// static/portal/js/invoice-product-search.js

(function($) {
    'use strict';

    // Product search functionality for invoice creation
    function initializeInvoiceProductSearch() {
        $(document).on('input', '.product-search-input', function() {
            const $input = $(this);
            const $container = $input.closest('.product-search-container');
            const $results = $container.find('.search-results');
            const $select = $container.find('select');
            const query = $input.val().trim();
            
            if (query.length < 2) {
                $results.hide();
                return;
            }
            
            // Show loading
            $results.html('<div class="search-loading">Searching...</div>').show();
            
            // Perform AJAX search using public endpoint
            $.ajax({
                url: '/ajax/product-search/',
                data: { q: query },
                method: 'GET',
                success: function(data) {
                    displayInvoiceSearchResults($results, data.products, $select, $container);
                },
                error: function() {
                    $results.html('<div class="search-no-results">Search error occurred</div>');
                }
            });
        });
        
        // Hide results when clicking outside
        $(document).on('click', function(e) {
            if (!$(e.target).closest('.product-search-container').length) {
                $('.search-results').hide();
            }
        });
    }
    
    function displayInvoiceSearchResults($results, products, $select, $container) {
        if (products.length === 0) {
            $results.html('<div class="search-no-results">No products found</div>');
            return;
        }
        
        let html = '';
        products.forEach(function(product) {
            const stockClass = product.stock <= 10 ? 'low-stock' : '';
            html += `
                <div class="search-result-item" data-product-id="${product.id}" data-product-data='${JSON.stringify(product)}'>
                    <div class="search-result-name">${product.name}</div>
                    <div class="search-result-details">
                        <span class="search-result-price">QAR ${product.unit_price}</span> |
                        <span class="search-result-stock ${stockClass}">${product.stock_text}</span> |
                        <span>${product.category}</span>
                        ${product.barcode ? `| Barcode: ${product.barcode}` : ''}
                    </div>
                </div>
            `;
        });
        
        $results.html(html);
        
        // Handle result item click
        $results.find('.search-result-item').on('click', function() {
            const productData = JSON.parse($(this).attr('data-product-data'));
            selectInvoiceProduct($select, productData, $container);
            $results.hide();
        });
    }
    
    function selectInvoiceProduct($select, productData, $container) {
        console.log('Selecting product:', productData);
        
        // Update the select element
        const optionHtml = `<option value="${productData.id}" 
                                   data-selling-price="${productData.unit_price}" 
                                   data-cost-price="${productData.cost_price || productData.unit_price}"
                                   data-unit-price="${productData.unit_price}"
                                   data-stock="${productData.stock}"
                                   data-barcode="${productData.barcode}"
                                   selected>${productData.display_text}</option>`;
        
        // Add option if it doesn't exist
        if ($select.find(`option[value="${productData.id}"]`).length === 0) {
            $select.append(optionHtml);
        }
        
        $select.val(productData.id).trigger('change');
        
        // Update price fields in the same row
        const $row = $container.closest('tr');
        const unitPrice = productData.unit_price || productData.selling_price || 0;
        const costPrice = productData.cost_price || unitPrice;
        
        console.log('Setting prices - Unit:', unitPrice, 'Cost:', costPrice);
        
        $row.find('.unit-price').val(unitPrice);
        $row.find('.cost-price').val(costPrice);
        
        // Clear and update search input
        $container.find('.product-search-input').val(productData.name);
        
        // Recalculate totals
        updateRowTotal($row);
        
        // Show selected product info
        showInvoiceProductInfo($container, productData);
        
        // Clear search input
        $container.find('.product-search-input').val('');
    }
    
    function showInvoiceProductInfo($container, productData) {
        const $info = $container.find('.selected-product-info');
        const stockClass = productData.stock <= 10 ? 'low-stock' : '';
        
        const infoHtml = `
            <div class="product-details">
                <div class="product-name">${productData.name}</div>
                <div class="product-meta">
                    Price: QAR ${productData.unit_price} | 
                    <span class="${stockClass}">${productData.stock_text}</span> | 
                    Category: ${productData.category}
                    ${productData.barcode ? `| Barcode: ${productData.barcode}` : ''}
                </div>
            </div>
        `;
        
        $info.html(infoHtml).show();
    }
    
    // Barcode scanner for invoice
    function initializeInvoiceBarcodeScanner() {
        $(document).on('click', '.barcode-scan-btn', function() {
            const $btn = $(this);
            const $container = $btn.closest('.product-search-container');
            const $select = $container.find('select');
            
            showInvoiceBarcodeScannerModal($select, $container);
        });
    }
    
    function showInvoiceBarcodeScannerModal($select, $container) {
        const modalHtml = `
            <div class="barcode-scanner-modal">
                <div class="barcode-scanner-content">
                    <h3>Scan Product Barcode</h3>
                    <div style="margin: 20px 0;">
                        <input type="text" placeholder="Enter barcode manually" class="manual-barcode-input form-control" style="margin-bottom: 10px;">
                        <button type="button" class="btn btn-primary btn-lookup-barcode">Lookup Product</button>
                    </div>
                    <div class="barcode-scanner-controls">
                        <button type="button" class="btn btn-secondary btn-close-scanner">Close</button>
                    </div>
                    <div class="scanner-status">Enter barcode above or scan with camera</div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        
        const $modal = $('.barcode-scanner-modal');
        
        // Handle manual barcode lookup
        $modal.find('.btn-lookup-barcode').on('click', function() {
            const barcode = $modal.find('.manual-barcode-input').val().trim();
            if (barcode) {
                lookupInvoiceProductByBarcode(barcode, $select, $container, $modal);
            }
        });
        
        // Handle Enter key in barcode input
        $modal.find('.manual-barcode-input').on('keypress', function(e) {
            if (e.which === 13) {
                $modal.find('.btn-lookup-barcode').click();
            }
        });
        
        // Close modal
        $modal.find('.btn-close-scanner').on('click', function() {
            $modal.remove();
        });
        
        // Close on outside click
        $modal.on('click', function(e) {
            if (e.target === this) {
                $modal.find('.btn-close-scanner').click();
            }
        });
        
        // Focus on barcode input
        $modal.find('.manual-barcode-input').focus();
    }
    
    function lookupInvoiceProductByBarcode(barcode, $select, $container, $modal) {
        $modal.find('.scanner-status').text('Looking up product...');
        
        $.ajax({
            url: '/ajax/barcode-lookup/',
            data: { barcode: barcode },
            method: 'GET',
            success: function(data) {
                if (data.product) {
                    console.log('Barcode lookup success:', data.product);
                    selectInvoiceProduct($select, data.product, $container);
                    $modal.remove();
                } else {
                    $modal.find('.scanner-status').text('Product not found');
                    alert('Product not found');
                }
            },
            error: function(xhr) {
                let message = 'Product not found';
                try {
                    const response = JSON.parse(xhr.responseText);
                    message = response.error || message;
                } catch (e) {
                    // Use default message
                }
                console.error('Barcode lookup error:', xhr.responseText);
                $modal.find('.scanner-status').text(message);
                alert(message);
            }
        });
    }
    
    // Helper function to update row total (assumes this exists in invoice.js)
    function updateRowTotal($row) {
        const quantity = parseFloat($row.find('.quantity').val()) || 0;
        const unitPrice = parseFloat($row.find('.unit-price').val()) || 0;
        const total = quantity * unitPrice;
        
        console.log('Updating row total:', { quantity, unitPrice, total });
        
        $row.find('.total').val(total.toFixed(2));
        
        // If there's a global total update function, call it
        if (typeof window.calculateTotals === 'function') {
            window.calculateTotals();
        } else if (typeof calculateTotals === 'function') {
            calculateTotals();
        }
    }
    
    // Add Product Row functionality
    function initializeAddProductFunctionality() {
        console.log('🚀 Initializing Add Product functionality...');
        
        // Check if button exists
        var addProductBtn = document.getElementById('add-product');
        if (addProductBtn) {
            console.log('✅ Add Product button found:', addProductBtn);
        } else {
            console.error('❌ Add Product button NOT found!');
            alert('❌ Add Product button not found on page!');
        }
        
        // Check if template exists
        var template = document.getElementById('product-row-template');
        if (template) {
            console.log('✅ Product template found:', template);
        } else {
            console.error('❌ Product template NOT found!');
            alert('❌ Product template not found on page!');
        }
        
        // Check if product-rows container exists
        var productRows = document.getElementById('product-rows');
        if (productRows) {
            console.log('✅ Product rows container found:', productRows);
        } else {
            console.error('❌ Product rows container NOT found!');
            alert('❌ Product rows container not found on page!');
        }
        
        // Define global functions that can be used by template
        window.updateTotals = function() {
            var subtotal = 0;
            $('.total').each(function() {
                var value = parseFloat($(this).val()) || 0;
                subtotal += value;
            });
            
            var tax = parseFloat($('#tax').val()) || 0;
            var discountValue = parseFloat($('#discount-value').val()) || 0;
            var discountType = $('#discount-type').val();
            
            var discountAmount = 0;
            if (discountType === 'percent') {
                discountAmount = subtotal * (discountValue / 100);
            } else {
                discountAmount = discountValue;
            }
            
            var grandTotal = subtotal + tax - discountAmount;
            
            $('#subtotal').val(subtotal.toFixed(2));
            $('#discount-amount').val(discountAmount.toFixed(2));
            $('#grand-total').val(grandTotal.toFixed(2));
            
            console.log('💰 Totals updated - Subtotal:', subtotal, 'Grand Total:', grandTotal);
        };
        
        window.calculateRowTotal = function(row) {
            var $row = $(row);
            var quantity = parseFloat($row.find('.quantity').val()) || 0;
            var unitPrice = parseFloat($row.find('.unit-price').val()) || 0;
            var total = quantity * unitPrice;
            
            $row.find('.total').val(total.toFixed(2));
            window.updateTotals();
            
            console.log('🧮 Row total calculated:', total);
        };
        
        // Add Product button click handler
        $(document).on('click', '#add-product', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🖱️ Add Product clicked from external JS');
            alert('Add Product button clicked! Checking template...');
            
            var template = document.getElementById('product-row-template');
            if (!template) {
                console.error('❌ Template not found');
                alert('❌ Product template not found. Please refresh the page.');
                return;
            }
            
            console.log('✅ Template found:', template);
            alert('✅ Template found! Cloning...');
            
            var clone;
            try {
                if (template.content) {
                    clone = document.importNode(template.content, true);
                    console.log('✅ Using HTML5 template.content');
                } else {
                    clone = $(template.innerHTML)[0];
                    console.log('✅ Using fallback innerHTML');
                }
            } catch (error) {
                console.error('❌ Clone error:', error);
                alert('❌ Error cloning template: ' + error.message);
                return;
            }
            
            var productRows = document.getElementById('product-rows');
            if (productRows) {
                try {
                    productRows.appendChild(clone);
                    console.log('✅ Product row added successfully');
                    alert('✅ Product row added successfully!');
                    window.updateTotals();
                } catch (error) {
                    console.error('❌ Error appending row:', error);
                    alert('❌ Error adding row: ' + error.message);
                }
            } else {
                console.error('❌ Product rows container not found');
                alert('❌ Could not find product-rows container. Please refresh the page.');
            }
        });
        
        // Product selection change handler
        $(document).on('change', '.product-select', function() {
            var $select = $(this);
            var $row = $select.closest('tr');
            var selectedOption = $select.find('option:selected');
            
            if (selectedOption.val()) {
                var unitPrice = selectedOption.data('selling-price') || selectedOption.data('unit-price') || 0;
                
                console.log('✅ Product selected:', {
                    id: selectedOption.val(),
                    name: selectedOption.text(),
                    unitPrice: unitPrice
                });
                
                $row.find('.unit-price').val(parseFloat(unitPrice).toFixed(2));
                window.calculateRowTotal($row[0]);
                
                var productName = selectedOption.text().split(' - ')[0];
                $row.find('.product-search-input').val(productName);
            } else {
                $row.find('.unit-price').val('0.00');
                $row.find('.total').val('0.00');
                $row.find('.product-search-input').val('');
                window.updateTotals();
            }
        });
        
        // Quantity change handler
        $(document).on('input change', '.quantity', function() {
            var $row = $(this).closest('tr');
            window.calculateRowTotal($row[0]);
        });
        
        // Remove product row handler
        $(document).on('click', '.remove-product', function(e) {
            e.preventDefault();
            $(this).closest('tr').remove();
            window.updateTotals();
            console.log('🗑️ Product row removed');
        });
        
        // Add first row automatically after a short delay
        setTimeout(function() {
            if ($('#product-rows tr').length === 0) {
                $('#add-product').trigger('click');
                console.log('🚀 First product row added automatically');
            }
        }, 500);
    }
    
    // Add Customer functionality
    function initializeAddCustomerFunctionality() {
        console.log('👤 Initializing Add Customer functionality...');
        
        $(document).on('click', '#add-customer-btn', function(e) {
            e.preventDefault();
            console.log('👤 Add Customer button clicked from external JS');
            alert('Add Customer clicked! Opening modal...');
            openCustomerModal();
        });
        
        window.openCustomerModal = function() {
            console.log('🔧 Opening customer modal from external JS...');
            
            const modalHtml = `
                <div class="modal fade" id="customerModal" tabindex="-1" role="dialog" aria-labelledby="customerModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-lg" role="document">
                        <div class="modal-content">
                            <div class="modal-header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                                <h5 class="modal-title" id="customerModalLabel">
                                    <i class="fas fa-user-plus me-2"></i>Add New Customer
                                </h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close" onclick="closeCustomerModal()">×</button>
                            </div>
                            <div class="modal-body">
                                <form id="customerForm">
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label for="full_name" class="form-label fw-bold">
                                                <i class="fas fa-user me-1"></i>Full Name <span class="text-danger">*</span>
                                            </label>
                                            <input type="text" class="form-control" id="full_name" name="full_name" required>
                                            <div class="invalid-feedback"></div>
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label for="phone" class="form-label fw-bold">
                                                <i class="fas fa-phone me-1"></i>Phone <span class="text-danger">*</span>
                                            </label>
                                            <input type="text" class="form-control" id="phone" name="phone" required>
                                            <div class="invalid-feedback"></div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-6 mb-3">
                                            <label for="company_name" class="form-label fw-bold">
                                                <i class="fas fa-building me-1"></i>Company Name
                                            </label>
                                            <input type="text" class="form-control" id="company_name" name="company_name">
                                        </div>
                                        <div class="col-md-6 mb-3">
                                            <label for="tax_number" class="form-label fw-bold">
                                                <i class="fas fa-receipt me-1"></i>Tax Number
                                            </label>
                                            <input type="text" class="form-control" id="tax_number" name="tax_number">
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-8 mb-3">
                                            <label for="address" class="form-label fw-bold">
                                                <i class="fas fa-map-marker-alt me-1"></i>Address
                                            </label>
                                            <textarea class="form-control" id="address" name="address" rows="3"></textarea>
                                        </div>
                                        <div class="col-md-4 mb-3">
                                            <label for="preferred_contact_method" class="form-label fw-bold">
                                                <i class="fas fa-envelope me-1"></i>Contact Method
                                            </label>
                                            <select class="form-control" id="preferred_contact_method" name="preferred_contact_method">
                                                <option value="">Select...</option>
                                                <option value="phone">Phone</option>
                                                <option value="email">Email</option>
                                                <option value="whatsapp">WhatsApp</option>
                                            </select>
                                        </div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" onclick="closeCustomerModal()">Cancel</button>
                                <button type="button" class="btn btn-primary" id="saveCustomerBtn">
                                    <i class="fas fa-save me-1"></i>Save Customer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            $('#customerModal').remove();
            $('body').append(modalHtml);
            
            try {
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = new bootstrap.Modal(document.getElementById('customerModal'));
                    modal.show();
                } else if ($.fn.modal) {
                    $('#customerModal').modal('show');
                } else {
                    $('#customerModal').addClass('show').css('display', 'block');
                    $('body').addClass('modal-open');
                }
                console.log('✅ Customer modal opened successfully');
            } catch (error) {
                console.error('❌ Error opening modal:', error);
                $('#customerModal').addClass('show').css('display', 'block');
                $('body').addClass('modal-open');
            }
            
            $(document).off('click', '#saveCustomerBtn').on('click', '#saveCustomerBtn', function() {
                saveCustomer();
            });
        };
        
        window.closeCustomerModal = function() {
            try {
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('customerModal'));
                    if (modal) modal.hide();
                } else if ($.fn.modal) {
                    $('#customerModal').modal('hide');
                } else {
                    $('#customerModal').removeClass('show').css('display', 'none');
                    $('body').removeClass('modal-open');
                }
            } catch (error) {
                $('#customerModal').removeClass('show').css('display', 'none');
                $('body').removeClass('modal-open');
            }
            
            setTimeout(function() {
                $('#customerModal').remove();
            }, 300);
        };
        
        window.saveCustomer = function() {
            alert('Save Customer function called! This will save the customer data.');
            // For now, just close the modal - you can implement full save later
            window.closeCustomerModal();
        };
    }

    // Initialize when DOM is ready
    $(document).ready(function() {
        initializeInvoiceProductSearch();
        initializeInvoiceBarcodeScanner();
        initializeAddProductFunctionality();
        initializeAddCustomerFunctionality();
    });
    
})(jQuery);
