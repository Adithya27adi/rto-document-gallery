from django.contrib import admin
from .models import RTORecord, Order, PrintOrder

@admin.register(RTORecord)
class RTORecordAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'record_type', 'status', 'created_at']
    list_filter = ['status', 'record_type', 'created_at']
    search_fields = ['name', 'contact_no', 'owner__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'reviewed_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'owner', 'name', 'contact_no', 'address', 'record_type')
        }),
        ('Documents', {
            'fields': ('rc_photo', 'insurance_doc', 'pu_check_doc', 'driving_license_doc')
        }),
        ('Generated Files', {
            'fields': ('qr_code_image', 'pdf_card_filepath')
        }),
        ('Review Information', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'order_type', 'total_amount', 'payment_status', 'created_at']
    list_filter = ['order_type', 'payment_status', 'payment_provider', 'created_at']
    search_fields = ['order_id', 'user__email', 'rto_record__name']
    readonly_fields = ['order_id', 'total_amount', 'created_at', 'updated_at', 'completed_at']

@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'tracking_number', 'shipping_partner', 'created_at']
    list_filter = ['status', 'shipping_partner', 'created_at']
    search_fields = ['order__order_id', 'tracking_number']
