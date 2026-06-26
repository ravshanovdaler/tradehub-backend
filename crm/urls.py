from django.urls import path
from .views import SellerCRMStatsView, CRMCalculationView, CRMCalculationDetailView

urlpatterns = [
    path('stats/', SellerCRMStatsView.as_view(), name='seller_crm_stats'),
    path('calculations/', CRMCalculationView.as_view(), name='crm_calculations'),
    path('calculations/<int:pk>/', CRMCalculationDetailView.as_view(), name='crm_calculation_detail'),
]
