import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradehub.settings')
django.setup()

from products.models import Category

defaults = [
    ('Electronics', '[PC]'),
    ('Textiles & Apparel', '[CLOTH]'),
    ('Food & Agriculture', '[FOOD]'),
    ('Building Materials', '[BUILD]'),
    ('Chemicals & Plastics', '[CHEM]'),
    ('Machinery & Equipment', '[MACH]'),
    ('Furniture & Decor', '[FURN]'),
    ('Health & Beauty', '[HLTH]'),
    ('Automotive Parts', '[AUTO]'),
    ('Other', '[PKG]'),
]

for name, icon in defaults:
    obj, created = Category.objects.get_or_create(name=name, defaults={'icon': icon})
    if not created:
        obj.icon = icon
        obj.save()
    status_str = 'Created' if created else 'Updated'
    sys.stdout.write(status_str + ': ' + icon + ' ' + name + '\n')

sys.stdout.write('Done!\n')
