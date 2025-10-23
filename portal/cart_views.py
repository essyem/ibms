# portal/cart_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.views.generic import TemplateView
from django.conf import settings
from .models import Product, Cart, CartItem, Order
from django.contrib.auth.models import User
import json
from decimal import Decimal


def get_or_create_cart(request):
    """Get or create cart for user (authenticated or anonymous)"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session
        if not request.session.session_key:
            request.session.create()
        
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    return cart


@require_POST
def add_to_cart(request):
    """Add product to cart via AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check stock availability
        if product.stock < quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {product.stock} units available in stock'
            })
        
        cart = get_or_create_cart(request)
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if product.stock < new_quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot add {quantity} more. Only {product.stock - cart_item.quantity} units available'
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        cart_total_items = sum(item.quantity for item in cart.cartitem_set.all())
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_total_items': cart_total_items,
            'item_quantity': cart_item.quantity
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_POST 
def update_cart_item(request):
    """Update cart item quantity"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        
        if quantity <= 0:
            cart_item.delete()
            action = 'removed'
        else:
            # Check stock availability
            if cart_item.product.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.product.stock} units available in stock'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            action = 'updated'
        
        cart_total_items = sum(item.quantity for item in cart.cartitem_set.all())
        cart_total_amount = sum(item.quantity * item.product.unit_price for item in cart.cartitem_set.all())
        
        return JsonResponse({
            'success': True,
            'message': f'Cart item {action}',
            'cart_total_items': cart_total_items,
            'cart_total_amount': float(cart_total_amount),
            'item_total_price': float(cart_item.quantity * cart_item.product.unit_price) if quantity > 0 else 0
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_POST
def remove_from_cart(request):
    """Remove item from cart"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        cart_total_items = sum(item.quantity for item in cart.cartitem_set.all())
        cart_total_amount = sum(item.quantity * item.product.unit_price for item in cart.cartitem_set.all())
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart_total_items': cart_total_items,
            'cart_total_amount': float(cart_total_amount)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def cart_count(request):
    """Get cart item count for display in navbar"""
    try:
        cart = get_or_create_cart(request)
        total_items = sum(item.quantity for item in cart.cartitem_set.all())
        
        return JsonResponse({
            'success': True,
            'cart_total_items': total_items
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'cart_total_items': 0
        })


class CartView(TemplateView):
    """Display shopping cart contents"""
    template_name = 'portal/cart/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            cart = get_or_create_cart(self.request)
            cart_items = cart.cartitem_set.select_related('product', 'product__category').all()
            
            total_amount = sum(item.quantity * item.product.unit_price for item in cart_items)
            total_items = sum(item.quantity for item in cart_items)
            
            context.update({
                'cart': cart,
                'cart_items': cart_items,
                'total_amount': total_amount,
                'total_items': total_items,
                'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97430514865'),
            })
        except Exception as e:
            context.update({
                'cart': None,
                'cart_items': [],
                'total_amount': 0,
                'total_items': 0,
                'error': str(e)
            })
        
        return context

    def render_to_response(self, context, **response_kwargs):
        """Render Arabic template if requested via query param or language code."""
        request = self.request
        # Preference: explicit query parameter ?lang=ar
        lang = request.GET.get('lang') or getattr(request, 'LANGUAGE_CODE', '')
        if lang and str(lang).lower().startswith('ar'):
            self.template_name = 'portal/cart/cart_ar.html'
        else:
            self.template_name = 'portal/cart/cart.html'

        return super().render_to_response(context, **response_kwargs)


