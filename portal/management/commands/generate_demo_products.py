from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.text import slugify
import os
import random

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from faker import Faker
import textwrap

# optional helpers for better Arabic rendering (if installed)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SHAPER_AVAILABLE = True
except Exception:
    ARABIC_SHAPER_AVAILABLE = False

from portal.models import Category, Product


class Command(BaseCommand):
    help = 'Generate demo products with optional Arabic names and images'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=12, help='Number of products to create')
        parser.add_argument('--site-categories', type=str, default='', help='Comma separated category names to use')
        parser.add_argument('--no-images', action='store_true', help='Do not generate or attach images (faster)')
        parser.add_argument('--start-index', type=int, default=1, help='Start index for SKU numbering (default 1)')

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        cat_names = [n.strip() for n in options['site_categories'].split(',') if n.strip()] if options['site_categories'] else []

        # Ensure media dir exists
        media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        products_dir = os.path.join(media_root, 'products')
        os.makedirs(products_dir, exist_ok=True)

        # Prepare categories
        default_cats = ['IT Hardware', 'Optics', 'Peripherals', 'Networking', 'Electronics']
        final_cats = cat_names or default_cats
        categories = []
        for name in final_cats:
            # Avoid MultipleObjectsReturned by reusing the first matching category if duplicates exist
            c = Category.objects.filter(name=name).first()
            if not c:
                c = Category.objects.create(name=name)
            categories.append(c)

        created = []
        start_index = options.get('start_index', 1) or 1
        for i in range(start_index, start_index + count):
            cat = random.choice(categories)
            en_name = fake.unique.sentence(nb_words=3).rstrip('.')
            # simple Arabic fallback using Faker with 'ar_PS' or transliteration
            try:
                ar_fake = Faker('ar_PS')
                ar_name = ar_fake.unique.word()
            except Exception:
                # naive transliteration: reverse words and append Arabic-looking suffix
                ar_name = en_name.split()[0] + ' ' + 'منتج'

            base_sku = f'DEMO{i:04d}'
            sku = base_sku
            # ensure SKU uniqueness (append suffix if needed)
            suffix = 1
            while Product.objects.filter(sku=sku).exists():
                sku = f"{base_sku}-{suffix:03d}"
                suffix += 1
            description = fake.paragraph(nb_sentences=2)
            description_ar = f"وصف {ar_name} - {fake.word()}"
            price = round(random.uniform(10, 800), 2)
            cost = round(price * random.uniform(0.5, 0.9), 2)
            stock = random.randint(0, 50)

            # create product
            defaults = dict(
                category=cat,
                name=en_name,
                name_ar=ar_name,
                description=description,
                description_ar=description_ar,
                cost_price=cost,
                unit_price=price,
                stock=stock,
                warranty_period=random.choice([0,6,12,24]),
                barcode=f"{random.randint(1000000000,9999999999)}",
                is_active=True
            )
            p, created_flag = Product.objects.get_or_create(sku=sku, defaults=defaults)

            no_images = options.get('no_images', False)
            if not no_images:
                # create or generate image
                img_name = f"{slugify(sku)}.png"
                img_path = os.path.join(products_dir, img_name)

                if PIL_AVAILABLE:
                    # generate a simple image with product name; prefer a local Arabic TTF if present
                    img = Image.new('RGB', (800, 800), color=(240, 240, 240))
                    draw = ImageDraw.Draw(img)

                    # look for fonts in a project-level fonts/ folder first
                    font_dir = os.path.join(getattr(settings, 'BASE_DIR', '.'), 'fonts')
                    arabic_font_path = os.path.join(font_dir, 'NotoNaskhArabic-Regular.ttf')
                    dejavu_in_project = os.path.join(font_dir, 'DejaVuSans.ttf')

                    # choose font: Arabic font if available, otherwise DejaVu then default
                    try:
                        if os.path.exists(arabic_font_path):
                            font_en = ImageFont.truetype(arabic_font_path, 44)
                            font_ar = ImageFont.truetype(arabic_font_path, 48)
                        elif os.path.exists(dejavu_in_project):
                            font_en = ImageFont.truetype(dejavu_in_project, 44)
                            font_ar = ImageFont.truetype(dejavu_in_project, 48)
                        else:
                            # try system DejaVu
                            font_en = ImageFont.truetype('DejaVuSans.ttf', 44)
                            font_ar = ImageFont.truetype('DejaVuSans.ttf', 48)
                    except Exception:
                        font_en = ImageFont.load_default()
                        font_ar = ImageFont.load_default()

                    # Prepare texts, reshape Arabic if possible
                    en_text = en_name
                    ar_text = ar_name
                    if ARABIC_SHAPER_AVAILABLE:
                        try:
                            ar_text = arabic_reshaper.reshape(ar_text)
                            ar_text = get_display(ar_text)
                        except Exception:
                            pass

                    # Draw header background
                    draw.rectangle([(0,0),(800,250)], fill=(51,102,153))

                    # wrap and draw English title centered
                    wrapped_en = textwrap.fill(en_text, width=18)
                    # measure block size
                    try:
                        w, h = font_en.getsize(wrapped_en)
                    except Exception:
                        bbox = font_en.getbbox(wrapped_en) if hasattr(font_en, 'getbbox') else (0,0,0,0)
                        w = bbox[2] - bbox[0]
                        h = bbox[3] - bbox[1]
                    draw.multiline_text(((800-w)/2, 40), wrapped_en, fill='white', font=font_en, align='center')

                    # draw Arabic name below if present (right-aligned)
                    if ar_text:
                        wrapped_ar = textwrap.fill(ar_text, width=18)
                        try:
                            w_ar, h_ar = font_ar.getsize(wrapped_ar)
                        except Exception:
                            bbox = font_ar.getbbox(wrapped_ar) if hasattr(font_ar, 'getbbox') else (0,0,0,0)
                            w_ar = bbox[2] - bbox[0]
                            h_ar = bbox[3] - bbox[1]
                        # right align Arabic text near right edge
                        draw.multiline_text((780 - w_ar, 160), wrapped_ar, fill='white', font=font_ar, align='right')

                    # draw SKU and meta
                    meta_font = font_en
                    draw.text((20, 320), f"SKU: {sku}", fill=(40,40,40), font=meta_font)
                    draw.text((20, 360), f"Price: {price}", fill=(40,40,40), font=meta_font)
                    img.save(img_path)
                else:
                    # fallback: copy logo if exists
                    possible = [os.path.join(media_root, 'logo.png'), os.path.join(media_root, 'logo-admin.png')]
                    copied = False
                    for src in possible:
                        if os.path.exists(src):
                            from shutil import copyfile
                            copyfile(src, img_path)
                            copied = True
                            break
                    if not copied:
                        # write a small placeholder
                        with open(img_path, 'wb') as fh:
                            fh.write(b'')

                # attach to product.image field
                with open(img_path, 'rb') as fh:
                    p.image.save(img_name, ContentFile(fh.read()), save=True)

            created.append(p)
            self.stdout.write(self.style.SUCCESS(f"Created demo product {p.sku} ({p.pk}) - {p.name} / {p.name_ar}"))

        self.stdout.write(self.style.SUCCESS(f"Generated {len(created)} demo products."))
