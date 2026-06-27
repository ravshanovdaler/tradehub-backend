import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradehub.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from accounts.models import SellerProfile, BuyerProfile
from products.models import Product, ProductImage, ProductVariant, ProductReview, ProductView
from orders.models import Order, OrderItem, OrderLocation

User = get_user_model()

def seed():
    print("Deleting old seed data...")
    User.objects.filter(username__in=['seller1', 'buyer1']).delete()

    print("Creating seller1 and buyer1...")
    # Create seller (Uzbek manufacturer)
    seller = User.objects.create_user(
        username='seller1',
        email='seller1@uzb2b.uz',
        password='password123',
        first_name='Jasur',
        last_name='Tursunov',
        phone_number='+998901234567',
        age=35,
        is_seller=True,
        is_buyer=False,
        email_verified=True  # Pre-verified for demo
    )
    profile = SellerProfile.objects.create(
        user=seller,
        company_name="Toshkent Tekstil Zavodi",
        business_address="Yunusobod tumani, Toshkent sh., O'zbekiston",
        address_latitude=41.3111,
        address_longitude=69.3083,
        registration_number="UZ-998877A",
        is_verified=True,
        verification_notes="Approved by system administrator"
    )

    # Create buyer (Uzbek retailer)
    buyer = User.objects.create_user(
        username='buyer1',
        email='buyer1@retail.uz',
        password='password123',
        first_name='Dilnoza',
        last_name='Karimova',
        phone_number='+998909876543',
        age=28,
        is_seller=False,
        is_buyer=True,
        email_verified=True  # Pre-verified for demo
    )
    BuyerProfile.objects.create(
        user=buyer,
        delivery_address="Chilonzor tumani, Toshkent sh., O'zbekiston",
        delivery_latitude=41.2856,
        delivery_longitude=69.2023,
    )

    print("Creating products...")
    p1 = Product.objects.create(
        seller=seller,
        name="O'zbek Paxta Matosi (Premium Grade)",
        description="Yuqori sifatli 100% o'zbek paxtasidan tayyorlangan mato. Sertifikat: ISO 9001. MOQ ulgurji narxda. Rangi: oq, ko'k, qizil va boshqalar.",
        price=1.85,
        moq=500,
        views_count=824
    )
    p2 = Product.objects.create(
        seller=seller,
        name="Ipak Gazlama To'plami (Samarqand)",
        description="Samarqand ustaları tomonidan to'qilgan natural ipak gazlama. Raqobatbardosh ulgurji narxlar. Minimal buyurtma: 100 metr. Milliy naqshlar mavjud.",
        price=12.50,
        moq=100,
        views_count=512
    )
    p3 = Product.objects.create(
        seller=seller,
        name="Qurilish G'ishti (M-150 Markali)",
        description="Yuqori sifatli M-150 markali qurilish g'ishti. Siqilish mustahkamligi: 150 kg/sm2. Saqlash muddati: cheksiz. Toshkentdagi ombordan olib ketish yoki yetkazib berish.",
        price=0.35,
        moq=1000,
        views_count=340
    )

    print("Creating product variants...")
    # Cotton fabric variants
    ProductVariant.objects.create(product=p1, attribute_name="Color", attribute_value="Oq (White)", additional_price=0.00)
    ProductVariant.objects.create(product=p1, attribute_name="Color", attribute_value="Ko'k (Blue)", additional_price=0.05)
    ProductVariant.objects.create(product=p1, attribute_name="Color", attribute_value="Qizil (Red)", additional_price=0.05)
    ProductVariant.objects.create(product=p1, attribute_name="Width", attribute_value="120 sm", additional_price=0.00)
    ProductVariant.objects.create(product=p1, attribute_name="Width", attribute_value="150 sm", additional_price=0.20)

    # Silk fabric variants
    ProductVariant.objects.create(product=p2, attribute_name="Pattern", attribute_value="Adras (Milliy)", additional_price=0.00)
    ProductVariant.objects.create(product=p2, attribute_name="Pattern", attribute_value="Satin (Tekis)", additional_price=1.50)
    ProductVariant.objects.create(product=p2, attribute_name="Pattern", attribute_value="Baxmal (Velvet)", additional_price=2.00)

    # Brick variants
    ProductVariant.objects.create(product=p3, attribute_name="Size", attribute_value="Standart (250x120x65)", additional_price=0.00)
    ProductVariant.objects.create(product=p3, attribute_name="Size", attribute_value="Katta (250x120x88)", additional_price=0.05)
    ProductVariant.objects.create(product=p3, attribute_name="Color", attribute_value="Qizil (Red)", additional_price=0.00)
    ProductVariant.objects.create(product=p3, attribute_name="Color", attribute_value="Sariq (Yellow)", additional_price=0.00)

    print("Creating reviews...")
    ProductReview.objects.create(product=p1, user=buyer, rating=5, comment="Mato sifati a'lo darajada! 1000 metr buyurtma berdik, hech qanday nuqson yo'q. Tavsiya qilamiz!")
    ProductReview.objects.create(product=p2, user=buyer, rating=4, comment="Ipak gazlama juda chiroyli. Narxi boshqa yetkazib beruvchilarga nisbatan arzonroq. Keyingisida yana buyurtma beramiz.")
    ProductReview.objects.create(product=p3, user=buyer, rating=5, comment="G'isht sifati standartga mos. O'z vaqtida yetkazib berishdi. Qurilish jarayonida hech qanday muammo bo'lmadi.")

    print("Creating mock product views...")
    now = timezone.now()
    for _ in range(300):
        days_ago = random.randint(1, 150)
        timestamp = now - timedelta(days=days_ago)
        p = random.choice([p1, p2, p3])
        pv = ProductView.objects.create(product=p, user=random.choice([buyer, None]))
        ProductView.objects.filter(pk=pv.pk).update(timestamp=timestamp)

    print("Creating mock orders...")
    # Completed Order
    o1 = Order.objects.create(buyer=buyer, seller=seller, total_price=1850.00, status='DELIVERED')
    Order.objects.filter(pk=o1.pk).update(created_at=now - timedelta(days=25))
    OrderItem.objects.create(order=o1, product=p1, quantity=500, price=1.85)
    OrderItem.objects.create(order=o1, product=p2, quantity=50, price=12.50)
    # Uzbekistan route locations
    loc1a = OrderLocation.objects.create(order=o1, latitude=41.3111, longitude=69.3083, description="Toshkent Tekstil Zavodidan jo'natildi")
    loc1b = OrderLocation.objects.create(order=o1, latitude=41.2995, longitude=69.2401, description="Toshkent Logistika Markazida saralandi")
    loc1c = OrderLocation.objects.create(order=o1, latitude=41.2856, longitude=69.2023, description="Xaridor omboriga yetkazildi - Chilonzor")
    OrderLocation.objects.filter(pk=loc1a.pk).update(timestamp=now - timedelta(days=24))
    OrderLocation.objects.filter(pk=loc1b.pk).update(timestamp=now - timedelta(days=23))
    OrderLocation.objects.filter(pk=loc1c.pk).update(timestamp=now - timedelta(days=22))

    # Shipping Order
    o2 = Order.objects.create(buyer=buyer, seller=seller, total_price=350.00, status='SHIPPED')
    Order.objects.filter(pk=o2.pk).update(created_at=now - timedelta(days=3))
    OrderItem.objects.create(order=o2, product=p3, quantity=1000, price=0.35)
    loc2a = OrderLocation.objects.create(order=o2, latitude=41.3111, longitude=69.3083, description="G'ishtlar yuklab jo'natildi - Toshkent Tekstil Zavodi")
    loc2b = OrderLocation.objects.create(order=o2, latitude=41.2995, longitude=69.2401, description="Yo'lda - Toshkent Logistika Markazi")
    OrderLocation.objects.filter(pk=loc2a.pk).update(timestamp=now - timedelta(days=2))
    OrderLocation.objects.filter(pk=loc2b.pk).update(timestamp=now - timedelta(days=1))

    # Pending Order
    o3 = Order.objects.create(buyer=buyer, seller=seller, total_price=925.00, status='PENDING')
    Order.objects.filter(pk=o3.pk).update(created_at=now - timedelta(hours=5))
    OrderItem.objects.create(order=o3, product=p1, quantity=500, price=1.85)
    OrderLocation.objects.create(order=o3, latitude=41.3111, longitude=69.3083, description="Buyurtma qabul qilindi. To'lov tasdiqlanishi kutilmoqda.")

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
