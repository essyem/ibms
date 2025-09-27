# portal/views.py
from django.views import View
from django.views.generic import (CreateView, UpdateView, DeleteView,
ListView, DetailView, View)
from portal.models import Invoice, InvoiceItem, Product, Customer
from procurement.models import Supplier, PurchaseOrder
from django.db.models import Sum, Q, Avg, Count, F, Case, When, DecimalField, Min, Max
from django.db.models.functions import Cast
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models.functions import TruncDate, TruncMonth
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from portal.forms import ProductEnquiryForm, InvoiceForm, InvoiceItemForm, CustomerForm
from django.contrib import messages
import decimal
from decimal import Decimal
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .decorators import superuser_required, dashboard_access_required, reports_access_required
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse, path
from django.template.loader import get_template, render_to_string
from io import BytesIO
from django.conf import settings
from django.utils.html import format_html
from django.utils import timezone
import json
import logging
from decimal import Decimal
import os
import base64
import random
from weasyprint import HTML, CSS
from django.conf import settings
import arabic_reshaper
from bidi.algorithm import get_display
from datetime import datetime, timedelta
from django.core.paginator import Paginator
import csv
from django.db.models import ExpressionWrapper, FloatField
from django.views.decorators.csrf import csrf_exempt


logger = logging.getLogger(__name__)

def process_arabic_text(text):
    """Process Arabic text for proper display in PDFs"""
    if not text:
        return text
    
    try:
        # Reshape Arabic text for proper connection of letters
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply bidirectional algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception:
        # Return original text if processing fails
        return text


@csrf_exempt
def set_language(request):
    """Set the preferred site language in session and redirect back.

    Accepts POST or GET with 'lang' param (e.g., 'en' or 'ar'). Stores in
    session under 'site_language' and also sets Django's LANGUAGE_CODE key.
    """
    lang = request.POST.get('lang') or request.GET.get('lang')
    next_url = request.META.get('HTTP_REFERER') or reverse('portal:index')

    if not lang:
        return redirect(next_url)

    # Save language in session
    try:
        request.session['site_language'] = lang
        request.session['django_language'] = lang
    except Exception:
        # If session not available, fall back to cookie
        response = redirect(next_url)
        response.set_cookie('site_language', lang)
        response.set_cookie('django_language', lang)
        return response

    return redirect(next_url)

class InvoicePDFView(View):
    @method_decorator(login_required, name='dispatch')
    def get(self, request, pk, *args, **kwargs):
        """Handle PDF generation with Arabic support using WeasyPrint"""
        invoice = get_object_or_404(Invoice, pk=pk)
        
        context = {
            'invoice': invoice,
            'STATIC_URL': settings.STATIC_URL,
        }
        
        try:
            # Load and encode logo - try production paths first
            logo_paths = [
                # Production paths (staticfiles) - tried first
                os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
                # Development paths (static)
                os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
                # Media fallback
                os.path.join(settings.BASE_DIR, 'media', 'logo.png'),
            ]
            
            logo_base64 = None
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    try:
                        with open(logo_path, 'rb') as logo_file:
                            logo_data = base64.b64encode(logo_file.read()).decode()
                            logo_base64 = f"data:image/png;base64,{logo_data}"
                            logger.info(f"Logo loaded successfully from: {logo_path}")
                            break
                    except Exception as e:
                        logger.error(f"Error reading logo from {logo_path}: {e}")
                        continue
            
            if not logo_base64:
                logger.warning("Logo could not be loaded from any path")
                    
            context['logo_base64'] = logo_base64
            
            # Render template with Arabic support
            template = get_template('portal/invoice_pdf.html')
            html_string = template.render(context)
            
            # Create CSS with Arabic font support for production (Gunicorn/Nginx)
            css_content = '''
                @page {
                    size: A4;
                    margin: 1cm;
                }
                
                body {
                    font-family: 'DejaVu Sans', serif;
                    font-size: 12px;
                    line-height: 1.4;
                    color: #333;
                }
                
                .arabic {
                    font-family: 'DejaVu Sans', serif;
                    direction: rtl;
                    display: inline-block;
                    margin-left: 5px;
                    color: #666;
                    font-size: 11px;
                }
                
                .bilingual-header {
                    font-family: 'Noto Sans Arabic', 'DejaVu Sans', Arial, sans-serif;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                    padding-bottom: 15px;
                }
                
                .header img {
                    max-height: 80px;
                    width: auto;
                    margin-bottom: 15px;
                }
                
                .company-name {
                    font-size: 1.8em;
                    font-weight: bold;
                    color: #2c3e50;
                }
                
                .invoice-info {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }
                
                th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
                
                .text-center { text-align: center; }
                .text-right { text-align: right; }
                
                .currency {
                    font-weight: bold;
                    color: #28a745;
                }
                
                .totals-section {
                    float: right;
                    width: 300px;
                    margin-top: 20px;
                }
                
                .grand-total {
                    font-weight: bold;
                    background-color: #f8f9fa;
                    border-top: 2px solid #28a745 !important;
                }
                
                .bank-details {
                    clear: both;
                    margin: 40px 0 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                
                .footer {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    text-align: center;
                    font-size: 11px;
                    color: #666;
                }
            '''
            
            # Generate PDF with proper font loading for production
            html = HTML(string=html_string)
            
            # Check if font files exist and prepare font CSS
            # Try both static/ (development) and staticfiles/ (production) directories
            font_paths_to_try = [
                # Production paths (staticfiles)
                os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', 'Amiri-Regular.ttf'),
                os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', 'amiri-regular.ttf'),
                # Development paths (static)
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf'),
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'amiri-regular.ttf'),
            ]
            
            font_path = None
            for path in font_paths_to_try:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if font_path:
                font_css_content = f'''
                    @font-face {{
                        font-family: 'Amiri';
                        src: url('file://{font_path}');
                        font-display: swap;
                    }}
                '''
                logger.info(f"Arabic font loaded from: {font_path}")
            else:
                logger.warning("Arabic font not found, falling back to DejaVu Sans")
            
            # Combine CSS with font loading
            combined_css = f'''
                {font_css_content}
                
                {css_content}
                
                body {{
                    font-family: 'Amiri', 'DejaVu Sans', serif !important;
                }}
                
                .arabic {{
                    font-family: 'Amiri', 'DejaVu Sans', serif !important;
                }}
                
                .bilingual-header {{
                    font-family: 'Amiri', 'DejaVu Sans', serif !important;
                }}
            '''
            
            main_css = CSS(string=combined_css)
            
            # Generate PDF with combined CSS
            pdf_file = html.write_pdf(stylesheets=[main_css])
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            
            # Determine if download or view
            if 'download' in request.GET or 'download/' in request.path:
                disposition = f"attachment; filename={filename}"
            else:
                disposition = f"inline; filename={filename}"
            
            response['Content-Disposition'] = disposition
            return response
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            
            # Determine if download or view
            if 'download' in request.GET or 'download/' in request.path:
                disposition = f"attachment; filename={filename}"
            else:
                disposition = f"inline; filename={filename}"
            
            response['Content-Disposition'] = disposition
            return response
            
        except Exception as e:
            logger.error(f"PDF generation exception: {str(e)}")
            return HttpResponse(f"Server error during PDF generation: {str(e)}", status=500)

