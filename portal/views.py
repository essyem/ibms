# portal/views.py
from django.views import View
from django.views.generic import (CreateView, UpdateView, 
ListView, DetailView, View)
from .models import Invoice, InvoiceItem, Product, Customer
from django.db.models import Sum, Q
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductEnquiryForm, InvoiceForm, InvoiceItemForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse, path
from django.template.loader import get_template, render_to_string
from io import BytesIO
from django.http import HttpResponse
from django.http import Http404
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


class InvoicePDFView(View):
    def pdf_actions(self, obj):
        """Admin action links for PDF viewing/downloading"""
        return format_html(
            '<a class="button" href="{}" target="_blank">View PDF</a>&nbsp;'
            '<a class="button" href="{}?download=true" download>Download PDF</a>',
            reverse('admin:invoice_pdf', args=[obj.pk]),
            reverse('admin:invoice_pdf', args=[obj.pk])
        )
    pdf_actions.short_description = 'PDF Actions'

    def get_urls(self):
        """URL patterns for PDF viewing/downloading"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/pdf/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf'),
            path('<int:pk>/pdf/download/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf_download'),
        ]
        return custom_urls + urls

    def get(self, request, *args, **kwargs):
        """Handle PDF generation with Arabic support using WeasyPrint"""
        invoice = get_object_or_404(Invoice, pk=self.kwargs['pk'])
        
        context = {
            'invoice': invoice,
            'STATIC_URL': settings.STATIC_URL,
        }
        
        try:
            # Load and encode logo
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
            logo_base64 = None
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = base64.b64encode(logo_file.read()).decode()
                    logo_base64 = f"data:image/png;base64,{logo_data}"
                    
            context['logo_base64'] = logo_base64
            
            # Render template with Arabic support
            template = get_template('portal/invoice_pdf.html')
            html_string = template.render(context)
            
            # Use WeasyPrint for better Arabic support
            # Use a safer base_url approach
            try:
                base_url = request.build_absolute_uri('/')
            except:
                # Fallback for test environments
                base_url = 'http://localhost:8000/'
            
            html = HTML(string=html_string, base_url=base_url)
            
            # Embed Arabic font as base64 for reliable loading
            font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')
            
            try:
                with open(font_path, 'rb') as f:
                    font_data = base64.b64encode(f.read()).decode()
                font_src = f'data:font/truetype;charset=utf-8;base64,{font_data}'
            except Exception as e:
                logger.error(f"Could not load font file: {e}")
                font_src = None
            
            if font_src:
                css_content = f'''
                    @font-face {{
                        font-family: 'Amiri';
                        src: url('{font_src}') format('truetype');
                        font-weight: normal;
                        font-style: normal;
                        font-display: swap;
                    }}
                    
                    body {{
                        font-family: 'DejaVu Sans', Arial, sans-serif;
                        font-size: 12px;
                    }}
                    
                    .arabic {{
                        font-family: 'Amiri', 'Traditional Arabic', 'Arabic Typesetting', sans-serif !important;
                        direction: rtl;
                        text-align: right;
                        unicode-bidi: embed;
                        font-feature-settings: "liga" 1, "calt" 1, "kern" 1, "curs" 1;
                        -webkit-font-feature-settings: "liga" 1, "calt" 1, "kern" 1, "curs" 1;
                        -moz-font-feature-settings: "liga" 1, "calt" 1, "kern" 1, "curs" 1;
                        font-size: 14px;
                        line-height: 1.8;
                        font-weight: 400;
                        text-rendering: optimizeLegibility;
                        -webkit-text-size-adjust: 100%;
                        -ms-text-size-adjust: 100%;
                    }}
                    
                    .bilingual .arabic {{
                        font-family: 'Amiri', sans-serif !important;
                    }}
                    
                    @page {{
                        size: A4;
                        margin: 1cm;
                    }}
                '''
            else:
                # Fallback CSS without custom font
                css_content = '''
                    body {
                        font-family: 'DejaVu Sans', Arial, sans-serif;
                        font-size: 12px;
                    }
                    
                    .arabic {
                        font-family: 'Traditional Arabic', 'Arabic Typesetting', Arial, sans-serif !important;
                        direction: rtl;
                        text-align: right;
                        unicode-bidi: embed;
                        font-size: 14px;
                        line-height: 1.8;
                    }
                    
                    @page {
                        size: A4;
                        margin: 1cm;
                    }
                '''
            
            css = CSS(string=css_content)
            
            # Generate PDF
            pdf_file = html.write_pdf(stylesheets=[css])
            
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

class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'      

    def get_context_data(self, **kwargs):
        """Add products and customers to template context"""
        context = super().get_context_data(**kwargs)
        context.update({
            'products': Product.objects.all(),
            'customers': Customer.objects.all()[:100]  # Limit to 100 most recent
        })
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                invoice = form.save(commit=False)
                invoice.due_date = form.cleaned_data.get('due_date') or timezone.now().date()
                invoice.status = 'draft'

                if not invoice.invoice_number or invoice.invoice_number == 'Auto-generated':
                    invoice.invoice_number = self._generate_invoice_number()

                if form.cleaned_data.get('payment_mode') == 'split':
                    invoice.cash_amount = Decimal(self.request.POST.get('cash_amount', 0))
                    invoice.pos_amount = Decimal(self.request.POST.get('pos_amount', 0))
                    invoice.other_amount = Decimal(self.request.POST.get('other_amount', 0))
                    invoice.other_method = self.request.POST.get('other_method', '')

                invoice.save()
                self._create_invoice_items(invoice)
                self._update_invoice_totals(invoice)

                return self._handle_response(invoice)

        except Exception as e:
            logger.error(f"Invoice creation error: {str(e)}")
            return self._handle_error(e, form)
        return super().form_valid(form)
    
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
        """Generate sequential invoice number"""
        last_invoice = Invoice.objects.order_by('-id').first()
        last_num = int(last_invoice.invoice_number.split('-')[-1]) if last_invoice else 0
        return f"INV-{timezone.now().year}-{last_num + 1:04d}"

    def _create_invoice_items(self, invoice):
        """Create all associated invoice items"""
        items_data = json.loads(self.request.POST.get('items', '[]'))
        for item in items_data:
            product = Product.objects.get(pk=item['product'])
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=item['quantity'],
                selling_price=item['selling_price'],
                cost_price=item['cost_price']
            )

    def _update_invoice_totals(self, invoice):
        """Update calculated invoice totals"""
        invoice.subtotal = Decimal(self.request.POST.get('subtotal', 0))
        invoice.discount_amount = Decimal(self.request.POST.get('discount_amount', 0))
        invoice.grand_total = Decimal(self.request.POST.get('grand_total', 0))
        invoice.save()

    def _handle_response(self, invoice):
        """Return appropriate response based on request type"""
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'redirect_url': self.get_success_url(),
                'invoice_number': invoice.invoice_number
            })
        self.object = invoice
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
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})

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
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})

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
    barcode_data = request.POST.get('barcode', '').strip()
    
    if not barcode_data:
        return JsonResponse({'error': 'No barcode data provided'}, status=400)
    
    try:
        product = Product.objects.get(barcode=barcode_data)
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': str(product.price),
                'image_url': product.image.url if product.image else None
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Adding a fallback view for empty searches


# BarcodeScanner
def barcode_scanner_view(request):
    """Render the barcode scanner interface page"""
    return render(request, 'portal/barcode_scanner.html')