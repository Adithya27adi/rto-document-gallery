from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.decorators import login_required
from .forms import CustomUserRegistrationForm
from .models import User

class CustomLoginView(LoginView):
    """Enhanced login view with proper redirect."""
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to dashboard after successful login."""
        print("DEBUG: Login successful, redirecting...")  # Debug line
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        print(f"DEBUG: Next URL: {next_url}")  # Debug line
        if next_url and next_url != '':
            return next_url
        return '/dashboard/'
    
    def form_valid(self, form):
        """Add success message and redirect."""
        user = form.get_user()
        print(f"DEBUG: Form valid for user: {user.email}")  # Debug line
        messages.success(self.request, f'Welcome back, {user.first_name or user.email}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Debug form errors."""
        print(f"DEBUG: Login form invalid. Errors: {form.errors}")  # Debug line
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)

class CustomRegistrationView(CreateView):
    """Enhanced registration view with automatic login and redirect."""
    model = User
    form_class = CustomUserRegistrationForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('core:dashboard')
    
    def form_valid(self, form):
        """Save user, log them in automatically, and redirect to dashboard."""
        print("DEBUG: Registration form valid, creating user...")  # Debug line
        try:
            # Save the user
            user = form.save()
            print(f"DEBUG: User created: {user.email}")  # Debug line
            
            # Log the user in automatically
            login(self.request, user)
            print("DEBUG: User logged in automatically")  # Debug line
            
            # Add success message
            messages.success(
                self.request, 
                f'Account created successfully! Welcome to RTO Record Management, {user.first_name or user.email}!'
            )
            
            # Get redirect URL from form or default to dashboard
            next_url = self.request.POST.get('next', '/dashboard/')
            print(f"DEBUG: Redirecting to: {next_url}")  # Debug line
            return redirect(next_url)
            
        except Exception as e:
            print(f"DEBUG: Registration error: {str(e)}")  # Debug line
            messages.error(self.request, f'Registration failed: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Debug form errors."""
        print(f"DEBUG: Registration form invalid. Errors: {form.errors}")  # Debug line
        messages.error(self.request, 'Please correct the errors in the form.')
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect to dashboard after successful registration."""
        return '/dashboard/'

@login_required
def profile_view(request):
    """User profile view."""
    return render(request, 'core/profile.html')

@login_required
def edit_profile_view(request):
    """Edit user profile."""
    if request.method == 'POST':
        messages.success(request, 'Profile updated successfully!')
        return redirect('authentication:profile')
    
    return render(request, 'core/edit_profile.html')
