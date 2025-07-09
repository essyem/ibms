#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

print("Testing admin URL configuration...")

# Import required modules
from django.contrib import admin
from django.urls import reverse, NoReverseMatch
from portal.models import Invoice

# Check if Invoice is registered
print(f"Invoice registered in admin: {Invoice in admin.site._registry}")

# Get the InvoiceAdmin instance
if Invoice in admin.site._registry:
    invoice_admin = admin.site._registry[Invoice]
    print(f"InvoiceAdmin class: {invoice_admin.__class__.__name__}")
    
    # Get custom URLs
    urls = invoice_admin.get_urls()
    print(f"Number of URLs from InvoiceAdmin: {len(urls)}")
    
    for i, url in enumerate(urls):
        if hasattr(url, 'name') and url.name:
            print(f"  URL {i}: name='{url.name}', pattern='{url.pattern}'")
    
    # Test URL resolution
    try:
        url = reverse('admin:invoice_pdf', args=[1])
        print(f"✅ URL 'admin:invoice_pdf' resolved to: {url}")
    except NoReverseMatch as e:
        print(f"❌ URL 'admin:invoice_pdf' failed: {e}")
        
        # Try different variations
        url_variations = [
            'portal_invoice_invoice_pdf',
            'portal_invoice_change_pdf',
            'portal_invoice_pdf',
        ]
        
        for variation in url_variations:
            try:
                url = reverse(f'admin:{variation}', args=[1])
                print(f"✅ URL 'admin:{variation}' resolved to: {url}")
                break
            except NoReverseMatch:
                print(f"❌ URL 'admin:{variation}' failed")
else:
    print("❌ Invoice model is not registered in admin!")
