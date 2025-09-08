from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RTORecordViewSet, PaymentViewSet, OrderViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'records', RTORecordViewSet, basename='records')
router.register(r'payments', PaymentViewSet, basename='payments')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]