@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(login_required, name='dispatch')
class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'

    def dispatch(self, request, *args, **kwargs):
        """Ensure CSRF cookie is set for all requests to this view"""
        return super().dispatch(request, *args, **kwargs)      

    def post(self, request, *args, **kwargs):
        print("\n" + "="*50)
        print("🚀 POST METHOD CALLED - INVOICE CREATION")
        print("="*50)
        print(f"Status value in POST: {request.POST.get('status')}")
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"FILES data keys: {list(request.FILES.keys())}")
        print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        
        # IMMEDIATE DEBUG - Check customer value before any processing
        raw_customer = request.POST.get('customer', '')
        print(f"🔍 IMMEDIATE CUSTOMER CHECK:")
        print(f"   Raw customer value: '{raw_customer}'")
        print(f"   Customer type: {type(raw_customer)}")
        print(f"   Customer repr: {repr(raw_customer)}")
        print(f"   Is numeric: {raw_customer.isdigit() if raw_customer else 'N/A'}")
        
        # Check all POST data for the problematic value
        print(f"🔍 SCANNING ALL POST DATA:")
        for key, value in request.POST.items():
            if '4c1eb6bdc544' in str(value):
                print(f"   ❌ FOUND PROBLEMATIC VALUE in '{key}': {repr(value)}")
            else:
                print(f"   ✅ {key}: {repr(value)}")
        
        print("="*50 + "\n")
        return super().post(request, *args, **kwargs)      

    def get_context_data(self, **kwargs):
        """Add products and customers to template context"""
        context = super().get_context_data(**kwargs)
        context.update({
            'products': Product.objects.all(),
            'customers': Customer.objects.all()[:100],  # Limit to 100 most recent
            'invoice_form': context['form']  # Add alias for backward compatibility
        })
        return context
    
    def form_valid(self, form):
        print("=== FORM_VALID CALLED ===")
        print(f"POST data: {dict(self.request.POST)}")
        print("=== STATUS DEBUG ===")
        print(f"Raw POST status: {self.request.POST.get('status')}")
        print(f"Form cleaned status: {form.cleaned_data.get('status')}")
        print(f"Form is valid: {form.is_valid()}")
        print(f"Form errors: {form.errors}")
        print(f"Is AJAX: {self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        logger.info(f"Invoice form_valid called with POST data: {dict(self.request.POST)}")
        
        # Debug: Check the status value from form
        status = form.cleaned_data.get('status', 'draft')
        print(f"🔍 Form status value: {status}")
        
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()
                print(f"Status before save: {invoice.status}") 

                if not invoice.invoice_number or invoice.invoice_number in ['Auto-generated', '']:
                    invoice.invoice_number = self._generate_invoice_number()
                    print(f"🔍 VIEW: Generated invoice number: {invoice.invoice_number}")

                if len(invoice.invoice_number) != 10 or not invoice.invoice_number.isdigit():
                    form.add_error(None, "Generated invoice number is invalid")
                    return self.form_invalid(form)
                
                invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()

                # Handle payment mode with safe decimal conversion
                payment_mode = form.cleaned_data.get('payment_mode', 'cash')
                if payment_mode == 'split':
                    try:
                        cash_amount = self.request.POST.get('cash_amount', '0').strip()
                        invoice.cash_amount = Decimal(cash_amount) if cash_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid cash amount '{self.request.POST.get('cash_amount')}', defaulting to 0")
                        invoice.cash_amount = Decimal('0')
                        
                    try:
                        pos_amount = self.request.POST.get('pos_amount', '0').strip()
                        invoice.pos_amount = Decimal(pos_amount) if pos_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid POS amount '{self.request.POST.get('pos_amount')}', defaulting to 0")
                        invoice.pos_amount = Decimal('0')
                        
                    try:
                        other_amount = self.request.POST.get('other_amount', '0').strip()
                        invoice.other_amount = Decimal(other_amount) if other_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid other amount '{self.request.POST.get('other_amount')}', defaulting to 0")
                        invoice.other_amount = Decimal('0')
                        
                    invoice.other_method = self.request.POST.get('other_method', '')

                # Handle customer with safe conversion and detailed debugging
                customer_id = self.request.POST.get('customer', '').strip()
                print(f"=== CUSTOMER DEBUG ===")
                print(f"Raw customer value: '{customer_id}'")
                print(f"Customer type: {type(customer_id)}")
                print(f"Customer length: {len(customer_id) if customer_id else 'None'}")
                
                if customer_id and customer_id != '':
                    try:
                        print(f"Attempting to convert '{customer_id}' to int...")
                        customer_id_int = int(customer_id)
                        print(f"Successfully converted to: {customer_id_int}")
                        invoice.customer_id = customer_id_int
                        logger.info(f"Assigned customer ID: {customer_id_int}")
                    except (ValueError, TypeError) as e:
                        print(f"Failed to convert '{customer_id}' to int: {e}")
                        logger.warning(f"Invalid customer ID: {customer_id}, using walk-in customer")
                        # Create or get walk-in customer
                        walk_in_customer, created = Customer.objects.get_or_create(
                            full_name='Walk-in Customer',
                            defaults={
                                'phone': '',
                                'address': ''
                            }
                        )
                        invoice.customer = walk_in_customer
                    except Customer.DoesNotExist:
                        print(f"Customer with ID {customer_id} not found")
                        logger.warning(f"Customer with ID {customer_id} not found, using walk-in customer")
                        # Create or get walk-in customer
                        walk_in_customer, created = Customer.objects.get_or_create(
                            full_name='Walk-in Customer',
                            defaults={
                                'phone': '',
                                'address': ''
                            }
                        )
                        invoice.customer = walk_in_customer
                else:
                    # Create or get walk-in customer for no customer selection
                    print("No customer selected, using walk-in customer")
                    logger.info("No customer selected, using walk-in customer")
                    walk_in_customer, created = Customer.objects.get_or_create(
                        full_name='Walk-in Customer',
                        defaults={
                            'phone': '',
                            'address': ''
                        }
                    )
                    invoice.customer = walk_in_customer

                invoice.save()
                print(f"Status after save: {invoice.status}")
                
                self._create_invoice_items(invoice)
                self._update_invoice_totals(invoice)

                return self._handle_response(invoice)

        except Exception as e:
            logger.error(f"Invoice creation error: {str(e)}")
            logger.error(f"POST data: {dict(self.request.POST)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._handle_error(e, form)
    
    def _create_invoice(self, form):
        """Create and save the invoice instance"""
        invoice = form.save(commit=False)
        
        # Set default values
        invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()
        # Use status from form instead of hardcoding to 'draft'
        invoice.status = form.cleaned_data.get('status', 'draft')
        print(f"🔍 Setting status to: {invoice.status}")
        
        # Generate invoice number if needed
        if not invoice.invoice_number or invoice.invoice_number in ['Auto-generated', '']:
            invoice.invoice_number = self._generate_invoice_number()
        
        invoice.save()
        return invoice
    
    def _generate_invoice_number(self):
        """Generate invoice number in YYYYMMDDNN format"""
        # Define date_part at the start
        date_part = timezone.now().strftime('%Y%m%d')  # YYYYMMDD format
    
        try:
            with transaction.atomic():
                # Get the highest invoice number for today
                last_invoice = Invoice.objects.filter(
                    invoice_number__startswith=date_part
                ).order_by('-invoice_number').first()
        
                if last_invoice:
                    last_num = int(last_invoice.invoice_number[-2:])  # Get last 2 digits
                    next_num = last_num + 1
                else:
                    next_num = 1
                
                # Ensure we don't exceed 99 invoices per day
                if next_num > 99:
                    raise ValueError("Maximum daily invoice limit (99) reached")
                
                new_number = f"{date_part}{next_num:02d}"
                print(f"✅ Generated new invoice number: {new_number}")
                return new_number
        except Exception as e:
            # Fallback mechanism
            fallback_num = random.randint(1, 99)
            fallback_number = f"{date_part}{fallback_num:02d}F"  # F for fallback
            print(f"🚨 Fallback invoice number generation: {fallback_number}")
            logger.error(f"Invoice number generation error: {str(e)}")
            return fallback_number

    def _create_invoice_items(self, invoice):
        """Create all associated invoice items"""
        items_data = json.loads(self.request.POST.get('items', '[]'))
        print(f"=== ITEMS DEBUG ===")
        print(f"Items JSON: {self.request.POST.get('items', '[]')}")
        print(f"Parsed items: {items_data}")
        logger.info(f"Creating invoice items: {items_data}")
        
        for item in items_data:
            print(f"=== PROCESSING ITEM ===")
            print(f"Item data: {item}")
            logger.info(f"Processing item: {item}")
            try:
                # Safely convert product ID to integer
                product_id = item.get('product', '').strip()
                print(f"Raw product ID: '{product_id}'")
                print(f"Product ID type: {type(product_id)}")
                print(f"Product ID length: {len(product_id) if product_id else 'None'}")
                
                if not product_id or product_id == '':
                    print("Skipping item with empty product ID")
                    logger.warning(f"Skipping item with empty product ID: {item}")
                    continue
                    
                try:
                    print(f"Attempting to convert '{product_id}' to int...")
                    product_id_int = int(product_id)
                    print(f"Successfully converted to: {product_id_int}")
                except (ValueError, TypeError) as e:
                    print(f"Failed to convert '{product_id}' to int: {e}")
                    logger.error(f"Invalid product ID '{product_id}' in item: {item}")
                    continue
                
                product = Product.objects.get(pk=product_id)
                logger.info(f"Found product: {product.name} (ID: {product.id})")
                
                # Safely convert quantity and price
                try:
                    quantity = int(item.get('quantity', '1'))
                    if quantity <= 0:
                        quantity = 1
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quantity '{item.get('quantity')}', defaulting to 1")
                    quantity = 1
                
                try:
                    unit_price = Decimal(str(item.get('selling_price', item.get('unit_price', product.unit_price))))
                except (ValueError, TypeError, decimal.InvalidOperation):
                    logger.warning(f"Invalid price '{item.get('unit_price')}', using product price")
                    unit_price = product.unit_price
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                logger.info(f"Created invoice item for product: {product.name}")
            except Product.DoesNotExist:
                logger.error(f"Product not found with ID: {product_id}")
                continue
            except Exception as e:
                logger.error(f"Error creating invoice item: {e}, item data: {item}")
                raise

    def _update_invoice_totals(self, invoice):
        """Update calculated invoice totals with safe decimal conversion"""
        try:
            subtotal = self.request.POST.get('subtotal', '0').strip()
            invoice.subtotal = Decimal(subtotal) if subtotal else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid subtotal '{self.request.POST.get('subtotal')}', defaulting to 0")
            invoice.subtotal = Decimal('0')
            
        try:
            discount_amount = self.request.POST.get('discount_amount', '0').strip()
            invoice.discount_amount = Decimal(discount_amount) if discount_amount else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid discount amount '{self.request.POST.get('discount_amount')}', defaulting to 0")
            invoice.discount_amount = Decimal('0')
            
        try:
            grand_total = self.request.POST.get('grand_total', '0').strip()
            invoice.grand_total = Decimal(grand_total) if grand_total else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid grand total '{self.request.POST.get('grand_total')}', defaulting to 0")
            invoice.grand_total = Decimal('0')
            
        invoice.save()
        return self._handle_response(invoice)

    def _handle_response(self, invoice):
        """Return appropriate response based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('portal:invoice_detail', kwargs={'pk': invoice.pk}),
                'invoice_number': invoice.invoice_number,
                'total_amount': str(invoice.grand_total),
                'invoice_id': invoice.pk
            })
        self.object = invoice
        return HttpResponseRedirect(reverse('portal:invoice_detail', kwargs={'pk': invoice.pk}))

    def _handle_error(self, error, form=None):
        """Handle errors appropriately based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(error)
            }, status=400)
        if form is None:
            form = self.get_form()
        return super().form_invalid(form)
    
    def form_invalid(self, form):
        print("=== FORM_INVALID CALLED ===")
        print(f"Form errors: {form.errors}")
        print(f"Form non-field errors: {form.non_field_errors()}")
        print(f"POST data: {dict(self.request.POST)}")
        print(f"Is AJAX: {self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Form validation failed'
            }, status=400)
        return super().form_invalid(form)
        
    def get_success_url(self):
        return reverse('portal:invoice_detail', kwargs={'pk': self.object.pk})


    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'

    def dispatch(self, request, *args, **kwargs):
        """Ensure CSRF cookie is set for all requests to this view"""
        return super().dispatch(request, *args, **kwargs)      

    def post(self, request, *args, **kwargs):
        print("\n" + "="*50)
        print("🚀 POST METHOD CALLED - INVOICE CREATION")
        print("="*50)
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        print(f"POST data keys: {list(request.POST.keys())}")
        print(f"FILES data keys: {list(request.FILES.keys())}")
        print(f"Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        
        # IMMEDIATE DEBUG - Check customer value before any processing
        raw_customer = request.POST.get('customer', '')
        print(f"🔍 IMMEDIATE CUSTOMER CHECK:")
        print(f"   Raw customer value: '{raw_customer}'")
        print(f"   Customer type: {type(raw_customer)}")
        print(f"   Customer repr: {repr(raw_customer)}")
        print(f"   Is numeric: {raw_customer.isdigit() if raw_customer else 'N/A'}")
        
        # Check all POST data for the problematic value
        print(f"🔍 SCANNING ALL POST DATA:")
        for key, value in request.POST.items():
            if '4c1eb6bdc544' in str(value):
                print(f"   ❌ FOUND PROBLEMATIC VALUE in '{key}': {repr(value)}")
            else:
                print(f"   ✅ {key}: {repr(value)}")
        
        print("="*50 + "\n")
        return super().post(request, *args, **kwargs)      

    def get_context_data(self, **kwargs):
        """Add products and customers to template context"""
        context = super().get_context_data(**kwargs)
        context.update({
            'products': Product.objects.all(),
            'customers': Customer.objects.all()[:100],  # Limit to 100 most recent
            'invoice_form': context['form']  # Add alias for backward compatibility
        })
        return context
    
    def form_valid(self, form):
        print("=== FORM_VALID CALLED ===")
        print(f"POST data: {dict(self.request.POST)}")
        print(f"Form is valid: {form.is_valid()}")
        print(f"Form errors: {form.errors}")
        print(f"Is AJAX: {self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        logger.info(f"Invoice form_valid called with POST data: {dict(self.request.POST)}")
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()
                # Use status from form instead of hardcoding to 'draft'
                invoice.status = form.cleaned_data.get('status', 'draft')
                print(f"🔍 VIEW: Setting status to: {invoice.status}")

                if not invoice.invoice_number or invoice.invoice_number in ['Auto-generated', '']:
                    invoice.invoice_number = self._generate_invoice_number()
                    print(f"🔍 VIEW: Generated invoice number: {invoice.invoice_number}")

                # Handle payment mode with safe decimal conversion
                payment_mode = form.cleaned_data.get('payment_mode', 'cash')
                if payment_mode == 'split':
                    try:
                        cash_amount = self.request.POST.get('cash_amount', '0').strip()
                        invoice.cash_amount = Decimal(cash_amount) if cash_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid cash amount '{self.request.POST.get('cash_amount')}', defaulting to 0")
                        invoice.cash_amount = Decimal('0')
                        
                    try:
                        pos_amount = self.request.POST.get('pos_amount', '0').strip()
                        invoice.pos_amount = Decimal(pos_amount) if pos_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid POS amount '{self.request.POST.get('pos_amount')}', defaulting to 0")
                        invoice.pos_amount = Decimal('0')
                        
                    try:
                        other_amount = self.request.POST.get('other_amount', '0').strip()
                        invoice.other_amount = Decimal(other_amount) if other_amount else Decimal('0')
                    except (ValueError, decimal.InvalidOperation):
                        logger.warning(f"Invalid other amount '{self.request.POST.get('other_amount')}', defaulting to 0")
                        invoice.other_amount = Decimal('0')
                        
                    invoice.other_method = self.request.POST.get('other_method', '')

                # Handle customer with safe conversion and detailed debugging
                customer_id = self.request.POST.get('customer', '').strip()
                print(f"=== CUSTOMER DEBUG ===")
                print(f"Raw customer value: '{customer_id}'")
                print(f"Customer type: {type(customer_id)}")
                print(f"Customer length: {len(customer_id) if customer_id else 'None'}")
                
                if customer_id and customer_id != '':
                    try:
                        print(f"Attempting to convert '{customer_id}' to int...")
                        customer_id_int = int(customer_id)
                        print(f"Successfully converted to: {customer_id_int}")
                        invoice.customer_id = customer_id_int
                        logger.info(f"Assigned customer ID: {customer_id_int}")
                    except (ValueError, TypeError) as e:
                        print(f"Failed to convert '{customer_id}' to int: {e}")
                        logger.warning(f"Invalid customer ID: {customer_id}, using walk-in customer")
                        # Create or get walk-in customer
                        walk_in_customer, created = Customer.objects.get_or_create(
                            full_name='Walk-in Customer',
                            defaults={
                                'phone': '',
                                'address': ''
                            }
                        )
                        invoice.customer = walk_in_customer
                    except Customer.DoesNotExist:
                        print(f"Customer with ID {customer_id} not found")
                        logger.warning(f"Customer with ID {customer_id} not found, using walk-in customer")
                        # Create or get walk-in customer
                        walk_in_customer, created = Customer.objects.get_or_create(
                            full_name='Walk-in Customer',
                            defaults={
                                'phone': '',
                                'address': ''
                            }
                        )
                        invoice.customer = walk_in_customer
                else:
                    # Create or get walk-in customer for no customer selection
                    print("No customer selected, using walk-in customer")
                    logger.info("No customer selected, using walk-in customer")
                    walk_in_customer, created = Customer.objects.get_or_create(
                        full_name='Walk-in Customer',
                        defaults={
                            'phone': '',
                            'address': ''
                        }
                    )
                    invoice.customer = walk_in_customer

                invoice.save()
                self._create_invoice_items(invoice)
                self._update_invoice_totals(invoice)

                return self._handle_response(invoice)

        except Exception as e:
            logger.error(f"Invoice creation error: {str(e)}")
            logger.error(f"POST data: {dict(self.request.POST)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return self._handle_error(e, form)
    
    def _create_invoice(self, form):
        """Create and save the invoice instance"""
        invoice = form.save(commit=False)
        
        # Set default values
        invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()
        # Use status from form instead of hardcoding to 'draft'
        invoice.status = form.cleaned_data.get('status', 'draft')
        print(f"🔍 Setting status to: {invoice.status}")
        
        # Generate invoice number if needed
        if not invoice.invoice_number or invoice.invoice_number in ['Auto-generated', '']:
            invoice.invoice_number = self._generate_invoice_number()
        
        invoice.save()
        return invoice
    
    def _generate_invoice_number(self):
        """Generate invoice number in YYYYMMDDNN format"""
        # Define date_part at the start
        date_part = timezone.now().strftime('%Y%m%d')  # YYYYMMDD format
    
        try:
            with transaction.atomic():
                # Get the highest invoice number for today
                last_invoice = Invoice.objects.filter(
                    invoice_number__startswith=date_part
                ).order_by('-invoice_number').first()
        
                if last_invoice:
                    last_num = int(last_invoice.invoice_number[-2:])  # Get last 2 digits
                    next_num = last_num + 1
                else:
                    next_num = 1
                
                # Ensure we don't exceed 99 invoices per day
                if next_num > 99:
                    raise ValueError("Maximum daily invoice limit (99) reached")
                
                new_number = f"{date_part}{next_num:02d}"
                print(f"✅ Generated new invoice number: {new_number}")
                return new_number
        except Exception as e:
            # Fallback mechanism
            fallback_num = random.randint(1, 99)
            fallback_number = f"{date_part}{fallback_num:02d}F"  # F for fallback
            print(f"🚨 Fallback invoice number generation: {fallback_number}")
            return fallback_number


    def _create_invoice_items(self, invoice):
        """Create all associated invoice items"""
        items_data = json.loads(self.request.POST.get('items', '[]'))
        print(f"=== ITEMS DEBUG ===")
        print(f"Items JSON: {self.request.POST.get('items', '[]')}")
        print(f"Parsed items: {items_data}")
        logger.info(f"Creating invoice items: {items_data}")
        
        for item in items_data:
            print(f"=== PROCESSING ITEM ===")
            print(f"Item data: {item}")
            logger.info(f"Processing item: {item}")
            try:
                # Safely convert product ID to integer
                product_id = item.get('product', '').strip()
                print(f"Raw product ID: '{product_id}'")
                print(f"Product ID type: {type(product_id)}")
                print(f"Product ID length: {len(product_id) if product_id else 'None'}")
                
                if not product_id or product_id == '':
                    print("Skipping item with empty product ID")
                    logger.warning(f"Skipping item with empty product ID: {item}")
                    continue
                    
                try:
                    print(f"Attempting to convert '{product_id}' to int...")
                    product_id_int = int(product_id)
                    print(f"Successfully converted to: {product_id_int}")
                except (ValueError, TypeError) as e:
                    print(f"Failed to convert '{product_id}' to int: {e}")
                    logger.error(f"Invalid product ID '{product_id}' in item: {item}")
                    continue
                
                product = Product.objects.get(pk=product_id)
                logger.info(f"Found product: {product.name} (ID: {product.id})")
                
                # Safely convert quantity and price
                try:
                    quantity = int(item.get('quantity', '1'))
                    if quantity <= 0:
                        quantity = 1
                except (ValueError, TypeError):
                    logger.warning(f"Invalid quantity '{item.get('quantity')}', defaulting to 1")
                    quantity = 1
                
                try:
                    unit_price = Decimal(str(item.get('selling_price', item.get('unit_price', product.unit_price))))
                except (ValueError, TypeError, decimal.InvalidOperation):
                    logger.warning(f"Invalid price '{item.get('unit_price')}', using product price")
                    unit_price = product.unit_price
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                logger.info(f"Created invoice item for product: {product.name}")
            except Product.DoesNotExist:
                logger.error(f"Product not found with ID: {product_id}")
                continue
            except Exception as e:
                logger.error(f"Error creating invoice item: {e}, item data: {item}")
                raise

    def _update_invoice_totals(self, invoice):
        """Update calculated invoice totals with safe decimal conversion"""
        try:
            subtotal = self.request.POST.get('subtotal', '0').strip()
            invoice.subtotal = Decimal(subtotal) if subtotal else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid subtotal '{self.request.POST.get('subtotal')}', defaulting to 0")
            invoice.subtotal = Decimal('0')
            
        try:
            discount_amount = self.request.POST.get('discount_amount', '0').strip()
            invoice.discount_amount = Decimal(discount_amount) if discount_amount else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid discount amount '{self.request.POST.get('discount_amount')}', defaulting to 0")
            invoice.discount_amount = Decimal('0')
            
        try:
            grand_total = self.request.POST.get('grand_total', '0').strip()
            invoice.grand_total = Decimal(grand_total) if grand_total else Decimal('0')
        except (ValueError, decimal.InvalidOperation):
            logger.warning(f"Invalid grand total '{self.request.POST.get('grand_total')}', defaulting to 0")
            invoice.grand_total = Decimal('0')
            
        invoice.save()

    def _handle_response(self, invoice):
        """Return appropriate response based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('portal:invoice_detail', kwargs={'pk': invoice.pk}),
                'invoice_number': invoice.invoice_number,
                'total_amount': str(invoice.grand_total),
                'invoice_id': invoice.pk
            })
        self.object = invoice
        return HttpResponseRedirect(reverse('portal:invoice_detail', kwargs={'pk': invoice.pk}))

    def _handle_error(self, error, form=None):
        """Handle errors appropriately based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': str(error)
            }, status=400)
        if form is None:
            form = self.get_form()
        return super().form_invalid(form)
    
    def form_invalid(self, form):
        print("=== FORM_INVALID CALLED ===")
        print(f"Form errors: {form.errors}")
        print(f"Form non-field errors: {form.non_field_errors()}")
        print(f"POST data: {dict(self.request.POST)}")
        print(f"Is AJAX: {self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'message': 'Form validation failed'
            }, status=400)
        return super().form_invalid(form)
        
    def get_success_url(self):
        return reverse('portal:invoice_detail', kwargs={'pk': self.object.pk})