class CheckoutView(TemplateView):
    """Checkout view for placing orders"""
    template_name = 'portal/cart/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        cart = get_or_create_cart(self.request)
        cart_items = cart.cartitem_set.select_related('product').all()
        
        total_amount = sum(item.quantity * item.product.unit_price for item in cart_items)
        
        context.update({
            'cart': cart,
            'cart_items': cart_items,
            'total_amount': total_amount,
            'cart_is_empty': not cart_items,
        })
        return context
    
    def get(self, request, *args, **kwargs):
        """Handle GET request - redirect to cart if empty"""
        cart = get_or_create_cart(request)
        cart_items = cart.cartitem_set.all()
        
        if not cart_items:
            messages.info(request, 'Your cart is empty. Add some items before checkout.')
            return redirect('portal:cart')
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request):
        """Process checkout form"""
        try:
            cart = get_or_create_cart(request)
            cart_items = cart.cartitem_set.all()
            
            if not cart_items:
                messages.error(request, 'Your cart is empty.')
                return redirect('portal:cart')
            
            # Get form data
            customer_name = request.POST.get('customer_name', '').strip()
            customer_email = request.POST.get('customer_email', '').strip()
            customer_phone = request.POST.get('customer_phone', '').strip()
            
            # Payment information
            payment_method = request.POST.get('payment_method', 'cod')
            transfer_receipt = request.FILES.get('transfer_receipt')
            
            # Detailed delivery address
            delivery_zone = request.POST.get('delivery_zone', '').strip()
            delivery_street = request.POST.get('delivery_street', '').strip()
            delivery_building = request.POST.get('delivery_building', '').strip()
            delivery_flat = request.POST.get('delivery_flat', '').strip()
            delivery_additional_info = request.POST.get('delivery_additional_info', '').strip()
            
            # Basic validation
            required_fields = [customer_name, customer_email, customer_phone, delivery_zone, delivery_street, delivery_building]
            if not all(required_fields):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, self.template_name, self.get_context_data())
            
            # Validate payment method specific requirements
            if payment_method == 'bank_transfer' and not transfer_receipt:
                messages.error(request, 'Please upload your bank transfer receipt.')
                return render(request, self.template_name, self.get_context_data())
            
            # Email validation
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, customer_email):
                messages.error(request, 'Please enter a valid email address.')
                return render(request, self.template_name, self.get_context_data())
            
            # Calculate total
            total_amount = sum(item.quantity * item.product.unit_price for item in cart_items)
            
            # Generate order number
            import uuid
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            # Create order with enhanced fields
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                order_number=order_number,
                total_price=total_amount,
                
                # Customer information
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                
                # Payment information
                payment_method=payment_method,
                transfer_receipt=transfer_receipt,
                
                # Detailed delivery address
                delivery_zone=delivery_zone,
                delivery_street=delivery_street,
                delivery_building=delivery_building,
                delivery_flat=delivery_flat,
                delivery_additional_info=delivery_additional_info,
                
                # Legacy fields for backward compatibility
                delivery_address=f"{delivery_zone}, {delivery_street}, {delivery_building}" + (f", {delivery_flat}" if delivery_flat else ""),
                preferred_contact=customer_phone,
            )
            
            # Copy cart items to order
            for cart_item in cart_items:
                order.items.add(cart_item)
            
            # Clear the cart
            cart_items.delete()
            
            # Success message with payment method info
            if payment_method == 'bank_transfer':
                messages.success(request, f'Order {order_number} placed successfully! We will verify your bank transfer and contact you soon.')
            else:
                messages.success(request, f'Order {order_number} placed successfully! We will contact you to confirm delivery details.')
            
            return redirect('portal:order_confirmation', order_number=order_number)
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return render(request, self.template_name, self.get_context_data())
            
            # Clear the cart
            cart_items.delete()
            
            messages.success(request, f'Order {order_number} placed successfully! We will contact you soon.')
            return redirect('portal:order_confirmation', order_number=order_number)
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return render(request, self.template_name, self.get_context_data())


def order_confirmation(request, order_number):
    """Order confirmation page"""
    order = get_object_or_404(Order, order_number=order_number)
    
    context = {
        'order': order,
        'whatsapp_number': getattr(settings, 'WHATSAPP_BUSINESS_NUMBER', '+97430514865'),
        'whatsapp_message': f"Hi! I just placed order {order_number} and would like to confirm the details."
    }
    
    return render(request, 'portal/cart/order_confirmation.html', context)