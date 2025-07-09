// Add Product Button Debug Script
(function() {
    'use strict';
    
    console.log('🔍 Add Product Button Debug Script Loaded');
    
    function debugAddProductButton() {
        const addBtn = document.getElementById('add-product');
        const productRows = document.getElementById('product-rows');
        const template = document.getElementById('product-row-template');
        
        console.log('Elements Check:');
        console.log('- Add Button:', addBtn);
        console.log('- Product Rows:', productRows);
        console.log('- Template:', template);
        
        if (!addBtn) {
            console.error('❌ Add Product button not found!');
            return false;
        }
        
        if (!productRows) {
            console.error('❌ Product rows container not found!');
            return false;
        }
        
        if (!template) {
            console.error('❌ Product row template not found!');
            return false;
        }
        
        console.log('✅ All elements found');
        
        // Test manual row addition
        function testAddRow() {
            console.log('🧪 Testing manual row addition...');
            const initialCount = productRows.children.length;
            console.log('Initial row count:', initialCount);
            
            const clone = template.content.cloneNode(true);
            productRows.appendChild(clone);
            
            const newCount = productRows.children.length;
            console.log('New row count:', newCount);
            
            if (newCount > initialCount) {
                console.log('✅ Manual row addition works!');
                return true;
            } else {
                console.log('❌ Manual row addition failed!');
                return false;
            }
        }
        
        // Add our own test listener
        addBtn.addEventListener('click', function(e) {
            console.log('🖱️ Test click handler triggered');
            testAddRow();
        });
        
        return true;
    }
    
    // Run debug when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', debugAddProductButton);
    } else {
        debugAddProductButton();
    }
    
    // Also run after a short delay to catch any late initialization
    setTimeout(debugAddProductButton, 1000);
    
})();