@method_decorator(login_required, name='dispatch')
class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'products': Product.objects.filter(is_active=True),
            'existing_items': self.object.items.select_related('product'),
            'Invoice': Invoice  # Make the model class available in template
        })
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                
                # Update payment details if split payment
                if invoice.payment_mode == 'split':
                    invoice.cash_amount = form.cleaned_data.get('cash_amount', 0)
                    invoice.pos_amount = form.cleaned_data.get('pos_amount', 0)
                    invoice.other_amount = form.cleaned_data.get('other_amount', 0)
                    invoice.other_method = form.cleaned_data.get('other_method', '')
                
                # Save the invoice first
                invoice.save()
                
                # Process invoice items
                self._process_invoice_items(invoice)
                
                # Update totals from form data
                invoice.subtotal = form.cleaned_data.get('subtotal', 0)
                invoice.tax = form.cleaned_data.get('tax', 0)
                invoice.discount_type = form.cleaned_data.get('discount_type', 'amount')
                discount_value = form.cleaned_data.get('discount_value', 0)
                print(f"DEBUG: discount_value from form: {discount_value} (type: {type(discount_value)})")
                invoice.discount_value = discount_value if discount_value is not None else 0
                invoice.discount_amount = form.cleaned_data.get('discount_amount', 0)
                invoice.grand_total = form.cleaned_data.get('grand_total', 0)
                print(f"DEBUG: invoice.discount_value before save: {invoice.discount_value}")
                invoice.save()
                
                messages.success(self.request, f"Invoice #{invoice.invoice_number} updated successfully!")
                return redirect('portal:invoice_detail', pk=invoice.pk)
                
        except Exception as e:
            logger.error(f"Invoice update error: {str(e)}", exc_info=True)
            messages.error(self.request, f"Error updating invoice: {str(e)}")
            return self.form_invalid(form)

    def _process_invoice_items(self, invoice):
        """Process all invoice item changes (create/update/delete)"""
        items_data = json.loads(self.request.POST.get('items', '[]'))
        existing_ids = set(invoice.items.values_list('id', flat=True))
        updated_ids = set()
        
        for item_data in items_data:
            if item_data.get('id'):
                # Update existing item
                self._update_existing_item(invoice, item_data)
                updated_ids.add(int(item_data['id']))
            else:
                # Create new item
                self._create_new_item(invoice, item_data)
        
        # Delete removed items
        self._delete_removed_items(invoice, existing_ids, updated_ids)

    def _update_existing_item(self, invoice, item_data):
        """Update an existing invoice item"""
        try:
            product = Product.objects.get(pk=item_data['product'])
            InvoiceItem.objects.filter(
                id=item_data['id'],
                invoice=invoice
            ).update(
                product=product,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=Decimal(item_data['quantity']) * Decimal(item_data['unit_price'])
            )
        except (Product.DoesNotExist, KeyError, ValueError) as e:
            logger.error(f"Error updating invoice item: {str(e)}")
            raise

    def _create_new_item(self, invoice, item_data):
        """Create a new invoice item"""
        try:
            product = Product.objects.get(pk=item_data['product'])
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=Decimal(item_data['quantity']) * Decimal(item_data['unit_price'])
            )
        except (Product.DoesNotExist, KeyError, ValueError) as e:
            logger.error(f"Error creating invoice item: {str(e)}")
            raise

    def _delete_removed_items(self, invoice, existing_ids, updated_ids):
        """Delete items that were removed from the invoice"""
        items_to_delete = existing_ids - updated_ids
        if items_to_delete:
            invoice.items.filter(id__in=items_to_delete).delete()


