# portal/views.py
from django.views.generic import (CreateView, UpdateView, 
ListView, DetailView, View)
from .models import Invoice, Product
from django.db.models import Q
from .models import Product  # Make sure to import your Product model
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductEnquiryForm, InvoiceForm, InvoiceItemForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse, path
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.http import HttpResponse
from django.http import Http404
from django.conf import settings
from django.utils.html import format_html


class InvoicePDFView(View):
    def pdf_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>&nbsp;'
            '<a class="button" href="{}" download>Download</a>',
            reverse('admin:invoice_pdf', args=[obj.pk]),
            reverse('admin:invoice_pdf_download', args=[obj.pk])
        )
    pdf_actions.short_description = 'Actions'
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/pdf/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf'),
            path('<int:pk>/pdf/download/',
                self.admin_site.admin_view(InvoicePDFView.as_view()),
                name='invoice_pdf_download'),
     ]
# Invoice PDF generation view
class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=self.kwargs['pk'])
        template = get_template('portal/invoice_pdf.html')
        context = {'invoice': invoice}
        html = template.render(context)
        
        # Create PDF
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            if request.GET.get('download'):
                content = f"attachment; filename={filename}"
            else:
                content = f"inline; filename={filename}"
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Error generating PDF", status=400)
# Ensure you have the necessary imports for your views
class InvoiceCreateView(CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(is_active=True)
        return context
    
    def get_success_url(self):
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})

class InvoiceUpdateView(UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'portal/invoice_create.html'
    
    def get_success_url(self):
        return reverse('invoice_detail', kwargs={'pk': self.object.pk})

class InvoiceDetailView(DetailView):
    model = Invoice
    template_name = 'portal/invoice_detail.html'

class InvoiceListView(ListView):
    model = Invoice
    template_name = 'portal/invoice_list.html'
    paginate_by = 10

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
def product_search_fallback(request):
    return render(request, 'portal/products/search_empty.html')

# BarcodeScanner
def barcode_scanner_view(request):
    """Render the barcode scanner interface page"""
    return render(request, 'portal/barcode_scanner.html')