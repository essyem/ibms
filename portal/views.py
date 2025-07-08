# portal/views.py
from django.views import View
from django.views.generic import (CreateView, UpdateView, 
ListView, DetailView, View)
from .models import Invoice, InvoiceItem, Product, Customer
from django.db.models import Sum, Q, Avg, Count, F
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductEnquiryForm, InvoiceForm, InvoiceItemForm, CustomerForm
from django.contrib import messages
import decimal
from decimal import Decimal
from django.http import JsonResponse, HttpResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
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

from weasyprint import HTML, CSS
from django.conf import settings

logger = logging.getLogger(__name__)




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


class InvoicePDFView(View):
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
                invoice.status = 'draft'

                if not invoice.invoice_number or invoice.invoice_number == 'Auto-generated':
                    invoice.invoice_number = self._generate_invoice_number()

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
        invoice.status = 'draft'
        
        # Generate invoice number if needed
        if not invoice.invoice_number or invoice.invoice_number == 'Auto-generated':
            invoice.invoice_number = self._generate_invoice_number()
        
        invoice.save()
        return invoice

    def _generate_invoice_number(self):
        """Generate sequential invoice number with robust error handling"""
        try:
            last_invoice = Invoice.objects.order_by('-id').first()
            last_num = 0
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    # Try to extract numeric part from invoice number
                    parts = last_invoice.invoice_number.split('-')
                    if len(parts) >= 2:
                        # Try to convert the last part to integer
                        last_part = parts[-1]
                        if last_part.isdigit():
                            last_num = int(last_part)
                        else:
                            print(f"⚠️ Non-numeric invoice suffix found: '{last_part}', starting fresh sequence")
                            last_num = 0
                    else:
                        print(f"⚠️ Unexpected invoice number format: '{last_invoice.invoice_number}', starting fresh sequence")
                        last_num = 0
                except (ValueError, AttributeError) as e:
                    print(f"⚠️ Error parsing invoice number '{last_invoice.invoice_number}': {e}")
                    last_num = 0
            
            new_number = f"INV-{timezone.now().year}-{last_num + 1:04d}"
            print(f"✅ Generated new invoice number: {new_number}")
            return new_number
            
        except Exception as e:
            # Fallback to timestamp-based number if all else fails
            fallback_number = f"INV-{timezone.now().year}-{timezone.now().timestamp():.0f}"
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

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'
    
    def get_context_data(self, **kwargs):
        """Add products, customers, and existing items to template context"""
        context = super().get_context_data(**kwargs)
        context.update({
            'products': Product.objects.filter(is_active=True),
            'customers': Customer.objects.filter(is_active=True),
            'existing_items': self.object.items.select_related('product')
        })
        return context
    
    def form_valid(self, form):
        """Handle invoice update with transaction safety"""
        try:
            with transaction.atomic():
                invoice = form.save()
                self._process_invoice_items(invoice)
                invoice.update_totals()
                
                return self._handle_response()
                
        except Exception as e:
            logger.error(f"Invoice update error: {str(e)}")
            return self._handle_error(e)

    def _process_invoice_items(self, invoice):
        """Process all invoice item changes (create/update/delete)"""
        items_data = json.loads(self.request.POST.get('items', '[]'))
        existing_ids = set(invoice.items.values_list('id', flat=True))
        updated_ids = set()
        
        for item_data in items_data:
            if item_data.get('id'):
                self._update_existing_item(invoice, item_data)
                updated_ids.add(int(item_data['id']))
            else:
                self._create_new_item(invoice, item_data)
        
        self._delete_removed_items(invoice, existing_ids, updated_ids)

    def _update_existing_item(self, invoice, item_data):
        """Update an existing invoice item"""
        product = Product.objects.get(pk=item_data['product'])
        InvoiceItem.objects.filter(
            id=item_data['id'],
            invoice=invoice
        ).update(
            product=product,
            quantity=item_data['quantity'],
            selling_price=item_data['selling_price'],
            cost_price=product.cost_price
        )

    def _create_new_item(self, invoice, item_data):
        """Create a new invoice item"""
        product = Product.objects.get(pk=item_data['product'])
        InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            quantity=item_data['quantity'],
            selling_price=item_data['selling_price'],
            cost_price=product.cost_price
        )

    def _delete_removed_items(self, invoice, existing_ids, updated_ids):
        """Delete items that were removed from the invoice"""
        items_to_delete = existing_ids - updated_ids
        if items_to_delete:
            invoice.items.filter(id__in=items_to_delete).delete()

    def _handle_response(self):
        """Return appropriate response based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url()
            })
        return super().form_valid(self.get_form())

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
      
    def get_success_url(self):
        return reverse('portal:invoice_detail', kwargs={'pk': self.object.pk})

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

class InvoiceListView(ListView):
    model = Invoice
    template_name = 'portal/invoice_list.html'
    paginate_by = 25
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Status filter
        status = self.request.GET.get('status')
        if status in dict(Invoice.INVOICE_STATUS).keys():
            queryset = queryset.filter(status=status)
            
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(customer__name__icontains=search) |
                Q(items__product__name__icontains=search)
            ).distinct()
            
        return queryset.select_related('customer').prefetch_related('items')




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


def profile(request):
    return render(request, 'portal/profile.html', {
        'featured_products': Product.objects.filter(is_active=True)[:4]
    })


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

def product_search_fallback(request):
    return render(request, 'portal/products/search_empty.html')
# views.py - add new imports and view


@csrf_exempt  # For simplicity in development, remove in production with proper CSRF handling
@require_http_methods(["POST"])
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

# Adding a fallback view for empty searches


# BarcodeScanner
def barcode_scanner_view(request):
    """Render the barcode scanner interface page"""
    return render(request, 'portal/barcode_scanner.html')

# Multi-tenant index view
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
from django.contrib.auth.decorators import login_required
from .decorators import superuser_required, dashboard_access_required, reports_access_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum, Avg, F, Q
from datetime import datetime, timedelta
from procurement.models import Supplier, PurchaseOrder
from django.core.paginator import Paginator

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
    total_inventory_value = Product.objects.filter(
        is_active=True
    ).aggregate(
        total_value=Sum(F('unit_price') * F('stock'))
    )['total_value'] or 0
    
    # Average product cost
    avg_product_cost = Product.objects.filter(
        is_active=True
    ).aggregate(avg_cost=Avg('unit_price'))['avg_cost'] or 0
    
    # Products by category count
    products_by_category = Product.objects.filter(
        is_active=True
    ).values('category__name').annotate(
        count=Count('id'),
        total_value=Sum(F('unit_price') * F('stock'))
    ).order_by('-count')[:5]
    
    # Recent products (last 10 added)
    recent_products = Product.objects.filter(
        is_active=True
    ).order_by('-id')[:10]
    
    # High value products (top 10 by cost)
    high_value_products = Product.objects.filter(
        is_active=True
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
        'avg_product_cost': avg_product_cost,
        'products_by_category': products_by_category,
        'recent_products': recent_products,
        'high_value_products': high_value_products,
    }
    
    return render(request, 'portal/dashboard.html', context)

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
    invoices = Invoice.objects.select_related('customer').order_by('-date')  # Use 'date' not 'invoice_date'
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
            invoices = invoices.filter(date__gte=date_from_obj)  # Use 'date' not 'invoice_date'
            purchase_orders = purchase_orders.filter(order_date__gte=date_from_obj)
            filters['date_from'] = date_from
        except ValueError:
            pass
            
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            invoices = invoices.filter(date__lte=date_to_obj)  # Use 'date' not 'invoice_date'
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
    customers = Customer.objects.order_by('full_name')  # No is_active field for Customer
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    invoice_status_choices = Invoice.INVOICE_STATUS  # Use correct field name
    purchase_order_status_choices = [  # Define choices since PurchaseOrder doesn't have STATUS_CHOICES
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
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
    }
    
    return render(request, 'portal/report.html', context)

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

# Customer Management Views
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

class CustomerUpdateView(UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'portal/customer_create.html'  # Reuse create template
    
    def get_success_url(self):
        return reverse('portal:customer_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'Customer "{form.instance.full_name}" updated successfully!')
        return super().form_valid(form)