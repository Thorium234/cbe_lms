# accounts/middleware.py
from django.utils import timezone
from .models import UserActivity, SiteSettings

class UserActivityMiddleware:
    """Middleware to track user activity"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.user.is_authenticated:
            # Update last activity
            request.user.last_activity = timezone.now()
            request.user.save(update_fields=['last_activity'])
            
            # Log activity for certain actions
            if request.path.startswith('/accounts/') or request.path.startswith('/lms/'):
                UserActivity.objects.create(
                    user=request.user,
                    action=f'VISIT_{request.path.strip("/").upper()}',
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SiteSettingsMiddleware:
    """Middleware to make site settings available in all templates"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data'):
            if response.context_data is None:
                response.context_data = {}
            response.context_data['site_settings'] = SiteSettings.load()
        return response