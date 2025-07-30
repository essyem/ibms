/**
 * Enhanced product search for procurement admin
 * Provides better autocomplete experience with multiple search fields
 */
(function($) {
    'use strict';
    
    // Enhanced autocomplete for product fields
    function enhanceProductAutocomplete() {
        // Find all product autocomplete fields
        const productFields = $('input[id*="product"]').filter('[data-autocomplete-light-url]');
        
        productFields.each(function() {
            const $field = $(this);
            const originalUrl = $field.attr('data-autocomplete-light-url');
            
            // Add custom search parameters to include multiple fields
            $field.on('autocomplete:initialize', function() {
                // Enhance the autocomplete widget
                const widget = $field.data('autocomplete');
                if (widget) {
                    // Override the remote method to include better search
                    const originalRemote = widget.remote;
                    widget.remote = function(query, syncCallback, asyncCallback) {
                        // Add enhanced search parameters
                        const enhancedQuery = {
                            q: query,
                            search_fields: 'name,sku,barcode,category__name'
                        };
                        
                        // Call original remote with enhanced query
                        return originalRemote.call(this, enhancedQuery, syncCallback, asyncCallback);
                    };
                }
            });
        });
    }
    
    // Initialize when DOM is ready
    $(document).ready(function() {
        enhanceProductAutocomplete();
        
        // Re-initialize when new inline forms are added
        $(document).on('formset:added', function() {
            setTimeout(enhanceProductAutocomplete, 100);
        });
    });
    
    // Add helpful tooltips for product search
    $(document).on('focus', 'input[id*="product"]', function() {
        const $field = $(this);
        if (!$field.attr('title')) {
            $field.attr('title', 'Search by product name, SKU, barcode, or category name');
        }
    });
    
})(django.jQuery);
