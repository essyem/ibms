#!/usr/bin/env python3
"""
Test script to verify admin URL resolution for PDF actions
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from django.urls import reverse
from portal.models import Invoice

def test_url_resolution():
    """Test admin PDF URL resolution"""
    
    try:
        # Try to get an invoice to test with
        invoice = Invoice.objects.first()
        if not invoice:
            print("❌ No invoices found in database. Please create an invoice first.")
            return False
        
        print(f"✅ Testing with Invoice ID: {invoice.pk}")
        
        # Test URL resolution
        try:
            pdf_url = reverse('admin:portal_invoice_invoice_pdf', args=[invoice.pk])
            print(f"✅ Admin PDF URL resolved: {pdf_url}")
            
            # Test with download parameter
            download_url = f"{pdf_url}?download=true"
            print(f"✅ Admin PDF Download URL: {download_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ URL resolution failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing admin PDF URL resolution...")
    success = test_url_resolution()
    
    if success:
        print("✅ Admin PDF URLs are working correctly!")
    else:
        print("❌ Admin PDF URL configuration needs fixing.")
