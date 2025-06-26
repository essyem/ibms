// Common payment mode handling
function handlePaymentMode() {
    const paymentMode = document.getElementById('payment-mode');
    const splitDetails = document.getElementById('split-details');
    
    if (paymentMode && splitDetails) {
        paymentMode.addEventListener('change', function() {
            if (this.value === 'split') {
                splitDetails.classList.remove('d-none');
            } else {
                splitDetails.classList.add('d-none');
            }
        });
        
        // Initialize state
        if (paymentMode.value === 'split') {
            splitDetails.classList.remove('d-none');
        }
    }
}

// Initialize on all pages
document.addEventListener('DOMContentLoaded', function() {
    handlePaymentMode();
});