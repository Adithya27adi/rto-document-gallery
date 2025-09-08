from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import User
import uuid

class CustomUserRegistrationForm(UserCreationForm):
    """Enhanced registration form with profile picture and state selection."""
    
    INDIAN_STATES = [
        ('', 'Select Your State'),
        ('andhra-pradesh', 'Andhra Pradesh'),
        ('arunachal-pradesh', 'Arunachal Pradesh'),
        ('assam', 'Assam'),
        ('bihar', 'Bihar'),
        ('chhattisgarh', 'Chhattisgarh'),
        ('goa', 'Goa'),
        ('gujarat', 'Gujarat'),
        ('haryana', 'Haryana'),
        ('himachal-pradesh', 'Himachal Pradesh'),
        ('jharkhand', 'Jharkhand'),
        ('karnataka', 'Karnataka'),
        ('kerala', 'Kerala'),
        ('madhya-pradesh', 'Madhya Pradesh'),
        ('maharashtra', 'Maharashtra'),
        ('manipur', 'Manipur'),
        ('meghalaya', 'Meghalaya'),
        ('mizoram', 'Mizoram'),
        ('nagaland', 'Nagaland'),
        ('odisha', 'Odisha'),
        ('punjab', 'Punjab'),
        ('rajasthan', 'Rajasthan'),
        ('sikkim', 'Sikkim'),
        ('tamil-nadu', 'Tamil Nadu'),
        ('telangana', 'Telangana'),
        ('tripura', 'Tripura'),
        ('uttar-pradesh', 'Uttar Pradesh'),
        ('uttarakhand', 'Uttarakhand'),
        ('west-bengal', 'West Bengal'),
        ('delhi', 'Delhi'),
        ('chandigarh', 'Chandigarh'),
        ('puducherry', 'Puducherry'),
    ]
    
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your full name'
        })
    )
    
    phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter 10-digit mobile number',
            'pattern': '[0-9]{10}'
        })
    )
    
    state = forms.ChoiceField(
        choices=INDIAN_STATES,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your complete address'
        })
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'state', 'address', 'profile_picture', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your email'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Create strong password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Confirm your password'
            })
        }

    def clean_phone(self):
        """Validate phone number."""
        phone = self.cleaned_data.get('phone')
        if phone and len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits')
        if phone and not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only digits')
        return phone

    def save(self, commit=True):
        """Save user with additional fields."""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('full_name')
        user.phone = self.cleaned_data.get('phone')
        user.state = self.cleaned_data.get('state')
        user.address = self.cleaned_data.get('address')
        
        if commit:
            user.save()
            # Handle profile picture if provided
            profile_picture = self.cleaned_data.get('profile_picture')
            if profile_picture:
                user.profile_picture = profile_picture
                user.save()
        
        return user
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
import uuid


class CustomUserRegistrationForm(UserCreationForm):
    """Enhanced registration form with profile picture and state selection."""
    
    INDIAN_STATES = [
        ('', 'Select Your State'),
        ('andhra-pradesh', 'Andhra Pradesh'),
        ('arunachal-pradesh', 'Arunachal Pradesh'),
        ('assam', 'Assam'),
        ('bihar', 'Bihar'),
        ('chhattisgarh', 'Chhattisgarh'),
        ('goa', 'Goa'),
        ('gujarat', 'Gujarat'),
        ('haryana', 'Haryana'),
        ('himachal-pradesh', 'Himachal Pradesh'),
        ('jharkhand', 'Jharkhand'),
        ('karnataka', 'Karnataka'),
        ('kerala', 'Kerala'),
        ('madhya-pradesh', 'Madhya Pradesh'),
        ('maharashtra', 'Maharashtra'),
        ('manipur', 'Manipur'),
        ('meghalaya', 'Meghalaya'),
        ('mizoram', 'Mizoram'),
        ('nagaland', 'Nagaland'),
        ('odisha', 'Odisha'),
        ('punjab', 'Punjab'),
        ('rajasthan', 'Rajasthan'),
        ('sikkim', 'Sikkim'),
        ('tamil-nadu', 'Tamil Nadu'),
        ('telangana', 'Telangana'),
        ('tripura', 'Tripura'),
        ('uttar-pradesh', 'Uttar Pradesh'),
        ('uttarakhand', 'Uttarakhand'),
        ('west-bengal', 'West Bengal'),
        ('delhi', 'Delhi'),
        ('chandigarh', 'Chandigarh'),
        ('puducherry', 'Puducherry'),
    ]
    
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your full name'
        })
    )
    
    phone = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter 10-digit mobile number',
            'pattern': '[0-9]{10}'
        })
    )
    
    state = forms.ChoiceField(
        choices=INDIAN_STATES,
        widget=forms.Select(attrs={
            'class': 'form-control form-select-lg'
        })
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter your complete address'
        })
    )
    
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone', 'state', 'address', 'profile_picture', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter your email'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Create strong password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Confirm your password'
            }),
        }

    def clean_phone(self):
        """Validate phone number."""
        phone = self.cleaned_data.get('phone')
        if phone and len(phone) != 10:
            raise forms.ValidationError('Phone number must be exactly 10 digits')
        if phone and not phone.isdigit():
            raise forms.ValidationError('Phone number must contain only digits')
        return phone

    def clean_email(self):
        """Validate uniqueness of email."""
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def save(self, commit=True):
        """Save user with additional fields and unique username handling."""
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('full_name')
        user.phone = self.cleaned_data.get('phone')
        user.state = self.cleaned_data.get('state')
        user.address = self.cleaned_data.get('address')

        # Auto-generate unique username to avoid conflicts
        if not user.username or User.objects.filter(username=user.username).exists():
            user.username = str(uuid.uuid4())[:30]  # Unique identifier for username

        if commit:
            user.save()
            profile_picture = self.cleaned_data.get('profile_picture')
            if profile_picture:
                user.profile_picture = profile_picture
                user.save()
        
        return user
