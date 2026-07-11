import os
import sys
import io
import django

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradehub.settings')
django.setup()

from products.models import Category

updates = {
    'Electronics': '\U0001f4bb',
    'Textiles & Apparel': '\U0001f457',
    'Food & Agriculture': '\U0001f33e',
    'Building Materials': '\U0001f3d7\ufe0f',
    'Chemicals & Plastics': '\U0001f9ea',
    'Machinery & Equipment': '\u2699\ufe0f',
    'Furniture & Decor': '\U0001fa91',
    'Health & Beauty': '\U0001f484',
    'Automotive Parts': '\U0001f697',
    'Other': '\U0001f4e6',
}

for name, icon in updates.items():
    updated = Category.objects.filter(name=name).update(icon=icon)
    sys.stdout.write('Updated icon for: ' + name + '\n')

sys.stdout.write('Done!\n')
