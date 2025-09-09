# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """
    Custom User model with additional fields for a reusable accounts app
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    is_premium = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        # Add unique constraint for username (case-insensitive)
        constraints = [
            models.UniqueConstraint(
                fields=['username'],
                name='unique_username_case_insensitive'
            ),
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email_case_insensitive'
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return full name or username if full name is empty"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def save(self, *args, **kwargs):
        """Override save method to ensure username is lowercase"""
        if self.username:
            self.username = self.username.lower()
        super().save(*args, **kwargs)


class UserActivity(models.Model):
    """
    Track user activities for analytics and security
    """
    ACTION_CHOICES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('ACCOUNT_CREATION', 'Account Creation'),
        ('EMAIL_VERIFICATION', 'Email Verification'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('FILE_DOWNLOAD', 'File Download'),
        ('FILE_UPLOAD', 'File Upload'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, max_length=500)
    additional_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"


class EmailVerificationToken(models.Model):
    """
    Token for email verification
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='email_verification_token')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Verification token for {self.user.email}"

    def is_expired(self):
        """Check if the token has expired"""
        return self.expires_at < timezone.now()

    def is_valid(self):
        """Check if the token is valid (not expired and not used)"""
        return not self.used and not self.is_expired()


class PasswordResetToken(models.Model):
    """
    Token for password reset
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='password_reset_token')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Password reset token for {self.user.email}"

    def is_expired(self):
        """Check if the token has expired"""
        return self.expires_at < timezone.now()

    def is_valid(self):
        """Check if the token is valid (not expired and not used)"""
        return not self.used and not self.is_expired()


class SiteSettings(models.Model):
    """
    Global site settings for the accounts app
    """
    site_name = models.CharField(max_length=100, default='CBC LMS')
    site_description = models.TextField(blank=True)
    contact_email = models.EmailField(default='contact@example.com')
    phone_number = models.CharField(max_length=20, blank=True)
    facebook_url = models.URLField(blank=True)
    whatsapp_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    address = models.TextField(blank=True)
    google_analytics_id = models.CharField(max_length=50, blank=True)
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    terms_of_service = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)
    cookie_policy = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def load(cls):
        """Get or create the singleton instance of SiteSettings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)

    def clean(self):
        """Validate model data"""
        super().clean()
        # Ensure only one instance exists
        if SiteSettings.objects.exclude(pk=self.pk).exists():
            raise ValidationError('Only one SiteSettings instance is allowed.')