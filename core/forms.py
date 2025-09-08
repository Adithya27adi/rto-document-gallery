from django import forms
from .models import RTORecord, Order
from authentication.models import User


class RTORecordForm(forms.ModelForm):
    """Enhanced form for RTO record creation with beautiful styling."""
    
    class Meta:
        model = RTORecord
        fields = [
            'name', 'contact_no', 'address',
            'rc_photo', 'insurance_doc', 'pu_check_doc', 'driving_license_doc'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'contact_no': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter contact number',
                'pattern': '[0-9]{10}',
                'title': 'Please enter 10 digit mobile number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address'
            }),
            'rc_photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'data-max-size': '5'  # 5MB max
            }),
            'insurance_doc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf',
                'data-max-size': '10'  # 10MB max
            }),
            'pu_check_doc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf',
                'data-max-size': '10'
            }),
            'driving_license_doc': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf',
                'data-max-size': '10'
            })
        }

    def clean_contact_no(self):
        """Validate contact number format."""
        contact_no = self.cleaned_data.get('contact_no')
        if contact_no and len(contact_no) != 10:
            raise forms.ValidationError('Contact number must be exactly 10 digits')
        if contact_no and not contact_no.isdigit():
            raise forms.ValidationError('Contact number must contain only digits')
        return contact_no


class SchoolRecordForm(forms.ModelForm):
    """Form for school record documents."""
    
    marks_card = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    convocation = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    migration = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf'
        })
    )
    
    class Meta:
        model = RTORecord
        fields = ['name', 'contact_no', 'address']


class OrderForm(forms.ModelForm):
    """Form for order placement with delivery details."""
    
    class Meta:
        model = Order
        fields = ['delivery_address', 'delivery_phone', 'delivery_pincode']
        widgets = {
            'delivery_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete delivery address',
                'required': True
            }),
            'delivery_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery contact number',
                'pattern': '[0-9]{10}',
                'required': True
            }),
            'delivery_pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter pincode',
                'pattern': '[0-9]{6}',
                'required': True
            })
        }
