// static/admin/js/barcode-scanner.js

(function($) {
    'use strict';
    
    // Enhanced barcode scanner with QuaggaJS support (if available)
    window.BarcodeScanner = {
        isInitialized: false,
        currentStream: null,
        
        init: function() {
            if (this.isInitialized) return;
            
            // Check if QuaggaJS is available (you can include it as a CDN)
            if (typeof Quagga !== 'undefined') {
                this.initQuagga();
            } else {
                console.log('QuaggaJS not available, using manual input');
            }
            
            this.isInitialized = true;
        },
        
        initQuagga: function() {
            // QuaggaJS configuration would go here
            console.log('QuaggaJS barcode scanner initialized');
        },
        
        startScanning: function(callback) {
            const self = this;
            
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                } 
            })
            .then(function(stream) {
                self.currentStream = stream;
                
                if (typeof Quagga !== 'undefined') {
                    self.startQuaggaScanning(stream, callback);
                } else {
                    // Fallback to manual input
                    callback(stream, null);
                }
            })
            .catch(function(error) {
                console.error('Camera access error:', error);
                callback(null, error);
            });
        },
        
        stopScanning: function() {
            if (this.currentStream) {
                this.currentStream.getTracks().forEach(track => track.stop());
                this.currentStream = null;
            }
            
            if (typeof Quagga !== 'undefined') {
                Quagga.stop();
            }
        },
        
        startQuaggaScanning: function(stream, callback) {
            // This would implement QuaggaJS scanning
            // For now, just call the callback
            callback(stream, null);
        }
    };
    
    // Initialize on document ready
    $(document).ready(function() {
        window.BarcodeScanner.init();
    });
    
})(django.jQuery);
