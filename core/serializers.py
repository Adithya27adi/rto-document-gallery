from rest_framework import serializers
from .models import RTORecord, Order, PrintOrder
from authentication.models import User

class RTORecordSerializer(serializers.ModelSerializer):
    """Serializer for RTO Record with file upload handling."""
    
    document_count = serializers.SerializerMethodField()
    has_documents = serializers.SerializerMethodField()
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RTORecord
        fields = [
            'id', 'name', 'contact_no', 'address', 'record_type', 'status',
            'rc_photo', 'insurance_doc', 'pu_check_doc', 'driving_license_doc',
            'qr_code_image', 'created_at', 'updated_at', 'document_count',
            'has_documents', 'qr_code_url'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'qr_code_image']
    
    def get_document_count(self, obj):
        return obj.get_document_count()
    
    def get_has_documents(self, obj):
        return obj.has_documents()
    
    def get_qr_code_url(self, obj):
        if obj.qr_code_image:
            return obj.qr_code_image.url
        return None

class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order management."""
    
    rto_record_details = RTORecordSerializer(source='rto_record', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'order_type', 'amount', 'shipping_cost', 'total_amount',
            'delivery_address', 'delivery_phone', 'delivery_pincode',
            'payment_status', 'payment_provider', 'created_at', 'updated_at',
            'rto_record_details'
        ]
        read_only_fields = ['order_id', 'created_at', 'updated_at', 'total_amount']

class QRGenerationSerializer(serializers.Serializer):
    """Serializer for QR code generation requests."""
    record_id = serializers.UUIDField()

class PaymentSerializer(serializers.Serializer):
    """Serializer for payment processing."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    order_type = serializers.ChoiceField(choices=Order.OrderType.choices)
    record_id = serializers.UUIDField()
    delivery_address = serializers.CharField(max_length=500, required=False)
    delivery_phone = serializers.CharField(max_length=20, required=False)
    delivery_pincode = serializers.CharField(max_length=10, required=False)
