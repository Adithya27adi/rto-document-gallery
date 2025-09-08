from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-order/<uuid:record_id>/', views.create_order_view, name='create_order'),
    path('process/<str:order_id>/', views.process_payment_view, name='process_payment'),
    path('success/<str:order_id>/', views.payment_success_view, name='payment_success'),
    path('failed/<str:order_id>/', views.payment_failed_view, name='payment_failed'),
    
    # Webhook URLs
    path('webhooks/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
