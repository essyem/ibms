#!/usr/bin/env python3
"""
Small helper to fill common English msgid translations in locale/ar/LC_MESSAGES/django.po
This is a convenience when gettext tooling is not available or you want to auto-fill
translations for the UI strings we added.

WARNING: This script does a best-effort replace for a subset of strings.
"""
import polib
from pathlib import Path

po_path = Path('locale/ar/LC_MESSAGES/django.po')
if not po_path.exists():
    print('django.po not found at', po_path)
    raise SystemExit(1)

po = polib.pofile(str(po_path))

# Mapping of English msgid -> Arabic translation (you can improve these later)
translations = {
    'Home': 'الرئيسية',
    'Product Catalog': 'كتالوج المنتجات',
    'Dashboard': 'لوحة التحكم',
    'All Products': 'جميع المنتجات',
    'Product Dashboard': 'لوحة منتجات',
    'Add Product': 'إضافة منتج',
    'Finance': 'المالية',
    'Finance Dashboard': 'لوحة مالية',
    'Daily Revenue': 'الإيرادات اليومية',
    'Procurement': 'المشتريات',
    'Purchase Orders': 'أوامر الشراء',
    'Suppliers': 'الموردون',
    'New Purchase Order': 'طلب شراء جديد',
    'Messages': 'الرسائل',
    'Static Files': 'الملفات الثابتة',
    'Syndication': 'النشرات',
    'Shopping Cart': 'سلة التسوق',
    'Review your selected items and proceed to checkout': 'راجع العناصر المختارة واستكمل عملية الدفع',
    'Item': 'عنصر',
    'In Stock': 'متوفر',
    'available': 'متاح',
    'each': 'لكل وحدة',
    'Remove': 'إزالة',
    'Continue Shopping': 'متابعة التسوق',
    'Order Summary': 'ملخص الطلب',
    'Items': 'العناصر',
    'Delivery': 'التوصيل',
    'Total': 'الإجمالي',
    'Proceed to Checkout': 'المتابعة للدفع',
    'Order via WhatsApp': 'اطلب عبر واتساب',
    'Your cart is empty': 'سلة التسوق فارغة',
    "Looks like you haven't added any items to your cart yet.": 'يبدو أنك لم تضف أي عناصر إلى سلة التسوق بعد.',
    'Start Shopping': 'ابدأ التسوق',
    'Success!': 'تم بنجاح!',
    'added to cart successfully!': 'تمت إضافته إلى السلة بنجاح!',
    'Cart updated successfully!': 'تم تحديث السلة بنجاح!',
    'Are you sure you want to remove this item?': 'هل أنت متأكد أنك تريد إزالة هذا العنصر؟',
    'Yes': 'نعم',
    'No': 'لا',
    'Continue Shopping': 'متابعة التسوق',
    'View Cart': 'عرض السلة'
}

count = 0
for entry in po:
    if entry.msgid in translations and (not entry.msgstr or entry.msgstr.strip() == ''):
        entry.msgstr = translations[entry.msgid]
        count += 1

po.save()
print(f'Updated {count} entries in {po_path}')

# Also write compiled .mo using polib
mo_path = po_path.with_suffix('.mo')
po.save_as_mofile(str(mo_path))
print('Wrote', mo_path)
