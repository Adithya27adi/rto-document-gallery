from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

def create_order_view(request, record_id):
    """Create order view placeholder."""
    return render(request, 'payments/create_order.html')

def process_payment_view(request, order_id):
    """Process payment view placeholder."""
    return render(request, 'payments/process_payment.html')

def payment_success_view(request, order_id):
    """Payment success view placeholder."""
    return render(request, 'payments/payment_success.html')

def payment_failed_view(request, order_id):
    """Payment failed view placeholder."""
    return render(request, 'payments/payment_failed.html')

@csrf_exempt
def razorpay_webhook(request):
    """Razorpay webhook handler placeholder."""
    return HttpResponse("OK")

@csrf_exempt
def stripe_webhook(request):
    """Stripe webhook handler placeholder."""
    return HttpResponse("OK")
