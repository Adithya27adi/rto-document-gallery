import razorpay
import hmac
import hashlib
import json
import qrcode
import os
from io import BytesIO
from urllib.parse import urljoin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.files import File

from .models import RTORecord, Order
from .forms import RTORecordForm, SchoolRecordForm, OrderForm

def landing_view(request):
    return render(request, 'landing.html')

def home_view(request):
    """Home page view - redirects to dashboard if authenticated, otherwise to landing"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return redirect('core:landing')

@login_required
def dashboard_view(request):
    user_records_qs = RTORecord.objects.filter(owner=request.user).order_by("-created_at")
    user_orders_qs = Order.objects.filter(user=request.user).order_by("-created_at")
    
    user_records = user_records_qs[:10]
    user_orders = user_orders_qs[:5]
    
    stats = {
        "total_records": user_records_qs.count(),
        "approved_records": user_records_qs.filter(status='approved').count(),
        "pending_records": user_records_qs.filter(status='pending').count(),
        "total_orders": user_orders_qs.count(),
    }
    
    return render(request, 'core/dashboard.html', {
        'user_records': user_records,
        'user_orders': user_orders,
        'stats': stats,
    })

@csrf_exempt
@login_required
def ajax_create_record(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name")
    contact_no = data.get("contact_no")
    address = data.get("address")
    record_type = data.get("record_type")
    cloudinary_urls = data.get("uploaded_documents", [])

    if not all([name, contact_no, address, record_type]) or not cloudinary_urls:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    # Create record with Cloudinary URLs only (no file storage)
    record = RTORecord.objects.create(
        owner=request.user,
        record_type=record_type,
        name=name,
        contact_no=contact_no,
        address=address,
    )
    
    # Store Cloudinary URLs in the record based on type
    urls = list(cloudinary_urls)
    if record_type == "rto":
        if len(urls) > 0: record.rc_photo = urls[0]
        if len(urls) > 1: record.insurance_doc = urls[1]
        if len(urls) > 2: record.pu_check_doc = urls[2]
        if len(urls) > 3: record.driving_license_doc = urls[3]
    elif record_type == "school":
        if len(urls) > 0: record.marks_card = urls[0]
        if len(urls) > 1: record.photo = urls[1]
        if len(urls) > 2: record.convocation = urls[2]
        if len(urls) > 3: record.migration = urls[3]
    
    record.save()

    # Create Razorpay order for ₹2
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount_paise = 200  # ₹2 in paise
    
    razorpay_order = client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': 1,
    })

    order = Order.objects.create(
        user=request.user,
        rto_record=record,
        order_id=razorpay_order['id'],
        order_type='qr_download',
        amount=2.00,
        payment_status=Order.Status.PENDING,
        payment_provider='razorpay',
    )

    payment_url = reverse('core:payment', kwargs={'record_id': record.id, 'order_type': 'qr_download'})
    return JsonResponse({'payment_url': payment_url})

@login_required
def create_record_view(request, record_type):
    if record_type == 'school':
        form_class = SchoolRecordForm
    else:
        form_class = RTORecordForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.owner = request.user
            record.record_type = record_type
            record.save()
            messages.success(request, "Record created successfully. Proceed to payment.")
            return redirect('core:payment', record_id=record.id, order_type='qr_download')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = form_class()

    return render(request, 'core/create_record.html', {'form': form, 'record_type': record_type})

@login_required
def edit_record_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    if record.record_type == 'school':
        form_class = SchoolRecordForm
    else:
        form_class = RTORecordForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Record updated successfully.")
            return redirect('core:record_detail', record_id=record.id)
    else:
        form = form_class(instance=record)

    return render(request, 'edit_record.html', {'form': form, 'record': record})

@login_required
def record_detail_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    orders = Order.objects.filter(rto_record=record)
    return render(request, 'record_detail.html', {'record': record, 'orders': orders})

@login_required
def payment_view(request, record_id, order_type):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    pricing = {
        'qr_download': {'amount': 200, 'title': 'QR Code Download', 'description': 'Digital QR Code', 'currency': 'INR'},
        'pvc_card': {'amount': 10000, 'title': 'PVC Card', 'description': 'Physical PVC Card', 'currency': 'INR'},
        'nfc_card': {'amount': 40000, 'title': 'NFC Card', 'description': 'NFC Card', 'currency': 'INR'},
    }
    if order_type not in pricing:
        messages.error(request, "Invalid payment option selected.")
        return redirect('core:dashboard')

    payment_info = pricing[order_type]
    amount = payment_info['amount']

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create(dict(
        amount=amount,
        currency=payment_info['currency'],
        payment_capture=1,
    ))

    order = Order.objects.create(
        user=request.user,
        rto_record=record,
        order_id=razorpay_order['id'],
        order_type=order_type,
        amount=amount / 100.0,
        payment_status=Order.Status.PENDING,
        payment_provider='razorpay',
    )

    context = {
        'record': record,
        'order': order,
        'razorpay_order': json.dumps(razorpay_order),
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'payment_info': payment_info,
        'order_type': order_type,
        'amount_in_rupees': amount / 100.0,
    }

    return render(request, 'core/payment.html', context)

@csrf_exempt
@login_required
def verify_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    data = json.loads(request.body)
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')

    try:
        order = Order.objects.get(order_id=razorpay_order_id, user=request.user)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)

    # Verify payment signature
    generated_signature = hmac.new(
        key=settings.RAZORPAY_KEY_SECRET.encode(),
        msg=f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if generated_signature != razorpay_signature:
        order.payment_status = Order.Status.FAILED
        order.save()
        return JsonResponse({'error': 'Signature verification failed'}, status=400)

    # Payment successful
    order.payment_status = Order.Status.COMPLETED
    order.payment_provider_payment_id = razorpay_payment_id
    order.save()
    
    record = order.rto_record
    
    # Generate HTML gallery page
    gallery_html = generate_gallery_html(record)
    
    # Save HTML file with proper folder structure
    folder_name = save_html_file(record, gallery_html)
    
    # Generate QR code pointing to folder path (not file path)
    netlify_url = f"https://shiny-yeot-9e86c3.netlify.app/{folder_name}/"
    generate_qr_code_for_record(record, netlify_url)
    
    # Store gallery URL in record
    record.gallery_html_url = netlify_url
    record.save()
    

    redirect_url = reverse('core:qr_success', kwargs={'record_id': record.id})
    return JsonResponse({'success': True, 'redirect_url': redirect_url})

def generate_gallery_html(record):
    """Generate HTML gallery page with Cloudinary URLs"""
    docs = []
    
    # Collect document URLs from cloudinary_urls field
    for i, url in enumerate(record.cloudinary_urls):
        docs.append({
            'url': url,
            'label': f'Document {i+1}',
            'download_url': url.replace('/upload/', '/upload/fl_attachment/')
        })
    
    # Generate ZIP download URL using Cloudinary's archive feature
    public_ids = []
    for url in record.cloudinary_urls:
        if 'cloudinary.com' in url:
            # Extract public ID from URL
            parts = url.split('/')
            if len(parts) > 7:
                public_id = '/'.join(parts[-2:]).split('.')[0]
                public_ids.append(public_id)
    
    zip_url = ""
    if public_ids:
        cloud_name = settings.CLOUDINARY_CLOUD_NAME
        zip_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/fl_attachment,archive={','.join(public_ids)}.zip"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Documents for {record.name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
            .header h1 {{ color: #333; margin-bottom: 10px; font-size: 2.5em; }}
            .header p {{ color: #666; font-size: 1.1em; }}
            .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px; margin-bottom: 40px; }}
            .doc-card {{ background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 25px rgba(0,0,0,0.15); transition: transform 0.3s ease; }}
            .doc-card:hover {{ transform: translateY(-5px); }}
            .doc-image {{ width: 100%; height: 250px; object-fit: cover; border-bottom: 1px solid #eee; }}
            .doc-info {{ padding: 20px; text-align: center; }}
            .doc-info h3 {{ margin: 0 0 15px 0; color: #333; font-size: 1.2em; }}
            .btn-group {{ display: flex; gap: 10px; justify-content: center; }}
            .btn {{ padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: 500; transition: all 0.3s ease; }}
            .btn-view {{ background: #667eea; color: white; }}
            .btn-view:hover {{ background: #5a67d8; }}
            .btn-download {{ background: #48bb78; color: white; }}
            .btn-download:hover {{ background: #38a169; }}
            .download-all {{ display: block; width: 300px; margin: 0 auto; padding: 20px; background: linear-gradient(45deg, #667eea, #764ba2); color: white; text-align: center; text-decoration: none; border-radius: 15px; font-weight: bold; font-size: 1.2em; box-shadow: 0 8px 25px rgba(0,0,0,0.2); transition: transform 0.3s ease; }}
            .download-all:hover {{ transform: translateY(-2px); }}
            .footer {{ text-align: center; margin-top: 40px; color: rgba(255,255,255,0.8); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📄 Documents for {record.name}</h1>
                <p><strong>📞 Contact:</strong> {record.contact_no}</p>
                <p><strong>🏷️ Type:</strong> {record.get_record_type_display()}</p>
                <p><strong>📅 Created:</strong> {record.created_at.strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="gallery">
    """
    
    for doc in docs:
        html += f"""
                <div class="doc-card">
                    <img src="{doc['url']}" alt="{doc['label']}" class="doc-image" loading="lazy">
                    <div class="doc-info">
                        <h3>{doc['label']}</h3>
                        <div class="btn-group">
                            <a href="{doc['url']}" class="btn btn-view" target="_blank">👁️ View</a>
                            <a href="{doc['download_url']}" class="btn btn-download" target="_blank">⬇️ Download</a>
                        </div>
                    </div>
                </div>
        """
    
    html += """
            </div>
            
    """
    
    if zip_url:
        html += f"""
            <a href="{zip_url}" class="download-all" target="_blank">
                📦 Download All Documents (ZIP)
            </a>
        """
    
    html += f"""
            <div class="footer">
                <p>Generated by RTO Management System | Secure Document Storage</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def save_html_file(record, content):
    """Save HTML to local file with proper Netlify folder structure"""
    # Create folder for this record
    record_folder = f'netlify_uploads/record_{record.id}'
    os.makedirs(record_folder, exist_ok=True)
    
    # Save HTML as index.html inside the record folder
    filepath = os.path.join(record_folder, 'index.html')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Create _redirects file in the record folder
    redirects_path = os.path.join(record_folder, '_redirects')
    with open(redirects_path, 'w') as f:
        f.write('/* /index.html 200\n')
    
    print(f"HTML file saved: {filepath}")
    print(f"Redirects file created: {redirects_path}")
    
    return f'record_{record.id}'  # Return folder name


def generate_qr_code_for_record(record, url):
    """Generate QR code pointing to the gallery URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create QR image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to model
    blob = BytesIO()
    img.save(blob, 'PNG')
    blob.seek(0)
    
    record.qr_code_image.save(f'qr_{record.id}.png', File(blob), save=False)
    record.save()

