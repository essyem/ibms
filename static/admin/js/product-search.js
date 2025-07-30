// static/admin/js/product-search.js

(function($) {
    'use strict';

    // Product search functionality
    function initializeProductSearch() {
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
            
            // Perform AJAX search
            $.ajax({
                url: '/admin/ajax/product-search/',
                data: { q: query },
                method: 'GET',
                success: function(data) {
                    displaySearchResults($results, data.products, $select, $container);
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
    
    function displaySearchResults($results, products, $select, $container) {
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
                        <span class="search-result-price">Selling: QAR ${product.unit_price}</span> |
                        <span class="search-result-cost">Cost: QAR ${product.cost_price || 'N/A'}</span> |
                        <span class="search-result-stock ${stockClass}">Stock: ${product.stock}</span> |
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
            selectProduct($select, productData, $container);
            $results.hide();
        });
    }
    
    function selectProduct($select, productData, $container) {
        // Update the select element
        const optionHtml = `<option value="${productData.id}" selected>${productData.display_text}</option>`;
        
        // Add option if it doesn't exist
        if ($select.find(`option[value="${productData.id}"]`).length === 0) {
            $select.append(optionHtml);
        }
        
        $select.val(productData.id).trigger('change');
        
        // Update unit price field if it exists
        const $priceField = $container.closest('tr, .form-row').find('input[name*="unit_price"]');
        if ($priceField.length) {
            $priceField.val(productData.unit_price);
        }
        
        // Show selected product info
        showSelectedProductInfo($container, productData);
        
        // Clear search input
        $container.find('.product-search-input').val('');
    }
    
    function showSelectedProductInfo($container, productData) {
        const $info = $container.find('.selected-product-info');
        const stockClass = productData.stock <= 10 ? 'low-stock' : '';
        
        const infoHtml = `
            <div class="product-details">
                <div class="product-name">${productData.name}</div>
                <div class="product-meta">
                    Selling: QAR ${productData.unit_price} | 
                    Cost: QAR ${productData.cost_price || 'N/A'} |
                    <span class="${stockClass}">Stock: ${productData.stock}</span> | 
                    Category: ${productData.category}
                    ${productData.barcode ? `| Barcode: ${productData.barcode}` : ''}
                </div>
            </div>
        `;
        
        $info.html(infoHtml).show();
    }
    
    // Barcode scanner functionality
    function initializeBarcodeScanner() {
        $(document).on('click', '.barcode-scan-btn', function() {
            const $btn = $(this);
            const $container = $btn.closest('.product-search-container');
            const $select = $container.find('select');
            
            showBarcodeScannerModal($select, $container);
        });
    }
    
    function showBarcodeScannerModal($select, $container) {
        const modalHtml = `
            <div class="barcode-scanner-modal">
                <div class="barcode-scanner-content">
                    <h3>Scan Product Barcode</h3>
                    <video class="barcode-scanner-video" autoplay></video>
                    <div class="barcode-scanner-controls">
                        <button type="button" class="btn-close-scanner">Close Scanner</button>
                    </div>
                    <div class="scanner-status">Position barcode within the camera view</div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        
        const $modal = $('.barcode-scanner-modal');
        const $video = $modal.find('.barcode-scanner-video')[0];
        const $status = $modal.find('.scanner-status');
        
        // Start camera
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(function(stream) {
                $video.srcObject = stream;
                
                // Simple barcode detection (you might want to use a proper barcode library)
                // This is a placeholder - in production, use libraries like QuaggaJS or ZXing
                $status.text('Camera ready - scan barcode');
                
                // Simulate barcode input for now
                $modal.find('.barcode-scanner-content').append(`
                    <div style="margin-top: 15px;">
                        <input type="text" placeholder="Enter barcode manually" class="manual-barcode-input" style="padding: 8px; width: 200px;">
                        <button type="button" class="btn-lookup-barcode" style="margin-left: 10px; padding: 8px 16px;">Lookup</button>
                    </div>
                `);
                
                // Handle manual barcode lookup
                $modal.find('.btn-lookup-barcode').on('click', function() {
                    const barcode = $modal.find('.manual-barcode-input').val().trim();
                    if (barcode) {
                        lookupProductByBarcode(barcode, $select, $container, $modal, stream);
                    }
                });
                
                // Handle Enter key in barcode input
                $modal.find('.manual-barcode-input').on('keypress', function(e) {
                    if (e.which === 13) {
                        $modal.find('.btn-lookup-barcode').click();
                    }
                });
            })
            .catch(function(error) {
                $status.text('Camera access denied or not available');
                console.error('Camera error:', error);
            });
        
        // Close modal
        $modal.find('.btn-close-scanner').on('click', function() {
            if ($video.srcObject) {
                $video.srcObject.getTracks().forEach(track => track.stop());
            }
            $modal.remove();
        });
        
        // Close on outside click
        $modal.on('click', function(e) {
            if (e.target === this) {
                $modal.find('.btn-close-scanner').click();
            }
        });
    }
    
    function lookupProductByBarcode(barcode, $select, $container, $modal, stream) {
        $.ajax({
            url: '/admin/ajax/barcode-lookup/',
            data: { barcode: barcode },
            method: 'GET',
            success: function(data) {
                if (data.product) {
                    selectProduct($select, data.product, $container);
                    
                    // Close scanner
                    if (stream) {
                        stream.getTracks().forEach(track => track.stop());
                    }
                    $modal.remove();
                } else {
                    alert('Product not found');
                }
            },
            error: function(xhr) {
                const response = JSON.parse(xhr.responseText);
                alert(response.error || 'Product not found');
            }
        });
    }
    
    // Initialize when DOM is ready
    $(document).ready(function() {
        initializeProductSearch();
        initializeBarcodeScanner();
    });
    
})(django.jQuery);
