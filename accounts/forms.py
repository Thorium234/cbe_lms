# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users with email field and enhanced validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your email'
        })
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Choose a username'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'First name (optional)'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Last name (optional)'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter password'
        })
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        """Validate email with case-insensitive check"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")

        # Case-insensitive check for existing email
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already in use.")
        return email.lower()  # Store email in lowercase

    def clean_username(self):
        """Validate username with enhanced rules"""
        username = self.cleaned_data.get('username')

        if not username:
            raise ValidationError("Username is required.")

        # Check length
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

        if len(username) > 150:
            raise ValidationError("Username cannot exceed 150 characters.")

        # Check for valid characters (letters, numbers, underscores, hyphens)
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters.")

        # Case-insensitive check for existing username
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")

        return username.lower()  # Store username in lowercase

    def clean_password1(self):
        """Validate password strength"""
        password1 = self.cleaned_data.get("password1")

        if not password1:
            raise ValidationError("Password is required.")

        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        # Check for minimum complexity
        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter.")

        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter.")

        if not re.search(r'\d', password1):
            raise ValidationError("Password must contain at least one number.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise ValidationError("Password must contain at least one special character.")

        # Check if password is too similar to username or email
        username = self.cleaned_data.get('username', '').lower()
        email = self.cleaned_data.get('email', '').lower()

        if username and username in password1.lower():
            raise ValidationError("Password is too similar to your username.")

        if email and email.split('@')[0] in password1.lower():
            raise ValidationError("Password is too similar to your email.")

        return password1

    def clean_password2(self):
        """Validate password confirmation"""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match.")

        return password2

    def clean(self):
        """Overall form validation"""
        cleaned_data = super().clean()

        # Additional cross-field validation
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')

        if email and username:
            # Prevent username from being part of email or vice versa
            email_username_part = email.split('@')[0].lower()
            if username.lower() == email_username_part:
                self.add_error('username', "Username cannot be the same as your email username part.")

        return cleaned_data


class CustomUserChangeForm(UserChangeForm):
    """
    Form for updating user information with enhanced validation
    """
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'bio', 'profile_picture')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'username': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '+254700000000'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Tell us about yourself...'
            }),
        }

    def clean_email(self):
        """Validate email during update"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")

        # Check for duplicates (excluding current user)
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This email is already in use.")
        return email.lower()

    def clean_username(self):
        """Validate username during update"""
        username = self.cleaned_data.get('username')
        if not username:
            raise ValidationError("Username is required.")

        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

        if len(username) > 150:
            raise ValidationError("Username cannot exceed 150 characters.")

        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and @/./+/-/_ characters.")

        # Check for duplicates (excluding current user)
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This username is already taken.")
        return username.lower()


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with enhanced styling and validation
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter your email address'
        })
    )

    def clean_email(self):
        """Validate email for password reset"""
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Enter a valid email address.")

        # Check if email exists (case-insensitive)
        if not User.objects.filter(email__iexact=email).exists():
            raise ValidationError("No user with this email address was found.")
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form with enhanced validation
    """
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Enter new password'
        }),
        help_text="""
        <ul class="text-sm text-gray-600 mt-1">
            <li>Your password must contain at least 8 characters.</li>
            <li>Your password must contain uppercase, lowercase, number, and special character.</li>
            <li>Your password can't be too similar to your other personal information.</li>
            <li>Your password can't be a commonly used password.</li>
        </ul>
        """
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm new password'
        })
    )

    def clean_new_password1(self):
        """Validate new password strength"""
        password1 = self.cleaned_data.get("new_password1")

        if not password1:
            raise ValidationError("Password is required.")

        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[A-Z]', password1):
            raise ValidationError("Password must contain at least one uppercase letter.")

        if not re.search(r'[a-z]', password1):
            raise ValidationError("Password must contain at least one lowercase letter.")

        if not re.search(r'\d', password1):
            raise ValidationError("Password must contain at least one number.")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            raise ValidationError("Password must contain at least one special character.")

        # Check if password is too similar to user's information
        user = self.user
        if user.username and user.username.lower() in password1.lower():
            raise ValidationError("Password is too similar to your username.")

        if user.first_name and user.first_name.lower() in password1.lower():
            raise ValidationError("Password is too similar to your first name.")

        if user.last_name and user.last_name.lower() in password1.lower():
            raise ValidationError("Password is too similar to your last name.")

        if user.email:
            email_username_part = user.email.split('@')[0].lower()
            if email_username_part in password1.lower():
                raise ValidationError("Password is too similar to your email.")

        return password1

    def clean_new_password2(self):
        """Validate password confirmation"""
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match.")

        return password2