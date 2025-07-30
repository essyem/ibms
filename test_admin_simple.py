#!/usr/bin/env python3
"""
Simple test to understand Django admin URL structure
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trendzportal.settings')
django.setup()

from django.contrib import admin
from django.urls import reverse
from portal.models import Invoice

# Test basic admin URLs first
try:
    changelist_url = reverse('admin:portal_invoice_changelist')
    print(f"✅ Changelist URL: {changelist_url}")
except Exception as e:
    print(f"❌ Changelist URL failed: {e}")

try:
    change_url = reverse('admin:portal_invoice_change', args=[1])
    print(f"✅ Change URL: {change_url}")
except Exception as e:
    print(f"❌ Change URL failed: {e}")

# Now test our custom PDF URL
try:
    pdf_url = reverse('admin:invoice_pdf', args=[1])
    print(f"✅ PDF URL: {pdf_url}")
except Exception as e:
    print(f"❌ PDF URL failed: {e}")
    
# Let's also check the admin site's URL patterns
print("\nAll admin URLs containing 'invoice' or 'pdf':")
for pattern in admin.site.get_urls():
    if hasattr(pattern, 'name') and pattern.name:
        if 'invoice' in pattern.name or 'pdf' in pattern.name:
            print(f"  {pattern.name}")
