import uuid
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordResetForm, CustomSetPasswordForm
from .models import CustomUser, UserActivity, EmailVerificationToken, PasswordResetToken, SiteSettings
import os
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

User = get_user_model()

class CustomLoginView(LoginView):
    """Custom login view with enhanced security and logging"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Handle successful login"""
        response = super().form_valid(form)
        try:
            # Log user activity
            UserActivity.objects.create(
                user=self.request.user,
                action='LOGIN',
                ip_address=self.get_client_ip(),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            messages.success(self.request, f'Welcome back, {self.request.user.username}!')
            logger.info(f"User {self.request.user.username} logged in successfully")
        except Exception as e:
            logger.error(f"Error logging login activity for user {self.request.user.username}: {str(e)}")
        return response

    def get_client_ip(self):
        """Get client IP address with fallbacks"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR', 'unknown')
        return ip

    def get_context_data(self, **kwargs):
        """Add additional context for the login template"""
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = SiteSettings.load()
            context['google_login_url'] = reverse('social:begin', args=['google-oauth2'])  # Use dynamic URL resolution
        except Exception as e:
            logger.error(f"Error loading site settings or Google login URL: {str(e)}")
            context['site_settings'] = None
            context['google_login_url'] = ''  # Fallback to empty string
        return context


class CustomLogoutView(LogoutView):
    """Custom logout view with activity logging"""
    next_page = 'lms:home'

    def dispatch(self, request, *args, **kwargs):
        """Log user activity before logout"""
        if request.user.is_authenticated:
            try:
                UserActivity.objects.create(
                    user=request.user,
                    action='LOGOUT',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
                )
                logger.info(f"User {request.user.username} logged out")
            except Exception as e:
                logger.error(f"Error logging logout activity for user {request.user.username}: {str(e)}")
        return super().dispatch(request, *args, **kwargs)

    def get_client_ip(self, request):
        """Get client IP address with fallbacks"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class SignupView(CreateView):
    """User signup view with email verification"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        """Handle valid signup form submission"""
        try:
            # Check if username already exists (case-insensitive)
            username = form.cleaned_data['username']
            if User.objects.filter(username__iexact=username).exists():
                form.add_error('username', 'A user with this username already exists.')
                return self.form_invalid(form)

            # Check if email already exists (case-insensitive)
            email = form.cleaned_data['email']
            if User.objects.filter(email__iexact=email).exists():
                form.add_error('email', 'A user with this email address already exists.')
                return self.form_invalid(form)

            # Create user but don't activate yet
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Create email verification token
            token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )

            # Send verification email
            self.send_verification_email(user, token)

            messages.success(
                self.request,
                'Account created successfully! Please check your email to verify your account.'
            )
            logger.info(f"User {user.username} signed up successfully")
            return redirect('accounts:login')

        except Exception as e:
            logger.error(f"Error during signup process: {str(e)}")
            messages.error(self.request, 'An error occurred during signup. Please try again.')
            return self.form_invalid(form)

    def send_verification_email(self, user, token):
        """Send email verification email with error handling"""
        try:
            current_site = get_current_site(self.request)
            subject = 'Verify your email address'
            context = {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'https' if self.request.is_secure() else 'http',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': token.token,
            }
            html_message = render_to_string('accounts/emails/verification_email.html', context)
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=os.environ.get('EMAIL_HOST_USER', 'noreply@yourdomain.com'),
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {str(e)}")


def activate_account(request, token):
    """Activate user account with token"""
    try:
        token_obj = EmailVerificationToken.objects.select_related('user').get(token=token)
        if token_obj.expires_at < timezone.now():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            logger.warning(f"Expired verification link used: {token}")
            return redirect('accounts:signup')

        user = token_obj.user
        user.is_active = True
        user.email_verified = True
        user.save()

        # Log the user in
        login(request, user)

        # Delete the token
        token_obj.delete()

        # Send welcome email
        send_welcome_email(user)

        messages.success(request, 'Your account has been verified successfully!')
        logger.info(f"User {user.username} account activated successfully")
        return redirect('lms:home')

    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        logger.warning(f"Invalid verification link used: {token}")
        return redirect('accounts:signup')
    except Exception as e:
        logger.error(f"Error during account activation: {str(e)}")
        messages.error(request, 'An error occurred during account activation. Please try again.')
        return redirect('accounts:signup')


def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        subject = 'Welcome to Our Platform!'
        context = {
            'user': user,
            'site_name': getattr(SiteSettings.load(), 'site_name', 'Our Platform')
        }
        html_message = render_to_string('accounts/emails/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=os.environ.get('EMAIL_HOST_USER', 'noreply@yourdomain.com'),
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending welcome email to {user.email}: {str(e)}")


@login_required
def profile(request):
    """User profile view with error handling"""
    try:
        user_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]
        context = {
            'user_activities': user_activities,
            'site_settings': SiteSettings.load(),
        }
        return render(request, 'accounts/profile.html', context)
    except Exception as e:
        logger.error(f"Error loading profile for user {request.user.username}: {str(e)}")
        messages.error(request, 'An error occurred while loading your profile. Please try again.')
        return redirect('lms:home')


@login_required
def edit_profile(request):
    """Edit user profile with proper form handling"""
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                # Check for username conflicts (case-insensitive)
                username = form.cleaned_data['username']
                existing_user = User.objects.filter(username__iexact=username).exclude(pk=request.user.pk).first()
                if existing_user:
                    form.add_error('username', 'This username is already taken.')
                    return render(request, 'accounts/edit_profile.html', {'form': form})
                form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                logger.info(f"User {request.user.username} updated profile")
                return redirect('accounts:profile')
            except Exception as e:
                logger.error(f"Error updating profile for user {request.user.username}: {str(e)}")
                messages.error(request, 'An error occurred while updating your profile.')
        # If form is invalid, fall through to render with errors
    else:
        form = CustomUserChangeForm(instance=request.user)
    context = {
        'form': form,
        'site_settings': SiteSettings.load(),
    }
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def change_password(request):
    """Handle password change with comprehensive validation"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')

        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            logger.warning(f"Failed password change attempt for user {request.user.username} - incorrect current password")
            return redirect('accounts:edit_profile')

        # Validate new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            logger.warning(f"Failed password change attempt for user {request.user.username} - passwords don't match")
            return redirect('accounts:edit_profile')

        # Validate password strength
        if len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            logger.warning(f"Failed password change attempt for user {request.user.username} - password too short")
            return redirect('accounts:edit_profile')

        # Additional password strength validation
        if not any(c.isupper() for c in new_password1):
            messages.error(request, 'New password must contain at least one uppercase letter.')
            return redirect('accounts:edit_profile')

        if not any(c.islower() for c in new_password1):
            messages.error(request, 'New password must contain at least one lowercase letter.')
            return redirect('accounts:edit_profile')

        if not any(c.isdigit() for c in new_password1):
            messages.error(request, 'New password must contain at least one number.')
            return redirect('accounts:edit_profile')

        # Check if new password is too similar to username or email
        if new_password1.lower() in request.user.username.lower() or new_password1.lower() in request.user.email.lower():
            messages.error(request, 'New password is too similar to your username or email.')
            return redirect('accounts:edit_profile')

        try:
            # Change password
            request.user.set_password(new_password1)
            request.user.save()

            # Update session to prevent logout
            update_session_auth_hash(request, request.user)

            # Log password change
            UserActivity.objects.create(
                user=request.user,
                action='PASSWORD_CHANGE',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
            )
            messages.success(request, 'Your password has been changed successfully!')
            logger.info(f"User {request.user.username} changed password successfully")
            return redirect('accounts:profile')

        except Exception as e:
            logger.error(f"Error changing password for user {request.user.username}: {str(e)}")
            messages.error(request, 'An error occurred while changing your password.')
            return redirect('accounts:edit_profile')
    return redirect('accounts:edit_profile')


def get_client_ip(request):
    """Get client IP address with fallbacks"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


@require_http_methods(["GET"])
def check_username(request):
    """Check if username is available with comprehensive validation"""
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'error': 'Username is required'})
    if len(username) < 3:
        return JsonResponse({'available': False, 'error': 'Username must be at least 3 characters long'})
    if len(username) > 150:
        return JsonResponse({'available': False, 'error': 'Username must be less than 150 characters'})
    if not username.replace('_', '').isalnum():
        return JsonResponse({'available': False, 'error': 'Username can only contain letters, numbers, and underscores'})
    try:
        if request.user.is_authenticated:
            if User.objects.filter(username__iexact=username).exclude(pk=request.user.pk).exists():
                return JsonResponse({'available': False, 'error': 'Username is already taken'})
        else:
            if User.objects.filter(username__iexact=username).exists():
                return JsonResponse({'available': False, 'error': 'Username is already taken'})
        return JsonResponse({'available': True})
    except Exception as e:
        logger.error(f"Error checking username availability for '{username}': {str(e)}")
        return JsonResponse({'available': False, 'error': 'An error occurred. Please try again.'})


@require_http_methods(["GET"])
def check_email(request):
    """Check if email is available with comprehensive validation"""
    email = request.GET.get('email', '').strip()
    if not email:
        return JsonResponse({'available': False, 'error': 'Email is required'})
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'available': False, 'error': 'Invalid email format'})
    try:
        if request.user.is_authenticated:
            if User.objects.filter(email__iexact=email).exclude(pk=request.user.pk).exists():
                return JsonResponse({'available': False, 'error': 'Email is already in use'})
        else:
            if User.objects.filter(email__iexact=email).exists():
                return JsonResponse({'available': False, 'error': 'Email is already in use'})
        return JsonResponse({'available': True})
    except Exception as e:
        logger.error(f"Error checking email availability for '{email}': {str(e)}")
        return JsonResponse({'available': False, 'error': 'An error occurred. Please try again.'})


def about(request):
    """About page view with error handling"""
    try:
        site_settings = SiteSettings.load()
        context = {
            'site_settings': site_settings,
        }
        return render(request, 'accounts/about.html', context)
    except Exception as e:
        logger.error(f"Error loading about page: {str(e)}")
        messages.error(request, 'An error occurred while loading this page. Please try again.')
        return redirect('lms:home')


def contact(request):
    """Contact page view with error handling"""
    try:
        site_settings = SiteSettings.load()
        context = {
            'site_settings': site_settings,
        }
        return render(request, 'accounts/contact.html', context)
    except Exception as e:
        logger.error(f"Error loading contact page: {str(e)}")
        messages.error(request, 'An error occurred while loading this page. Please try again.')
        return redirect('lms:home')


def terms_of_service(request):
    """Terms of service page view with error handling"""
    try:
        site_settings = SiteSettings.load()
        context = {
            'site_settings': site_settings,
        }
        return render(request, 'accounts/terms.html', context)
    except Exception as e:
        logger.error(f"Error loading terms of service page: {str(e)}")
        messages.error(request, 'An error occurred while loading this page. Please try again.')
        return redirect('lms:home')


def privacy_policy(request):
    """Privacy policy page view with error handling"""
    try:
        site_settings = SiteSettings.load()
        context = {
            'site_settings': site_settings,
        }
        return render(request, 'accounts/privacy.html', context)
    except Exception as e:
        logger.error(f"Error loading privacy policy page: {str(e)}")
        messages.error(request, 'An error occurred while loading this page. Please try again.')
        return redirect('lms:home')


@require_http_methods(["GET"])
def debug_env(request):
    """
    Debug view to check environment variables
    WARNING: Only use this in development, never in production
    """
    if not request.user.is_superuser:
        logger.warning(f"Unauthorized access to debug_env by user {request.user.username}")
        return HttpResponse("Access denied", status=403)
    content = "<h1>Environment Variables</h1>"
    content += f"<p>SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: {os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', 'Not found')}</p>"
    content += f"<p>SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: {'Set' if os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET') else 'Not set'}</p>"
    content += f"<p>DJANGO_SECRET_KEY: {'Set' if os.environ.get('DJANGO_SECRET_KEY') else 'Not set'}</p>"
    content += f"<p>DJANGO_DEBUG: {os.environ.get('DJANGO_DEBUG', 'Not set')}</p>"
    return HttpResponse(content)