@method_decorator(login_required, name='dispatch')
class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'portal/invoice_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object
        context['items'] = invoice.items.select_related('product')
        
        # Add calculated fields for template
        context.update({
            'subtotal': invoice.subtotal,
            'tax_amount': invoice.tax,
            'discount_amount': invoice.discount_amount,
            'grand_total': invoice.grand_total,
            'status_display': invoice.get_status_display()
        })
        return context

@method_decorator(login_required, name='dispatch')
class InvoiceListView(ListView):
    model = Invoice
    template_name = 'portal/invoice_list.html'
    paginate_by = 25
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Check if any filters are active
        filters_active = any([
            self.request.GET.get('date_from'),
            self.request.GET.get('date_to'),
            self.request.GET.get('status'),
            self.request.GET.get('payment_mode')
        ])
        
        # Default to recent invoices (last 7 days) if no filters
        if not filters_active:
            last_week = timezone.now() - timezone.timedelta(days=7)
            queryset = queryset.filter(date__gte=last_week)
        
        # Date range filtering
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from and date_to:
            queryset = queryset.filter(date__range=[date_from, date_to])
        elif date_from:
            queryset = queryset.filter(date__gte=date_from)
        elif date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        # Status filter
        status = self.request.GET.get('status')
        if status in dict(Invoice.INVOICE_STATUS).keys():
            queryset = queryset.filter(status=status)
            
        # Payment mode filter
        payment_mode = self.request.GET.get('payment_mode')
        if payment_mode in dict(Invoice.PAYMENT_MODES).keys():
            queryset = queryset.filter(payment_mode=payment_mode)
            
        return queryset.select_related('customer')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        # Calculate summary statistics in single query
        aggregates = queryset.aggregate(
            total_amount=Sum('grand_total'),
            paid_amount=Sum('grand_total', filter=Q(status='paid')),
            pending_amount=Sum('grand_total', filter=~Q(status__in=['paid', 'cancelled']))
        )
        
        context.update({
            'total_invoices': queryset.count(),
            'paid_invoices': queryset.filter(status='paid').count(),
            'pending_invoices': queryset.exclude(status__in=['paid', 'cancelled']).count(),
            'total_amount': aggregates['total_amount'] or 0,
            'paid_amount': aggregates['paid_amount'] or 0,
            'pending_amount': aggregates['pending_amount'] or 0,
            # Current filter values for template
            'current_status': self.request.GET.get('status', ''),
            'current_payment_mode': self.request.GET.get('payment_mode', ''),
            'current_date_from': self.request.GET.get('date_from', ''),
            'current_date_to': self.request.GET.get('date_to', ''),
        })
        return context


@method_decorator(login_required, name='dispatch')
class InvoiceDeleteView(DeleteView):
    model = Invoice
    success_url = reverse_lazy('portal:invoice_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(site=self.request.site)
    
    def delete(self, request, *args, **kwargs):
        # Get the object before deletion for success message
        self.object = self.get_object()
        invoice_number = self.object.invoice_number
        
        # Perform the deletion
        response = super().delete(request, *args, **kwargs)
        
        # Add success message
        messages.success(request, f'Invoice #{invoice_number} has been deleted successfully.')
        
        return response


@login_required
def get_product_details(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'cost_price': str(product.cost_price),
        'selling_price': str(product.selling_price),
        'image_url': product.image.url if product.image else None
    })

@login_required
def enquiry(request):
    if request.method == 'POST':
        form = ProductEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save(commit=False)
            enquiry.save()
            messages.success(request, f'Thank you {enquiry.name}! Your enquiry about {enquiry.subject} has been submitted.')
            return redirect('enquiry')
    else:
        form = ProductEnquiryForm()
    
    return render(request, 'portal/enquiry.html', {'form': form})

#home view
def home(request):
    return render(request, 'portal/home.html', {
        'featured_products': Product.objects.filter(is_active=True)[:4]
    })

def register(request):
    return render(request, 'portal/register.html')

def terms(request):
    return render(request, 'portal/terms.html')

@login_required
def profile(request):
    return render(request, 'portal/profile.html', {
        'featured_products': Product.objects.filter(is_active=True)[:4]
    })

@method_decorator(login_required, name='dispatch')
class ProductSearchView(ListView):
    model = Product
    template_name = 'portal/products/search.html'  # Updated path to follow Django conventions
    context_object_name = 'products'  # Explicitly set context variable name
    paginate_by = 10  # Add pagination

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if not query:
            return Product.objects.none()  # Return empty queryset if no query
            
        return Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__iexact=query),
            is_active=True
        ).select_related('category')  # Optimize DB queries

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

@login_required
def product_search_fallback(request):
    return render(request, 'portal/products/search_empty.html')

@csrf_exempt  # For simplicity in development, remove in production with proper CSRF handling
@require_http_methods(["POST"])
@login_required
def barcode_scan(request):
    """
    Enhanced barcode scanner that fetches complete product details including:
    - Product information (name, SKU, description)
    - Stock availability
    - Cost price and selling price
    - Category information
    - Profit calculations
    """
    barcode_data = request.POST.get('barcode', '').strip()
    
    if not barcode_data:
        return JsonResponse({'error': 'No barcode data provided'}, status=400)
    
    try:
        # Get product with related category information
        product = Product.objects.select_related('category').get(barcode=barcode_data)
        
        # Calculate profit margin and amount
        profit_margin = product.profit_margin()
        profit_amount = product.profit_amount()
        
        # Determine stock status with proper labels
        if product.stock > 10:
            stock_status = 'In Stock'
        elif product.stock > 0:
            stock_status = 'Low Stock'
        else:
            stock_status = 'Out of Stock'
        
        response_data = {
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'description': product.description,
                'barcode': product.barcode,
                
                # Pricing information
                'cost_price': str(product.cost_price),
                'selling_price': str(product.selling_price),
                'profit_margin': f"{profit_margin:.1f}%" if profit_margin else "0.0%",
                'profit_amount': str(profit_amount) if profit_amount else "0.00",
                
                # Stock information
                'stock': product.stock,
                'stock_status': stock_status,
                'is_active': product.is_active,
                
                # Category information
                'category_name': product.category.name if product.category else 'Uncategorized',
                'category_description': product.category.description if product.category else '',
                'category_icon': product.category.icon if product.category else '',
                
                # Additional information
                'warranty': f"{product.warranty_period} months" if product.warranty_period else "No warranty",
                'image_url': product.image.url if product.image else None,
                
                # Legacy field for backward compatibility
                'legacy_price': str(product.selling_price),  # Keep for existing code
            }
        }
        
        return JsonResponse(response_data)
        
    except Product.DoesNotExist:
        return JsonResponse({
            'error': 'Product not found',
            'barcode': barcode_data,
            'suggestions': 'Please check the barcode number or add this product to inventory'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': f'An unexpected error occurred: {str(e)}',
            'barcode': barcode_data
        }, status=500)

# customer search
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def customer_search(request):
    print(f"🔍 customer_search called with query: {request.GET.get('q', '')}")
    query = request.GET.get('q', '')
    
    if not query:
        print("❌ No query provided")
        return JsonResponse({'customers': []})
    
    print(f"📡 Searching for customers with query: {query}")
    customers = Customer.objects.filter(
        Q(full_name__icontains=query) | 
        Q(company_name__icontains=query) |
        Q(customer_id__icontains=query) |
        Q(phone__icontains=query)
    ).order_by('company_name', 'full_name')[:10]
    
    print(f"✅ Found {customers.count()} customers")
    results = []
    for customer in customers:
        results.append({
            'id': customer.id,
            'display_text': customer.company_name or customer.full_name,
            'phone': customer.phone,
            'tax_number': customer.tax_number,
            'address': customer.address,
        })
    
    print(f"📤 Returning results: {results}")
    return JsonResponse({'customers': results})

