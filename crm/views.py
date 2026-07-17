from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from orders.models import Order, OrderItem
from products.models import Product, ProductView
from .models import CRMCalculation
from accounts.utils import convert_currency

class SellerCRMStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response({'error': 'Only sellers have access to the CRM dashboard.'}, status=status.HTTP_403_FORBIDDEN)

        seller_currency = getattr(user, 'currency', 'UZS')

        # 1. Product views aggregate
        products = Product.objects.filter(seller=user)
        total_views = products.aggregate(total=Sum('views_count'))['total'] or 0

        # 2. Sales / Order metrics (excluding PENDING and CANCELLED)
        orders = Order.objects.filter(seller=user).exclude(status__in=['PENDING', 'CANCELLED'])
        total_orders = orders.count()

        total_sales = 0.0
        for order in orders:
            total_sales += convert_currency(float(order.total_price), order.currency, seller_currency)

        avg_order_value = round(total_sales / total_orders, 2) if total_orders > 0 else 0.0
        conversion_rate = round((total_orders / total_views) * 100, 2) if total_views > 0 else 0.0

        # Status distribution
        status_dist = list(
            Order.objects.filter(seller=user)
            .values('status')
            .annotate(count=Count('id'))
        )

        # Top Viewed Products (converted to seller currency)
        top_viewed = []
        for p in products.order_by('-views_count')[:5]:
            top_viewed.append({
                'id': p.id,
                'name': p.name,
                'views_count': p.views_count,
                'price': convert_currency(float(p.price), p.currency, seller_currency)
            })

        # Top Sold Products (aggregate OrderItem, convert to seller currency)
        items = OrderItem.objects.filter(order__seller=user).exclude(order__status__in=['PENDING', 'CANCELLED'])
        sold_map = {}
        for item in items:
            prod_id = item.product.id if item.product else None
            prod_name = item.product.name if item.product else 'Deleted Product'
            if not prod_id:
                continue
            revenue_converted = convert_currency(float(item.price * item.quantity), item.order.currency, seller_currency)
            if prod_id not in sold_map:
                sold_map[prod_id] = {
                    'product__id': prod_id,
                    'product__name': prod_name,
                    'units_sold': 0,
                    'sales_revenue': 0.0
                }
            sold_map[prod_id]['units_sold'] += item.quantity
            sold_map[prod_id]['sales_revenue'] += revenue_converted
        top_sold = sorted(sold_map.values(), key=lambda x: x['units_sold'], reverse=True)[:5]

        # Monthly Sales Trend (last 6 months, converted to seller currency)
        monthly_map = {}
        for order in orders:
            month = order.created_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            revenue_converted = convert_currency(float(order.total_price), order.currency, seller_currency)
            if month not in monthly_map:
                monthly_map[month] = {'month': month, 'revenue': 0.0, 'order_count': 0}
            monthly_map[month]['revenue'] += revenue_converted
            monthly_map[month]['order_count'] += 1
        monthly_sales = sorted(monthly_map.values(), key=lambda x: x['month'])
        
        # Format monthly sales for chart
        sales_trend_labels = []
        sales_trend_data = []
        for entry in monthly_sales:
            month_str = entry['month'].strftime('%b %Y')
            sales_trend_labels.append(month_str)
            sales_trend_data.append(entry['revenue'])

        # If data is empty, insert default labels
        if not sales_trend_labels:
            sales_trend_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
            sales_trend_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Monthly Product Views Trend
        views_trend = list(
            ProductView.objects.filter(product__seller=user)
            .annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        views_trend_labels = []
        views_trend_data = []
        for entry in views_trend:
            if entry['month']:
                month_str = entry['month'].strftime('%b %Y')
                views_trend_labels.append(month_str)
                views_trend_data.append(entry['count'])
        if not views_trend_data:
            views_trend_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
            views_trend_data = [0, 0, 0, 0, 0, 0]

        # Financial Breakdown
        calcs = CRMCalculation.objects.filter(user=user)
        order_items = OrderItem.objects.filter(order__in=orders)

        actual_mfg_cost = 0.0
        for item in order_items:
            mfg_converted = convert_currency(float(item.manufacturing_cost or 0), item.order.currency, seller_currency)
            actual_mfg_cost += mfg_converted * item.quantity

        actual_logistics_cost = 0.0
        for o in orders:
            log_converted = convert_currency(float(o.transport_cost or 0), o.currency, seller_currency)
            actual_logistics_cost += log_converted

        total_costs = actual_mfg_cost + actual_logistics_cost
        total_tax = 0.0

        calculations_breakdown = []
        for c in calcs:
            if c.value_type == 'PERCENTAGE':
                cost_val = round(total_sales * (float(c.value) / 100.0), 2)
            elif c.value_type == 'USD':
                cost_val = convert_currency(float(c.value), 'USD', seller_currency)
            elif c.value_type == 'UZS':
                cost_val = convert_currency(float(c.value), 'UZS', seller_currency)
            else:
                cost_val = float(c.value)
            
            if 'tax' in c.name.lower() or 'vat' in c.name.lower():
                total_tax += cost_val

            total_costs += cost_val
            calculations_breakdown.append({
                'id': c.id,
                'name': c.name,
                'value_type': c.value_type,
                'value': float(c.value),
                'cost': cost_val
            })

        net_profit = round(total_sales - total_costs, 2)

        # Top Products: combine views and sold data (converted)
        top_products = []
        for p in products.order_by('-views_count')[:10]:
            p_items = OrderItem.objects.filter(order__seller=user, product=p).exclude(order__status__in=['PENDING', 'CANCELLED'])
            revenue = 0.0
            for item in p_items:
                revenue += convert_currency(float(item.price * item.quantity), item.order.currency, seller_currency)

            top_products.append({
                'id': p.id,
                'name': p.name,
                'price': convert_currency(float(p.price), p.currency, seller_currency),
                'views_count': p.views_count,
                'total_orders_ann': p_items.values('order').distinct().count(),
                'revenue': revenue,
            })

        finance_breakdown = {
            'revenue': total_sales,
            'tax': round(total_tax, 2),
            'logistics': actual_logistics_cost,
            'manufacturing': actual_mfg_cost,
            'profit': net_profit,
            'calculations': calculations_breakdown
        }

        return Response({
            'overview': {
                'total_views': total_views,
                'total_sales': total_sales,
                'total_orders': total_orders,
                'avg_order_value': avg_order_value,
                'conversion_rate': conversion_rate,
            },
            'total_views': total_views,
            'total_revenue': total_sales,
            'total_orders': total_orders,
            'conversion_rate': conversion_rate,
            'net_revenue': total_sales,
            'total_logistics_cost': round(actual_logistics_cost, 2),
            'total_tax': round(total_tax, 2),
            'total_manufacturing_cost': round(actual_mfg_cost, 2),
            'estimated_profit': net_profit,
            'status_distribution': status_dist,
            'top_products': top_products,
            'sales_trend': [
                {'month': l, 'revenue': d}
                for l, d in zip(sales_trend_labels, sales_trend_data)
            ],
            'views_trend': [
                {'product_name': l, 'views': d}
                for l, d in zip(views_trend_labels, views_trend_data)
            ],
            'calculations': calculations_breakdown,
            'finance': finance_breakdown,
            'currency': seller_currency,
        })


class CRMCalculationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response({'error': 'Only sellers can manage calculations.'}, status=status.HTTP_403_FORBIDDEN)
        
        calcs = CRMCalculation.objects.filter(user=user)
        # Do NOT auto-create defaults — let users define their own

        payload = [{'id': c.id, 'name': c.name, 'value_type': c.value_type, 'value': float(c.value)} for c in calcs]
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response({'error': 'Only sellers can manage calculations.'}, status=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name')
        value_type = request.data.get('value_type', 'PERCENTAGE')
        value = request.data.get('value')

        if not name or value is None:
            return Response({'error': 'Name and value are required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        if value_type not in ['PERCENTAGE', 'USD']:
            return Response({'error': 'value_type must be PERCENTAGE or USD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from decimal import Decimal
            value_dec = Decimal(str(value))
            if value_type == 'PERCENTAGE':
                if value_dec < 0 or value_dec > 100:
                    return Response({'error': 'Percentage must be between 0 and 100.'}, status=status.HTTP_400_BAD_REQUEST)
            else: # USD
                if value_dec < 0:
                    return Response({'error': 'USD value must be greater than or equal to 0.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Invalid value.'}, status=status.HTTP_400_BAD_REQUEST)

        calc = CRMCalculation.objects.create(
            user=user,
            name=name,
            value_type=value_type,
            value=value_dec
        )
        return Response({
            'id': calc.id,
            'name': calc.name,
            'value_type': calc.value_type,
            'value': float(calc.value)
        }, status=status.HTTP_201_CREATED)


class CRMCalculationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response({'error': 'Only sellers can edit calculations.'}, status=status.HTTP_403_FORBIDDEN)
        
        calc = get_object_or_404(CRMCalculation, id=pk, user=user)
        name = request.data.get('name')
        value_type = request.data.get('value_type')
        value = request.data.get('value')

        if not name or value is None or not value_type:
            return Response({'error': 'Name, value, and value_type are required fields.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if value_type not in ['PERCENTAGE', 'USD']:
            return Response({'error': 'value_type must be PERCENTAGE or USD.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from decimal import Decimal
            value_dec = Decimal(str(value))
            if value_type == 'PERCENTAGE':
                if value_dec < 0 or value_dec > 100:
                    return Response({'error': 'Percentage must be between 0 and 100.'}, status=status.HTTP_400_BAD_REQUEST)
            else: # USD
                if value_dec < 0:
                    return Response({'error': 'USD value must be greater than or equal to 0.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Invalid value.'}, status=status.HTTP_400_BAD_REQUEST)

        calc.name = name
        calc.value_type = value_type
        calc.value = value_dec
        calc.save()

        return Response({
            'id': calc.id,
            'name': calc.name,
            'value_type': calc.value_type,
            'value': float(calc.value)
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        user = request.user
        if not user.is_seller:
            return Response({'error': 'Only sellers can delete calculations.'}, status=status.HTTP_403_FORBIDDEN)
        
        calc = get_object_or_404(CRMCalculation, id=pk, user=user)
        calc.delete()
        return Response({'message': 'Calculation deleted successfully.'}, status=status.HTTP_200_OK)
