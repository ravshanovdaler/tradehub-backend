from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from crm.models import CRMCalculation

User = get_user_model()

class CRMCalculationsTestCase(APITestCase):
    def setUp(self):
        # Create seller user
        self.seller = User.objects.create_user(
            username='seller1',
            email='seller1@test.com',
            password='password123',
            is_seller=True
        )
        # Login
        self.client.login(username='seller1', password='password123')
        
    def test_auto_seed_calculations_on_get(self):
        # Initial check: no calculations in DB
        self.assertEqual(CRMCalculation.objects.filter(user=self.seller).count(), 0)
        
        # Call GET on calculations list
        url = reverse('crm_calculations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify 3 items are auto-seeded
        self.assertEqual(CRMCalculation.objects.filter(user=self.seller).count(), 3)
        data = response.data
        self.assertEqual(len(data), 3)
        
        # Verify default names are present
        names = [item['name'] for item in data]
        self.assertIn('Logistics Costs', names)
        self.assertIn('Taxes', names)
        self.assertIn('Manufacturing Cost', names)

    def test_create_calculation_percentage(self):
        url = reverse('crm_calculations')
        payload = {
            'name': 'Marketing Cost',
            'value_type': 'PERCENTAGE',
            'value': 12.50
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Marketing Cost')
        self.assertEqual(response.data['value_type'], 'PERCENTAGE')
        self.assertEqual(response.data['value'], 12.5)

    def test_create_calculation_usd(self):
        url = reverse('crm_calculations')
        payload = {
            'name': 'Office Rent',
            'value_type': 'USD',
            'value': 750.00
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Office Rent')
        self.assertEqual(response.data['value_type'], 'USD')
        self.assertEqual(response.data['value'], 750.0)

    def test_update_calculation(self):
        # First seed or create an item
        calc = CRMCalculation.objects.create(
            user=self.seller,
            name='Temporary Cost',
            value_type='PERCENTAGE',
            value=10.00
        )
        
        # Update using PUT
        url = reverse('crm_calculation_detail', kwargs={'pk': calc.id})
        payload = {
            'name': 'Updated Cost Name',
            'value_type': 'USD',
            'value': 250.00
        }
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Reload from database and verify
        calc.refresh_from_db()
        self.assertEqual(calc.name, 'Updated Cost Name')
        self.assertEqual(calc.value_type, 'USD')
        self.assertEqual(float(calc.value), 250.00)

    def test_delete_calculation(self):
        calc = CRMCalculation.objects.create(
            user=self.seller,
            name='Delete Me',
            value_type='PERCENTAGE',
            value=10.00
        )
        
        url = reverse('crm_calculation_detail', kwargs={'pk': calc.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CRMCalculation.objects.filter(id=calc.id).exists())

    def test_crm_stats_calculations_breakdown(self):
        # Place a mock sale order
        from orders.models import Order
        Order.objects.create(
            seller=self.seller,
            buyer=self.seller, # dummy buyer
            total_price=1000.00,
            status='COMPLETED'
        )
        
        # Create calculations: 5% Tax (Percentage) and 150 USD Logistics (Flat)
        CRMCalculation.objects.create(
            user=self.seller,
            name='Tax Rate',
            value_type='PERCENTAGE',
            value=5.00
        )
        CRMCalculation.objects.create(
            user=self.seller,
            name='Flat Logistics',
            value_type='USD',
            value=150.00
        )
        
        url = reverse('seller_crm_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        finance = response.data['finance']
        self.assertEqual(finance['revenue'], 1000.00)
        
        # Verify individual calculations
        calcs = finance['calculations']
        self.assertEqual(len(calcs), 2)
        
        tax_calc = next(item for item in calcs if item['name'] == 'Tax Rate')
        logistics_calc = next(item for item in calcs if item['name'] == 'Flat Logistics')
        
        # 5% of 1000 = 50
        self.assertEqual(tax_calc['cost'], 50.00)
        # Flat USD = 150
        self.assertEqual(logistics_calc['cost'], 150.00)
        
        # Profit = 1000 - 50 - 150 = 800
        self.assertEqual(finance['profit'], 800.00)

    def test_crm_stats_dynamic_product_mfg_and_order_transport(self):
        # Create mock products
        from products.models import Product
        from orders.models import Order, OrderItem
        
        prod_with_mfg = Product.objects.create(
            seller=self.seller,
            name='Custom widget A',
            price=10.00,
            manufacturing_cost=4.00,
            moq=1
        )
        prod_without_mfg = Product.objects.create(
            seller=self.seller,
            name='Custom widget B',
            price=20.00,
            manufacturing_cost=0.00, # fallback to percentage
            moq=1
        )
        
        # Create completed order with transport cost
        order = Order.objects.create(
            seller=self.seller,
            buyer=self.seller,
            total_price=100.00,
            transport_cost=15.00,
            status='COMPLETED'
        )
        
        # Order items
        OrderItem.objects.create(order=order, product=prod_with_mfg, quantity=2, price=10.00)  # mfg cost: 2 * 4.00 = 8.00
        OrderItem.objects.create(order=order, product=prod_without_mfg, quantity=4, price=20.00) # mfg cost fallback: 4 * 20.00 * 55% = 44.00
        
        # Create global calculations list
        CRMCalculation.objects.create(
            user=self.seller,
            name='Manufacturing Cost',
            value_type='PERCENTAGE',
            value=55.00
        )
        CRMCalculation.objects.create(
            user=self.seller,
            name='Logistics Costs',
            value_type='PERCENTAGE',
            value=8.00
        )
        
        url = reverse('seller_crm_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        finance = response.data['finance']
        calcs = finance['calculations']
        
        mfg_calc = next(item for item in calcs if item['name'] == 'Manufacturing Cost')
        logistics_calc = next(item for item in calcs if item['name'] == 'Logistics Costs')
        
        # Mfg Cost: 8.00 (widget A) + 44.00 (widget B fallback) = 52.00
        self.assertEqual(mfg_calc['cost'], 52.00)
        
        # Logistics: flat order transport_cost = 15.00
        self.assertEqual(logistics_calc['cost'], 15.00)
        
        # Profit: 100 - 52 (Mfg) - 15 (Logistics) = 33
        self.assertEqual(finance['profit'], 33.00)

    def test_cannot_create_default_calculations(self):
        url = reverse('crm_calculations')
        for name in ['Manufacturing Cost', 'Logistics Costs', 'Logistics Cost', 'Transport Cost', 'Transport costs']:
            payload = {
                'name': name,
                'value_type': 'PERCENTAGE',
                'value': 10.00
            }
            response = self.client.post(url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("cannot be overridden or created", response.data['error'])

    def test_cannot_update_default_calculations(self):
        calc = CRMCalculation.objects.create(
            user=self.seller,
            name='Manufacturing Cost',
            value_type='PERCENTAGE',
            value=55.00
        )
        url = reverse('crm_calculation_detail', kwargs={'pk': calc.id})
        payload = {
            'name': 'Changed Name',
            'value_type': 'PERCENTAGE',
            'value': 60.00
        }
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot be updated globally", response.data['error'])

    def test_cannot_delete_default_calculations(self):
        calc = CRMCalculation.objects.create(
            user=self.seller,
            name='Logistics Costs',
            value_type='PERCENTAGE',
            value=8.00
        )
        url = reverse('crm_calculation_detail', kwargs={'pk': calc.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot be deleted", response.data['error'])

