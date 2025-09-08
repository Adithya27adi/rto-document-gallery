from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class PaymentGateway(models.Model):
    """Configuration for payment gateways."""
    
    class Provider(models.TextChoices):
        RAZORPAY = 'razorpay', 'Razorpay'
        STRIPE = 'stripe', 'Stripe'
    
    provider = models.CharField(max_length=20, choices=Provider.choices, unique=True)
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=True)
    
    # Configuration
    supported_currencies = models.JSONField(default=list)
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.9)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_gateway'
        verbose_name = 'Payment Gateway'
        verbose_name_plural = 'Payment Gateways'
    
    def __str__(self):
        mode = "Test" if self.is_test_mode else "Live"
        return f"{self.get_provider_display()} ({mode})"


class PaymentTransaction(models.Model):
    """Track individual payment transactions with detailed information."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'
        REFUNDED = 'refunded', 'Refunded'
        PARTIALLY_REFUNDED = 'partially_refunded', 'Partially Refunded'
    
    # Transaction Details
    transaction_id = models.CharField(max_length=100, unique=True)
    order = models.ForeignKey('core.Order', on_delete=models.CASCADE, related_name='transactions')
    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    
    # Payment Information
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Provider Details
    provider_transaction_id = models.CharField(max_length=200, blank=True)
    provider_payment_id = models.CharField(max_length=200, blank=True)
    provider_signature = models.CharField(max_length=500, blank=True)
    
    # Response Data
    provider_response = models.JSONField(default=dict)
    failure_reason = models.TextField(blank=True)
    
    # Refund Information
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refund_reason = models.TextField(blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transaction'
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.gateway.provider} - ₹{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        # Set completed_at when status changes to success
        if self.status == self.Status.SUCCESS and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Generate unique transaction ID."""
        return f"TXN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:10].upper()}"


class WebhookEvent(models.Model):
    """Track webhook events from payment providers for idempotency."""
    
    class EventType(models.TextChoices):
        PAYMENT_SUCCESS = 'payment.success', 'Payment Success'
        PAYMENT_FAILED = 'payment.failed', 'Payment Failed'
        PAYMENT_CANCELLED = 'payment.cancelled', 'Payment Cancelled'
        REFUND_PROCESSED = 'refund.processed', 'Refund Processed'
        OTHER = 'other', 'Other'
    
    # Event Details
    event_id = models.CharField(max_length=200, unique=True)
    provider = models.CharField(max_length=20, choices=PaymentGateway.Provider.choices)
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    
    # Related Objects
    transaction = models.ForeignKey(
        PaymentTransaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='webhook_events'
    )
    
    # Event Data
    raw_data = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_result = models.JSONField(default=dict)
    
    # Metadata
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_event'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        ordering = ['-received_at']
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.event_id}"
    
    def mark_processed(self, result=None):
        """Mark webhook event as processed."""
        self.processed = True
        self.processed_at = timezone.now()
        if result:
            self.processing_result = result
        self.save(update_fields=['processed', 'processed_at', 'processing_result'])