# BarcodeScanner
@login_required
def barcode_scanner_view(request):
    """Render the barcode scanner interface page"""
    return render(request, 'portal/barcode_scanner.html')

def custom_logout(request):
    """Custom logout view that properly clears session and redirects"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('/')

# Multi-tenant index view
@login_required
def index(request):
    """
    Main index view that renders site-specific templates
    """
    # Get the current site
    site_name = getattr(request, 'company_short', 'TRENDZ')
    
    # Add featured products to context (like the home view does)
    from .models import Product
    context = {
        'site_name': getattr(request, 'company_name', 'TRENDZ Portal'),
        'featured_products': Product.objects.filter(is_active=True)[:4]
    }
    
    # Try to render site-specific template first
    site_template = None
    if site_name == 'Al Malika':
        site_template = 'sites/almalika/index.html'
    else:
        site_template = 'sites/portal/index.html'
    
    # First check if the site-specific template exists
    from django.template.loader import get_template
    from django.template import TemplateDoesNotExist
    
    try:
        # Try site-specific template
        get_template(site_template)
        return render(request, site_template, context)
    except TemplateDoesNotExist:
        try:
            # Try generic template
            get_template('index.html')
            return render(request, 'index.html', context)
        except TemplateDoesNotExist:
            # Final fallback to portal/home.html
            return render(request, 'portal/home.html', context)

# Dashboard and Report Views

@dashboard_access_required
def dashboard_view(request):
    """
    Comprehensive dashboard with business metrics and recent activity
    """
    # Calculate date ranges
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # Basic counts
    total_customers = Customer.objects.count()  # No is_active field for Customer
    active_products = Product.objects.filter(is_active=True).count()
    active_suppliers = Supplier.objects.filter(is_active=True).count()
    
    # Invoice metrics
    pending_invoices = Invoice.objects.filter(
        status__in=['draft', 'pending']
    ).count()
    
    # Monthly revenue (current month)
    monthly_revenue = Invoice.objects.filter(
        date__gte=current_month_start,  # Use 'date' not 'invoice_date'
        status='paid'
    ).aggregate(total=Sum('grand_total'))['total'] or 0
    
    # Purchase order metrics
    pending_purchase_orders = PurchaseOrder.objects.filter(
        status__in=['draft', 'ordered']
    ).count()
    
    # Recent invoices (last 10)
    recent_invoices = Invoice.objects.select_related(
        'customer'
    ).order_by('-date')[:10]  # Use 'date' instead of 'created_at'
    
    # Recent purchase orders (last 10)
    recent_purchase_orders = PurchaseOrder.objects.select_related(
        'supplier'
    ).order_by('-created_at')[:10]
    
    # Low stock products (stock <= 10)
    low_stock_products = Product.objects.filter(
        stock__lte=10,
        is_active=True
    ).order_by('stock')[:10]
    
    # Top selling products (this month)
    top_products = InvoiceItem.objects.filter(
        invoice__date__gte=current_month_start,  # Use 'date' not 'invoice_date'
        invoice__status='paid'
    ).values(
        'product__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_qty')[:5]
    
    # Recent customers (last 10 registered)
    recent_customers = Customer.objects.order_by('-created_at')[:5]  # No is_active field
    
    # Enhanced Product Analytics
    # Total inventory value (cost price * stock)
    total_inventory_cost_value = Product.objects.filter(
        is_active=True
    ).aggregate(
        total_value=Sum(F('cost_price') * F('stock'))
    )['total_value'] or 0
    
    # Total inventory value (selling price * stock)  
    total_inventory_value = Product.objects.filter(
        is_active=True
    ).aggregate(
        total_value=Sum(F('unit_price') * F('stock'))
    )['total_value'] or 0
    
    # Potential profit
    potential_profit = total_inventory_value - total_inventory_cost_value
    
    # Average cost price
    avg_cost_price = Product.objects.filter(
        is_active=True
    ).aggregate(avg_cost=Avg('cost_price'))['avg_cost'] or 0

    # Average product cost (selling price)
    avg_product_cost = Product.objects.filter(
        is_active=True
    ).aggregate(avg_cost=Avg('unit_price'))['avg_cost'] or 0
    
    # Average profit margin
    avg_profit_margin = 0
    if avg_cost_price > 0:
        avg_profit_margin = ((avg_product_cost - avg_cost_price) / avg_cost_price) * 100

    # Products by category count with cost analysis
    products_by_category = Product.objects.filter(
        is_active=True
    ).values('category__name').annotate(
        count=Count('id'),
        total_cost_value=Sum(F('cost_price') * F('stock')),
        total_value=Sum(F('unit_price') * F('stock')),
        profit=Sum((F('unit_price') - F('cost_price')) * F('stock')),
        avg_cost=Avg('cost_price'),
        avg_selling=Avg('unit_price')
    ).annotate(
        profit_margin=Case(
            When(avg_cost__gt=0, then=(F('avg_selling') - F('avg_cost')) / F('avg_cost') * 100),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-count')[:5]
    
    # Procurement Analytics
    total_purchase_orders = PurchaseOrder.objects.count()
    total_procurement_value = PurchaseOrder.objects.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # This month's procurement
    monthly_procurement = PurchaseOrder.objects.filter(
        order_date__gte=current_month_start
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Average order value
    avg_order_value = 0
    if total_purchase_orders > 0:
        avg_order_value = total_procurement_value / total_purchase_orders
    
    # Recent products (last 10 added) with profit calculations
    recent_products = Product.objects.filter(
        is_active=True
    ).annotate(
        profit_margin_calc=Case(
            When(cost_price__gt=0, then=(F('unit_price') - F('cost_price')) / F('cost_price') * 100),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-id')[:10]
    
    # High value products (top 10 by cost) with profit calculations
    high_value_products = Product.objects.filter(
        is_active=True
    ).annotate(
        profit_per_unit=F('unit_price') - F('cost_price'),
        total_cost_value=F('cost_price') * F('stock'),
        total_selling_value=F('unit_price') * F('stock')
    ).order_by('-unit_price')[:10]
    
    # Monthly comparison data
    last_month_revenue = Invoice.objects.filter(
        date__gte=last_month_start,  # Use 'date' not 'invoice_date'
        date__lte=last_month_end,
        status='paid'
    ).aggregate(total=Sum('grand_total'))['total'] or 0
    
    revenue_change = 0
    if last_month_revenue > 0:
        revenue_change = ((monthly_revenue - last_month_revenue) / last_month_revenue) * 100
    
    context = {
        'total_customers': total_customers,
        'pending_invoices': pending_invoices,
        'monthly_revenue': monthly_revenue,
        'active_products': active_products,
        'active_suppliers': active_suppliers,
        'pending_purchase_orders': pending_purchase_orders,
        'recent_invoices': recent_invoices,
        'recent_purchase_orders': recent_purchase_orders,
        'low_stock_products': low_stock_products,
        'top_products': top_products,
        'recent_customers': recent_customers,
        'revenue_change': revenue_change,
        'last_month_revenue': last_month_revenue,
        'current_month': current_month_start.strftime('%B %Y'),
        'total_inventory_value': total_inventory_value,
        'total_inventory_cost_value': total_inventory_cost_value,
        'potential_profit': potential_profit,
        'avg_product_cost': avg_product_cost,
        'avg_cost_price': avg_cost_price,
        'avg_profit_margin': avg_profit_margin,
        'products_by_category': products_by_category,
        'recent_products': recent_products,
        'high_value_products': high_value_products,
        'total_purchase_orders': total_purchase_orders,
        'total_procurement_value': total_procurement_value,
        'monthly_procurement': monthly_procurement,
        'avg_order_value': avg_order_value,
    }
    
    # Render enhanced dashboard with improved styling
    return render(request, 'portal/dashboard_enhanced.html', context)

@dashboard_access_required
def analytics_api(request):
    """
    API endpoint for dashboard analytics data (for AJAX updates)
    """
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # Get period (default to current month)
    period = request.GET.get('period', 'month')
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'quarter':
        start_date = current_month_start - timedelta(days=90)
    elif period == 'year':
        start_date = current_month_start.replace(month=1)
    else:  # month
        start_date = current_month_start
    
    # Revenue trend data
    revenue_data = []
    for i in range(30):  # Last 30 days
        date = today - timedelta(days=i)
        daily_revenue = Invoice.objects.filter(
            date=date,  # Use 'date' not 'invoice_date'
            status='paid'
        ).aggregate(total=Sum('grand_total'))['total'] or 0
        
        revenue_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'revenue': float(daily_revenue)
        })
    
    # Top customers by revenue
    top_customers = Customer.objects.annotate(
        total_revenue=Sum('invoice__grand_total', filter=Q(
            invoice__status='paid',
            invoice__date__gte=start_date  # Use 'date' not 'invoice_date'
        ))
    ).filter(total_revenue__isnull=False).order_by('-total_revenue')[:5]
    
    customer_data = [
        {
            'name': customer.full_name,
            'revenue': float(customer.total_revenue or 0)
        }
        for customer in top_customers
    ]
    
    return JsonResponse({
        'revenue_trend': revenue_data,
        'top_customers': customer_data,
    })


@dashboard_access_required
def dashboard_summary_api(request):
    """
    Returns rendered HTML for the dashboard summary (cards/tables) so the main dashboard can load quickly
    and fetch heavy data asynchronously.
    """
    # Build the same heavy context used previously but keep it minimal and efficient
    total_customers = Customer.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    active_suppliers = Supplier.objects.filter(is_active=True).count()
    pending_invoices = Invoice.objects.filter(status__in=['draft', 'pending']).count()

    monthly_revenue = Invoice.objects.filter(
        date__gte=timezone.now().date().replace(day=1),
        status='paid'
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    # Product/Procurement aggregates (limited sets)
    total_inventory_cost_value = Product.objects.filter(is_active=True).aggregate(total_value=Sum(F('cost_price') * F('stock')))['total_value'] or 0
    total_inventory_value = Product.objects.filter(is_active=True).aggregate(total_value=Sum(F('unit_price') * F('stock')))['total_value'] or 0
    potential_profit = total_inventory_value - total_inventory_cost_value

    total_purchase_orders = PurchaseOrder.objects.count()
    total_procurement_value = PurchaseOrder.objects.aggregate(total=Sum('total'))['total'] or 0
    monthly_procurement = PurchaseOrder.objects.filter(order_date__gte=timezone.now().date().replace(day=1)).aggregate(total=Sum('total'))['total'] or 0
    avg_order_value = 0
    if total_purchase_orders > 0:
        avg_order_value = total_procurement_value / total_purchase_orders

    products_by_category = Product.objects.filter(is_active=True).values('category__name').annotate(
        count=Count('id'),
        total_cost_value=Sum(F('cost_price') * F('stock')),
        total_value=Sum(F('unit_price') * F('stock')),
        profit=Sum((F('unit_price') - F('cost_price')) * F('stock'))
    ).order_by('-count')[:5]

    high_value_products = Product.objects.filter(is_active=True).annotate(
        profit_per_unit=F('unit_price') - F('cost_price'),
        total_cost_value=F('cost_price') * F('stock'),
        total_selling_value=F('unit_price') * F('stock')
    ).order_by('-unit_price')[:10]

    ctx = {
        'total_customers': total_customers,
        'pending_invoices': pending_invoices,
        'monthly_revenue': monthly_revenue,
        'active_products': active_products,
        'active_suppliers': active_suppliers,
        'total_inventory_cost_value': total_inventory_cost_value,
        'total_inventory_value': total_inventory_value,
        'potential_profit': potential_profit,
        'total_purchase_orders': total_purchase_orders,
        'total_procurement_value': total_procurement_value,
        'monthly_procurement': monthly_procurement,
        'avg_order_value': avg_order_value,
        'products_by_category': products_by_category,
        'high_value_products': high_value_products,
    }

    html = render(request, 'portal/_dashboard_summary.html', ctx).content.decode('utf-8')
    return JsonResponse({'html': html})

@reports_access_required
def report_view(request):
    """
    Comprehensive reports with filtering capabilities
    """
    # Get filter parameters
    customer_id = request.GET.get('customer_id')
    supplier_id = request.GET.get('supplier_id')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    report_type = request.GET.get('report_type', 'invoice')
    
    # Base querysets
    invoices = Invoice.objects.select_related('customer').order_by('-date')
    purchase_orders = PurchaseOrder.objects.select_related('supplier').order_by('-order_date')
    
    # Apply filters
    filters = {}
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
        filters['customer_id'] = customer_id
        
    if supplier_id:
        purchase_orders = purchase_orders.filter(supplier_id=supplier_id)
        filters['supplier_id'] = supplier_id
        
    if status:
        invoices = invoices.filter(status=status)
        purchase_orders = purchase_orders.filter(status=status)
        filters['status'] = status
        
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(date__gte=date_from_obj)
            purchase_orders = purchase_orders.filter(order_date__gte=date_from_obj)
            filters['date_from'] = date_from
        except ValueError:
            pass
            
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(date__lte=date_to_obj)
            purchase_orders = purchase_orders.filter(order_date__lte=date_to_obj)
            filters['date_to'] = date_to
        except ValueError:
            pass
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = 25
    
    if report_type == 'purchase_order':
        paginator = Paginator(purchase_orders, items_per_page)
        page_obj = paginator.get_page(page)
        
        # Purchase order statistics
        total_count = purchase_orders.count()
        total_amount = purchase_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        avg_amount = purchase_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Status breakdown
        status_breakdown = purchase_orders.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        )
        
        stats = {
            'total_count': total_count,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_breakdown': status_breakdown,
        }
    else:
        # Default to invoice report
        paginator = Paginator(invoices, items_per_page)
        page_obj = paginator.get_page(page)
        
        # Invoice statistics
        total_count = invoices.count()
        total_amount = invoices.aggregate(total=Sum('grand_total'))['total'] or 0
        avg_amount = invoices.aggregate(avg=Avg('grand_total'))['avg'] or 0
        
        # Status breakdown
        status_breakdown = invoices.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('grand_total')
        )
        
        stats = {
            'total_count': total_count,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_breakdown': status_breakdown,
        }
    
    # Get choices for dropdowns
    customers = Customer.objects.order_by('full_name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    invoice_status_choices = Invoice.INVOICE_STATUS
    purchase_order_status_choices = [
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Calculate cost value based on product cost prices (from inventory)
    total_cost_value = InvoiceItem.objects.filter(
        invoice__in=invoices.filter(status='paid')
    ).aggregate(
        total_cost=Sum(F('quantity') * F('product__cost_price'))
    )['total_cost'] or 0
    
    # Revenue from invoices (in filtered period if applicable)
    total_revenue = invoices.filter(status='paid').aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    
    # Gross profit and margin
    gross_profit = total_revenue - total_cost_value
    gross_margin = 0
    if total_revenue > 0:
        gross_margin = (gross_profit / total_revenue) * 100
    # Use total_revenue from invoices (grand_total), not from InvoiceItem/unit_price
    # total_revenue = invoices.filter(status='paid').aggregate(
    #     total=Sum('grand_total')
    # )['total'] or 0
    total_revenue = invoices.filter(status='paid').aggregate(
        total=Sum('grand_total')
    )['total'] or 0    
    # Gross profit and margin
    # Daily breakdown (using InvoiceItem)
    daily_gross_profit = (
        InvoiceItem.objects.filter(invoice__status='paid')
        .annotate(date=TruncDate('invoice__date'))
        .values('date')
        .annotate(
            sales_value=Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
            cost_value=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField()),
        )
        .annotate(
            gross_profit=F('sales_value') - F('cost_value'),
            margin=Case(
                When(sales_value__gt=0, then=(F('gross_profit') / F('sales_value')) * 100),
                default=0,
                output_field=DecimalField(max_digits=5, decimal_places=1)
            )
        )
        .order_by('date')
    )
    # Monthly breakdown
    monthly_gross_profit = (
        InvoiceItem.objects.filter(invoice__status='paid')
        .annotate(month=TruncMonth('invoice__date'))
        .values('month')
        .annotate(
            sales_value=Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
            cost_value=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField()),
        )
        .annotate(
            gross_profit=F('sales_value') - F('cost_value'),
            margin=Case(
                When(sales_value__gt=0, then=(F('gross_profit') / F('sales_value')) * 100),
                default=0,
                output_field=DecimalField(max_digits=5, decimal_places=1)
            )
        )
        .order_by('month')
    )

    # Add to context:
    context = {}
    context['daily_gross_profit'] = daily_gross_profit
    context['monthly_gross_profit'] = monthly_gross_profit
    
    # Category analysis - using 'items' as related_name
    category_analysis = InvoiceItem.objects.filter(
        invoice__in=invoices.filter(status='paid')
    ).values('product__category__name').annotate(
        count=Count('id'),
        total_qty=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('product__cost_price')),
        total_revenue=Sum(F('quantity') * F('unit_price')),
        avg_cost=Avg('product__cost_price'),
        avg_selling=Avg('unit_price')
    ).annotate(
        margin=Case(
            When(avg_cost__gt=0, then=(F('avg_selling') - F('avg_cost')) / F('avg_cost') * 100),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-total_revenue')[:10]

    # Top products
    top_products = InvoiceItem.objects.filter(
        invoice__status='paid'
    ).values(
        'product__name', 
        'product__cost_price'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price')),
        total_cost=Sum(F('quantity') * F('product__cost_price'))
    ).annotate(
        total_profit=F('total_revenue') - F('total_cost'),
        margin=Case(
            When(total_revenue__gt=0, then=(F('total_profit') / F('total_revenue')) * 100),
            default=0,
            output_field=DecimalField(max_digits=5, decimal_places=1)
        )
    ).order_by('-total_revenue')[:10]

    # Invoice and PO totals for summary cards
    invoice_totals = {
        'count': invoices.count(),
        'total_amount': invoices.aggregate(total=Sum('grand_total'))['total'] or 0
    }
    
    po_totals = {
        'count': purchase_orders.count(),
        'total_amount': purchase_orders.aggregate(total=Sum('total'))['total'] or 0
    }
    

    # Calculate profit metrics
    total_profit = gross_profit
    profit_margin = gross_margin
    avg_margin = 0
    
    if category_analysis:
        avg_margin = sum(cat['margin'] or 0 for cat in category_analysis) / len(category_analysis)
    
    # Define daily_profit_breakdown using the same queryset as daily_gross_profit for compatibility
    daily_profit_breakdown = daily_gross_profit

    # Define monthly_profit_breakdown using similar logic, grouped by month
    monthly_profit_breakdown = (
        InvoiceItem.objects.filter(invoice__status='paid')
        .annotate(month=TruncMonth('invoice__date'))
        .values('month')
        .annotate(
            sales_value=Sum(F('quantity') * F('unit_price'), output_field=DecimalField()),
            cost_value=Sum(F('quantity') * F('product__cost_price'), output_field=DecimalField()),
        )
        .annotate(
            gross_profit=F('sales_value') - F('cost_value'),
            margin=Case(
                When(sales_value__gt=0, then=(F('gross_profit') / F('sales_value')) * 100),
                default=0,
                output_field=DecimalField(max_digits=5, decimal_places=1)
            )
        )
        .order_by('month')
    )

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filters': filters,
        'customers': customers,
        'suppliers': suppliers,
        'invoice_status_choices': invoice_status_choices,
        'purchase_order_status_choices': purchase_order_status_choices,
        'report_type': report_type,
        'current_filters': request.GET,
        'invoice_totals': invoice_totals,
        'po_totals': po_totals,
        'total_cost_value': total_cost_value,
        'total_revenue': total_revenue,
        'gross_profit': gross_profit,
        'gross_margin': gross_margin,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'avg_margin': avg_margin,
        'total_costs': total_cost_value,
        'category_analysis': category_analysis,
        'top_products': top_products,
        'daily_profit_breakdown': daily_profit_breakdown,
        'monthly_profit_breakdown': monthly_profit_breakdown,
        'invoices': invoices[:50],
        'purchase_orders': purchase_orders[:50],
    }
    
    return render(request, 'portal/report.html', context)

@login_required
def export_reports(request):
    export_type = request.GET.get('export', 'invoices')
    
    # Get filters from request
    filters = {
        'customer_id': request.GET.get('customer_id'),
        'supplier_id': request.GET.get('supplier_id'),
        'status': request.GET.get('status'),
        'date_from': request.GET.get('date_from'),
        'date_to': request.GET.get('date_to'),
    }
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{export_type}_export_{timezone.now().date()}.csv"'
    
    writer = csv.writer(response)
    
    if export_type == 'invoices':
        # Filter invoices based on request parameters
        invoices = Invoice.objects.all()
        
        if filters['customer_id']:
            invoices = invoices.filter(customer_id=filters['customer_id'])
        if filters['date_from']:
            invoices = invoices.filter(date__gte=filters['date_from'])
        if filters['date_to']:
            invoices = invoices.filter(date__lte=filters['date_to'])
        if filters['status']:
            invoices = invoices.filter(status=filters['status'])
        
        # Write CSV header
        writer.writerow([
            'Invoice Number', 'Customer', 'Date', 
            'Subtotal', 'Tax', 'Discount', 'Grand Total', 
            'Status', 'Payment Status', 'Created At'
        ])
        
        # Write data rows
        for invoice in invoices:
            writer.writerow([
                invoice.invoice_number,
                invoice.customer.full_name if invoice.customer else '',
                invoice.date.strftime('%Y-%m-%d'),
                invoice.subtotal,
                invoice.tax_amount,
                invoice.discount_amount,
                invoice.grand_total,
                invoice.get_status_display(),
                invoice.get_payment_status_display(),
                invoice.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    elif export_type == 'purchase_orders':
        # Filter purchase orders
        purchase_orders = PurchaseOrder.objects.all()
        
        if filters['supplier_id']:
            purchase_orders = purchase_orders.filter(supplier_id=filters['supplier_id'])
        if filters['date_from']:
            purchase_orders = purchase_orders.filter(order_date__gte=filters['date_from'])
        if filters['date_to']:
            purchase_orders = purchase_orders.filter(order_date__lte=filters['date_to'])
        if filters['status']:
            purchase_orders = purchase_orders.filter(status=filters['status'])
        
        # Write CSV header
        writer.writerow([
            'PO Reference', 'Supplier', 'Order Date', 
            'Delivery Date', 'Total Amount', 'Status', 
            'Created At', 'Created By'
        ])
        
        # Write data rows
        for po in purchase_orders:
            writer.writerow([
                po.reference,
                po.supplier.name if po.supplier else '',
                po.order_date.strftime('%Y-%m-%d'),
                po.delivery_date.strftime('%Y-%m-%d') if po.delivery_date else '',
                po.total,
                po.get_status_display(),
                po.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                po.created_by.get_full_name() if po.created_by else ''
            ])
    
    elif export_type == 'payments':
        # Filter payments
        payments = Payment.objects.all()
        
        if filters['date_from']:
            payments = payments.filter(payment_date__gte=filters['date_from'])
        if filters['date_to']:
            payments = payments.filter(payment_date__lte=filters['date_to'])
        
        # Write CSV header
        writer.writerow([
            'Payment Date', 'PO Reference', 'Supplier', 
            'Amount', 'Payment Method', 'Reference', 
            'Notes', 'Created At'
        ])
        
        # Write data rows
        for payment in payments:
            writer.writerow([
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.purchase_order.reference if payment.purchase_order else '',
                payment.purchase_order.supplier.name if payment.purchase_order and payment.purchase_order.supplier else '',
                payment.amount,
                payment.get_payment_method_display(),
                payment.reference or '',
                payment.notes or '',
                payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return response

'''
@reports_access_required
def report_view(request):
    """
    Comprehensive reports with filtering capabilities
    """
    # Get filter parameters
    customer_id = request.GET.get('customer_id')
    supplier_id = request.GET.get('supplier_id')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    report_type = request.GET.get('report_type', 'invoice')
    
    # Base querysets
    invoices = Invoice.objects.select_related('customer').order_by('-date')
    purchase_orders = PurchaseOrder.objects.select_related('supplier').order_by('-order_date')
    
    # Apply filters
    filters = {}
    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
        filters['customer_id'] = customer_id
        
    if supplier_id:
        purchase_orders = purchase_orders.filter(supplier_id=supplier_id)
        filters['supplier_id'] = supplier_id
        
    if status:
        invoices = invoices.filter(status=status)
        purchase_orders = purchase_orders.filter(status=status)
        filters['status'] = status
        
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            invoices = invoices.filter(date__gte=date_from_obj)
            purchase_orders = purchase_orders.filter(order_date__gte=date_from_obj)
            filters['date_from'] = date_from
        except ValueError:
            pass
            
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(date__lte=date_to_obj)
            purchase_orders = purchase_orders.filter(order_date__lte=date_to_obj)
            filters['date_to'] = date_to
        except ValueError:
            pass
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = 25
    
    if report_type == 'purchase_order':
        paginator = Paginator(purchase_orders, items_per_page)
        page_obj = paginator.get_page(page)
        
        # Purchase order statistics
        total_count = purchase_orders.count()
        total_amount = purchase_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        avg_amount = purchase_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Status breakdown
        status_breakdown = purchase_orders.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('total_amount')
        )
        
        stats = {
            'total_count': total_count,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_breakdown': status_breakdown,
        }
    else:
        # Default to invoice report
        paginator = Paginator(invoices, items_per_page)
        page_obj = paginator.get_page(page)
        
        # Invoice statistics
        total_count = invoices.count()
        total_amount = invoices.aggregate(total=Sum('grand_total'))['total'] or 0
        avg_amount = invoices.aggregate(avg=Avg('grand_total'))['avg'] or 0
        
        # Status breakdown
        status_breakdown = invoices.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('grand_total')
        )
        
        stats = {
            'total_count': total_count,
            'total_amount': total_amount,
            'avg_amount': avg_amount,
            'status_breakdown': status_breakdown,
        }
    
    # Get choices for dropdowns
    customers = Customer.objects.order_by('full_name')
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    invoice_status_choices = Invoice.INVOICE_STATUS
    purchase_order_status_choices = [
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Enhanced Analytics for Reports
    # Calculate cost value based on product cost prices (from inventory)
    total_cost_value = InvoiceItem.objects.filter(
        invoice__in=invoices.filter(status='paid')
    ).aggregate(
        total_cost=Sum(F('quantity') * F('product__cost_price'))
    )['total_cost'] or 0
    
    # Revenue from invoices (in filtered period if applicable)
    total_revenue = invoices.filter(status='paid').aggregate(
        total=Sum('grand_total')
    )['total'] or 0
    
    # Gross profit and margin
    gross_profit = total_revenue - total_cost_value
    gross_margin = 0
    if total_revenue > 0:
        gross_margin = (gross_profit / total_revenue) * 100
    
    # Daily Profit Breakdown - using 'items' as related_name
    daily_profit_breakdown = Invoice.objects.filter(
        status='paid',
        date__gte=date_from_obj if date_from else timezone.now().date() - timedelta(days=30),
        date__lte=date_to_obj if date_to else timezone.now().date()
    ).annotate(
        date_trunc=TruncDate('date')
    ).values('date_trunc').annotate(
        sales_value=Sum('grand_total'),
        cost_value=Sum(
            F('items__quantity') * F('items__product__cost_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        invoice_count=Count('id')
    ).annotate(
        gross_profit=F('sales_value') - F('cost_value'),
        margin=Case(
            When(sales_value__gt=0, then=(F('gross_profit') / F('sales_value')) * 100),
            default=0,
            output_field=DecimalField(max_digits=5, decimal_places=1)
        )
    ).order_by('-date_trunc')

    # Monthly Profit Breakdown - using 'items' as related_name
    monthly_profit_breakdown = Invoice.objects.filter(
        status='paid'
    ).annotate(
        month_trunc=TruncMonth('date')
    ).values('month_trunc').annotate(
        sales_value=Sum('grand_total'),
        cost_value=Sum(
            F('items__quantity') * F('items__product__cost_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        ),
        invoice_count=Count('id')
    ).annotate(
        gross_profit=F('sales_value') - F('cost_value'),
        margin=Case(
            When(sales_value__gt=0, then=(F('gross_profit') / F('sales_value')) * 100),
            default=0,
            output_field=DecimalField(max_digits=5, decimal_places=1)
        )
    ).order_by('-month_trunc')[:12]

    # Category analysis - using 'items' as related_name
    category_analysis = InvoiceItem.objects.filter(
        invoice__in=invoices.filter(status='paid')
    ).values('product__category__name').annotate(
        count=Count('id'),
        total_qty=Sum('quantity'),
        total_cost=Sum(F('quantity') * F('product__cost_price')),
        total_revenue=Sum(F('quantity') * F('unit_price')),
        avg_cost=Avg('product__cost_price'),
        avg_selling=Avg('unit_price')
    ).annotate(
        margin=Case(
            When(avg_cost__gt=0, then=(F('avg_selling') - F('avg_cost')) / F('avg_cost') * 100),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).order_by('-total_revenue')[:10]

    # Top products
    top_products = InvoiceItem.objects.filter(
        invoice__status='paid'
    ).values(
        'product__name', 
        'product__cost_price'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price')),
        total_cost=Sum(F('quantity') * F('product__cost_price'))
    ).annotate(
        total_profit=F('total_revenue') - F('total_cost'),
        margin=Case(
            When(total_revenue__gt=0, then=(F('total_profit') / F('total_revenue')) * 100),
            default=0,
            output_field=DecimalField(max_digits=5, decimal_places=1)
        )
    ).order_by('-total_revenue')[:10]

    # Invoice and PO totals for summary cards
    invoice_totals = {
        'count': invoices.count(),
        'total_amount': invoices.aggregate(total=Sum('grand_total'))['total'] or 0
    }
    
    po_totals = {
        'count': purchase_orders.count(),
        'total_amount': purchase_orders.aggregate(total=Sum('total'))['total'] or 0
    }
    
    # Calculate profit metrics
    total_profit = gross_profit
    profit_margin = gross_margin
    avg_margin = 0
    
    if category_analysis:
        avg_margin = sum(cat['margin'] or 0 for cat in category_analysis) / len(category_analysis)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filters': filters,
        'customers': customers,
        'suppliers': suppliers,
        'invoice_status_choices': invoice_status_choices,
        'purchase_order_status_choices': purchase_order_status_choices,
        'report_type': report_type,
        'current_filters': request.GET,
        'invoice_totals': invoice_totals,
        'po_totals': po_totals,
        'total_cost_value': total_cost_value,
        'total_revenue': total_revenue,
        'gross_profit': gross_profit,
        'gross_margin': gross_margin,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'avg_margin': avg_margin,
        'total_costs': total_cost_value,
        'category_analysis': category_analysis,
        'top_products': top_products,
        'daily_profit_breakdown': daily_profit_breakdown,
        'monthly_profit_breakdown': monthly_profit_breakdown,
        'invoices': invoices[:50],
        'purchase_orders': purchase_orders[:50],
    }
    
    return render(request, 'portal/report.html', context)
'''

# Customer Management Views
@method_decorator(login_required, name='dispatch')
class CustomerListView(ListView):
    model = Customer
    template_name = 'portal/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Customer.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(company_name__icontains=search)
            )
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context

@method_decorator(login_required, name='dispatch')
class CustomerCreateView(CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'portal/customer_create.html'
    
    def get_success_url(self):
        # If this is an AJAX request from invoice creation, return JSON
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return None
        return reverse('portal:customer_list')
    
    def form_valid(self, form):
        customer = form.save()
        
        # Handle AJAX request from invoice creation
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.full_name,
                    'phone': customer.phone,
                    'display_text': f"{customer.full_name} - {customer.phone}"
                }
            })
        
        messages.success(self.request, f'Customer "{customer.full_name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)

@method_decorator(login_required, name='dispatch')
class CustomerDetailView(DetailView):
    model = Customer
    template_name = 'portal/customer_detail.html'
    context_object_name = 'customer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get customer's invoices
        context['invoices'] = Invoice.objects.filter(
            customer=self.object
        ).order_by('-date')[:10]  # Last 10 invoices
        return context

@method_decorator(login_required, name='dispatch')
class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'portal/customer_create.html'  # Reuse create template
    
    def get_success_url(self):
        return reverse('portal:customer_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Customer "{form.instance.full_name}" updated successfully!')
        return super().form_valid(form)


# =============================================================================
# PRODUCT MANAGEMENT VIEWS
# =============================================================================

@method_decorator(login_required, name='dispatch')
class ProductListView(ListView):
    """Frontend product list view with filtering and search"""
    model = Product
    template_name = 'portal/products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('-id')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(barcode__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Stock status filter
        stock_status = self.request.GET.get('stock_status', '')
        if stock_status == 'in_stock':
            queryset = queryset.filter(stock__gt=10)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(stock__lte=10, stock__gt=0)
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(stock=0)
        
        # Active status filter
        is_active = self.request.GET.get('is_active', '')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from portal.models import Category
        
        context.update({
            'categories': Category.objects.all(),
            'current_category': self.request.GET.get('category', ''),
            'current_search': self.request.GET.get('q', ''),
            'current_stock_status': self.request.GET.get('stock_status', ''),
            'current_is_active': self.request.GET.get('is_active', ''),
            'total_products': Product.objects.count(),
            'active_products': Product.objects.filter(is_active=True).count(),
            'low_stock_products': Product.objects.filter(stock__lte=10, stock__gt=0).count(),
            'out_of_stock_products': Product.objects.filter(stock=0).count(),
        })
        return context


@method_decorator(login_required, name='dispatch')
class ProductDetailView(DetailView):
    """Frontend product detail view"""
    model = Product
    template_name = 'portal/products/product_detail.html'
    context_object_name = 'product'
    
    def get_template_names(self):
        """Always use the public product detail template (storefront) for all users."""
        return ['portal/products/public_product_detail.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get related products from same category
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:6]
        
        # Base context used by admin/internal template
        context.update({
            'related_products': related_products,
            'profit_margin': product.profit_margin(),
            'profit_amount': product.profit_amount(),
        })

        # If this view is rendering the public template for a regular user,
        # provide the additional context keys the public template expects.
        try:
            template_names = self.get_template_names()
            if 'portal/products/public_product_detail.html' in template_names:
                from django.utils.translation import get_language
                lang_param = self.request.GET.get('lang')
                lang = lang_param or get_language()
                use_ar = bool(lang and str(lang).lower().startswith('ar'))
                display_name = product.name_ar if use_ar and getattr(product, 'name_ar', None) else product.name
                display_description = product.description_ar if use_ar and getattr(product, 'description_ar', None) else product.description

                product_url = self.request.build_absolute_uri(
                    reverse('portal:public_product_detail', kwargs={'pk': product.pk})
                )
                if lang_param:
                    sep = '&' if '?' in product_url else '?'
                    product_url = f"{product_url}{sep}lang={lang_param}"

                context.update({
                    'product_url': product_url,
                    'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97444444444'),
                    'whatsapp_message': f"Hi! I'm interested in {display_name} (SKU: {product.sku}). Can you provide more details?",
                    'product_display_name': display_name,
                    'product_display_description': display_description,
                })
        except Exception:
            # If anything goes wrong adding public context, leave base context as-is
            pass
        return context


class PublicProductCatalogView(ListView):
    """Public product catalog view for e-commerce functionality"""
    model = Product
    template_name = 'portal/products/public_catalog.html'
    context_object_name = 'products'
    paginate_by = 24  # More products per page for grid view
    
    def get_queryset(self):
        # Only show active products with stock > 0
        queryset = Product.objects.filter(
            is_active=True,
            stock__gt=0
        ).select_related('category').order_by('-id')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(barcode__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Price range filter
        min_price = self.request.GET.get('min_price', '')
        max_price = self.request.GET.get('max_price', '')
        if min_price:
            try:
                queryset = queryset.filter(unit_price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                queryset = queryset.filter(unit_price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'price_low':
            queryset = queryset.order_by('unit_price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-unit_price')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'popular':
            # For now, order by stock (higher stock = more popular)
            queryset = queryset.order_by('-stock')
        else:  # newest (default)
            queryset = queryset.order_by('-id')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from portal.models import Category
        
        # Get categories that have active products
        categories = Category.objects.filter(
            product__is_active=True,
            product__stock__gt=0
        ).distinct()
        
        # Get price range for filters
        products = Product.objects.filter(is_active=True, stock__gt=0)
        price_range = products.aggregate(
            min_price=Min('unit_price'),
            max_price=Max('unit_price')
        )
        
        context.update({
            'categories': categories,
            'current_category': self.request.GET.get('category', ''),
            'current_search': self.request.GET.get('q', ''),
            'current_sort': self.request.GET.get('sort', 'newest'),
            'current_min_price': self.request.GET.get('min_price', ''),
            'current_max_price': self.request.GET.get('max_price', ''),
            'price_range': price_range,
            'total_products': products.count(),
            'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97444444444'),  # Default Qatar number
        })
        return context


class PublicProductDetailView(DetailView):
    """Public product detail view for e-commerce functionality"""
    model = Product
    template_name = 'portal/products/public_product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        # Only show active products
        return Product.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get related products from same category
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True,
            stock__gt=0
        ).exclude(id=product.id)[:6]
        
        # Determine preferred language from ?lang= or from Django's active language
        from django.utils.translation import get_language
        lang_param = self.request.GET.get('lang')
        lang = lang_param or get_language()

        # Choose localized product fields when Arabic requested and translation exists
        use_ar = bool(lang and str(lang).lower().startswith('ar'))
        display_name = product.name_ar if use_ar and getattr(product, 'name_ar', None) else product.name
        display_description = product.description_ar if use_ar and getattr(product, 'description_ar', None) else product.description

        # Create product URL for sharing (preserve ?lang param if present)
        product_url = self.request.build_absolute_uri(
            reverse('portal:public_product_detail', kwargs={'pk': product.pk})
        )
        if lang_param:
            sep = '&' if '?' in product_url else '?'
            product_url = f"{product_url}{sep}lang={lang_param}"

        context.update({
            'related_products': related_products,
            'product_url': product_url,
            'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97444444444'),
            'whatsapp_message': f"Hi! I'm interested in {display_name} (SKU: {product.sku}). Can you provide more details?",
            'product_display_name': display_name,
            'product_display_description': display_description,
            # Note: attachments are not provided by default
        })
        # Attachments/discovery removed in revert - no additional context changes

        return context


@method_decorator(login_required, name='dispatch')
class ProductCreateView(CreateView):
    """Frontend product creation view"""
    model = Product
    template_name = 'portal/products/product_form.html'
    fields = [
        'category', 'name', 'name_ar', 'sku', 'description', 'description_ar', 'cost_price', 
        'unit_price', 'stock', 'image', 'warranty_period', 
        'barcode', 'is_active'
    ]
    
    def get_success_url(self):
        return reverse('portal:product_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from portal.models import Category
        context['categories'] = Category.objects.all()
        context['form_action'] = 'Create'
        return context


@method_decorator(login_required, name='dispatch')
class ProductUpdateView(UpdateView):
    """Frontend product update view"""
    model = Product
    template_name = 'portal/products/product_form.html'
    fields = [
        'category', 'name', 'name_ar', 'sku', 'description', 'description_ar', 'cost_price', 
        'unit_price', 'stock', 'image', 'warranty_period', 
        'barcode', 'is_active'
    ]
    
    def get_success_url(self):
        return reverse('portal:product_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Product "{form.instance.name}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from portal.models import Category
        context['categories'] = Category.objects.all()
        context['form_action'] = 'Update'
        return context


@require_http_methods(["POST"])
@login_required
def product_delete(request, pk):
    """Delete product via AJAX"""
    try:
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Product "{product_name}" deleted successfully!'
            })
        else:
            messages.success(request, f'Product "{product_name}" deleted successfully!')
            return redirect('portal:product_list')
            
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': f'Error deleting product: {str(e)}'
            })
        else:
            messages.error(request, f'Error deleting product: {str(e)}')
            return redirect('portal:product_list')


@require_http_methods(["POST"])
@login_required
def product_toggle_active(request, pk):
    """Toggle product active status via AJAX"""
    try:
        product = get_object_or_404(Product, pk=pk)
        product.is_active = not product.is_active
        product.save()
        
        return JsonResponse({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product "{product.name}" {"activated" if product.is_active else "deactivated"} successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error updating product: {str(e)}'
        })


@login_required
def product_dashboard(request):
    """Product management dashboard"""
    from django.db.models import Sum, Avg, Count
    from portal.models import Category
    
    # Get statistics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(stock__lte=10, stock__gt=0).count()
    out_of_stock_products = Product.objects.filter(stock=0).count()
    total_stock_value = Product.objects.aggregate(
        total_value=Sum(F('cost_price') * F('stock'))
    )['total_value'] or 0
    
    # Recent products
    recent_products = Product.objects.order_by('-id')[:5]
    
    # Low stock products
    low_stock_list = Product.objects.filter(stock__lte=10).order_by('stock')[:10]
    
    # Category breakdown
    category_stats = Category.objects.annotate(
        product_count=Count('product'),
        total_stock=Sum('product__stock')
    ).order_by('-product_count')[:5]
    
    # Price analysis
    price_stats = Product.objects.aggregate(
        avg_cost=Avg('cost_price'),
        avg_unit=Avg('unit_price'),
        min_price=Min('unit_price'),
        max_price=Max('unit_price')
    )
    # Compute average margin (absolute and percent) safely here so templates don't need custom filters
    avg_cost = price_stats.get('avg_cost') or 0
    avg_unit = price_stats.get('avg_unit') or 0
    try:
        avg_margin = avg_unit - avg_cost
        margin_percent = (avg_margin / avg_cost) * 100 if avg_cost and avg_cost != 0 else 0
    except Exception:
        avg_margin = 0
        margin_percent = 0
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'total_stock_value': total_stock_value,
        'recent_products': recent_products,
        'low_stock_list': low_stock_list,
        'category_stats': category_stats,
        'price_stats': price_stats,
        'avg_margin': avg_margin,
        'margin_percent': margin_percent,
    }
    
    return render(request, 'portal/products/product_dashboard.html', context)