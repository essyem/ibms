# portal/resources.py
from import_export import resources
from .models import Product

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('id', 'name', 'category__name', 'price', 'stock')
        export_order = fields