# Add all your other missing views
@login_required
def generate_qr_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    if not record.has_documents():
        messages.error(request, 'Please upload at least one document before generating QR code.')
        return redirect('core:record_detail', record_id=record.id)
    try:
        qr_url = record.generate_qr_code()
        messages.success(request, 'QR code generated successfully!')
        return redirect('core:record_detail', record_id=record.id)
    except Exception as e:
        messages.error(request, f'Failed to generate QR code: {str(e)}')
        return redirect('core:record_detail', record_id=record.id)

@login_required
def qr_preview_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    return render(request, 'qr_preview.html', {'record': record})

@require_POST
@login_required
def create_payment_order(request):
    return JsonResponse({'success': True, 'message': 'Payment order created'})

@login_required
def download_qr_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    if not record.qr_code_image:
        record.generate_qr_code()
    return render(request, 'core/download_qr.html', {'record': record})

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders.html', {'orders': orders})

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})

@login_required
def order_cancel_view(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    messages.info(request, "Order cancellation requested.")
    return redirect('core:orders')

@login_required
def verify_record_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id)
    return render(request, 'verify_record.html', {'record': record})

@login_required
def profile_view(request):
    return render(request, 'profile.html')

@login_required
def edit_profile_view(request):
    return render(request, 'edit_profile.html')

@login_required
def search_records_view(request):
    return redirect('core:dashboard')

@login_required
def export_records_view(request):
    return redirect('core:dashboard')
@login_required
def qr_success_view(request, record_id):
    record = get_object_or_404(RTORecord, id=record_id, owner=request.user)
    return render(request, 'core/qr_success.html', {'record': record})

