from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import razorpay
import hmac
import hashlib

from .models import RTORecord, Order, PrintOrder
from .serializers import RTORecordSerializer, OrderSerializer, QRGenerationSerializer, PaymentSerializer

class RTORecordViewSet(viewsets.ModelViewSet):
    """API for RTO Record Management with full functionality."""
    serializer_class = RTORecordSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return RTORecord.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_qr(self, request, pk=None):
        """Generate QR code after document submission."""
        record = self.get_object()
        
        # Check if at least one document is uploaded
        if not record.has_documents():
            return Response(
                {'error': 'Please upload at least one document before generating QR code'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate QR code
        try:
            qr_url = record.generate_qr_code()
            return Response({
                'success': True,
                'qr_code_url': qr_url,
                'record_id': record.id,
                'message': 'QR code generated successfully!'
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate QR code: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download_qr_pdf(self, request, pk=None):
        """Generate PDF with QR code for ₹2 payment."""
        record = self.get_object()
        
        if not record.qr_code_image:
            return Response(
                {'error': 'Generate QR code first'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create PDF with QR code
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Add title
            p.setFont("Helvetica-Bold", 20)
            p.drawString(50, height - 80, f"RTO Record QR Code")
            
            # Add user info
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, height - 120, f"Name: {record.name}")
            p.drawString(50, height - 145, f"Contact: {record.contact_no}")
            p.drawString(50, height - 170, f"Record Type: {record.get_record_type_display()}")
            
            # Add QR code image to PDF
            qr_image_path = record.qr_code_image.path
            p.drawImage(qr_image_path, 50, height - 450, width=300, height=300)
            
            # Add instructions
            p.setFont("Helvetica", 12)
            p.drawString(50, height - 480, "Scan this QR code to view all uploaded documents")
            p.drawString(50, height - 500, f"Record ID: {record.id}")
            p.drawString(50, height - 520, f"Generated on: {record.created_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Add footer
            p.setFont("Helvetica-Oblique", 10)
            p.drawString(50, 50, "© RTO Record Management System - Digitally Generated Document")
            
            p.showPage()
            p.save()
            buffer.seek(0)
            
            # Return PDF response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="RTO_QR_Code_{record.name}_{record.id}.pdf"'
            response.write(buffer.getvalue())
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PaymentViewSet(viewsets.ViewSet):
    """Handle payment processing for QR download, PVC, and NFC cards."""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_razorpay_order(self, request):
        """Create Razorpay order for payment processing."""
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            serializer = PaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            amount = int(float(serializer.validated_data['amount']) * 100)  # Convert to paisa
            order_type = serializer.validated_data['order_type']
            record_id = serializer.validated_data['record_id']
            
            # Verify record belongs to user
            record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
            
            # Create order in Razorpay
            razorpay_order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'receipt': f'{order_type}_{record_id}_{request.user.id}',
                'notes': {
                    'user_id': request.user.id,
                    'record_id': str(record_id),
                    'order_type': order_type
                }
            })
            
            # Create order in our database
            order = Order.objects.create(
                user=request.user,
                rto_record=record,
                order_id=razorpay_order['id'],
                order_type=order_type,
                amount=amount/100,  # Convert paisa to rupees
                total_amount=amount/100,
                payment_provider='razorpay',
                payment_provider_id=razorpay_order['id'],
                delivery_address=serializer.validated_data.get('delivery_address', ''),
                delivery_phone=serializer.validated_data.get('delivery_phone', ''),
                delivery_pincode=serializer.validated_data.get('delivery_pincode', '')
            )
            
            return Response({
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'name': 'RTO Record Management',
                'description': f'{order_type.replace("_", " ").title()} for {record.name}',
                'prefill': {
                    'name': record.name,
                    'contact': record.contact_no,
                    'email': request.user.email
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create payment order: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify payment and process order."""
        try:
            payment_id = request.data.get('payment_id')
            order_id = request.data.get('order_id')
            signature = request.data.get('signature')
            
            if not all([payment_id, order_id, signature]):
                return Response(
                    {'error': 'Missing payment verification data'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify payment signature
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f'{order_id}|{payment_id}'.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature == signature:
                # Payment successful - update order
                order = Order.objects.get(payment_provider_id=order_id, user=request.user)
                order.payment_status = 'completed'
                order.save()
                
                # Create print order for physical cards
                if order.order_type in ['pvc_card', 'nfc_card']:
                    PrintOrder.objects.create(
                        order=order,
                        rto_record=order.rto_record
                    )
                
                return Response({
                    'success': True,
                    'message': 'Payment verified successfully!',
                    'order_id': order.order_id,
                    'order_type': order.order_type,
                    'redirect_url': f'/orders/{order.order_id}/success/'
                })
            else:
                return Response(
                    {'error': 'Payment verification failed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Payment verification error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """API for viewing user orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
