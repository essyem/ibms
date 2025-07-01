#!/usr/bin/env python
"""
Test the live admin PDF generation with base64 embedded fonts
"""
import requests
import tempfile
import os

def test_admin_pdf():
    """Test PDF generation through admin interface"""
    
    # Test URL (without authentication for now)
    url = "http://127.0.0.1:8003/admin/portal/invoice/4/pdf/?download=true"
    
    print(f"Testing admin PDF URL: {url}")
    
    try:
        # Make request with a proper User-Agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Content type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Content length: {len(response.content)} bytes")
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            # Save the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(response.content)
                print(f"✓ Admin PDF downloaded: {tmp_file.name}")
                
                # Copy to accessible location
                static_path = "/home/essyem/portal/trendzportal/static/admin_test.pdf"
                with open(static_path, 'wb') as f:
                    f.write(response.content)
                print(f"✓ PDF copied to: {static_path}")
                
                return True
        else:
            print(f"✗ Failed to get PDF. Response content:")
            print(response.text[:500])  # First 500 chars
            return False
            
    except Exception as e:
        print(f"✗ Error testing admin PDF: {e}")
        return False

if __name__ == '__main__':
    print("Testing Admin PDF Generation")
    print("=" * 40)
    test_admin_pdf()
