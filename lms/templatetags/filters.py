# lms/templatetags/filters.py
from django import template
from django.template.defaultfilters import stringfilter
import os

register = template.Library()

@register.filter
def basename(value):
    """Get the base name of a file path"""
    try:
        return os.path.basename(value)
    except:
        return ''

@register.filter
def filter_by_type(queryset, resource_type_name):
    """Filter a queryset by resource type name"""
    try:
        if not resource_type_name or resource_type_name == 'all':
            return queryset
        return queryset.filter(resource_type__name__iexact=resource_type_name)
    except:
        return queryset

@register.filter
def filter_by_access(queryset, access_type):
    """Filter a queryset by access type (free, premium, downloadable)"""
    try:
        if access_type == 'free':
            return queryset.filter(is_premium=False)
        elif access_type == 'premium':
            return queryset.filter(is_premium=True)
        elif access_type == 'downloadable':
            return queryset.filter(allow_download=True)
        else:
            return queryset
    except:
        return queryset

@register.filter
def filter_by_subject(queryset, subject_id):
    """Filter a queryset by subject ID"""
    try:
        if not subject_id:
            return queryset
        return queryset.filter(subject__id=subject_id)
    except:
        return queryset

@register.filter
def filter_by_grade(queryset, grade_id):
    """Filter a queryset by grade ID"""
    try:
        if not grade_id:
            return queryset
        return queryset.filter(subject__grades__id=grade_id)
    except:
        return queryset

@register.filter
def filter_by_category(queryset, category_id):
    """Filter a queryset by subject category ID"""
    try:
        if not category_id:
            return queryset
        return queryset.filter(subject__category__id=category_id)
    except:
        return queryset

@register.filter
def filter_active(queryset, is_active=True):
    """Filter a queryset by active status"""
    try:
        return queryset.filter(is_active=is_active)
    except:
        return queryset

@register.filter
def search_by_title(queryset, search_term):
    """Filter a queryset by searching in title"""
    try:
        if not search_term:
            return queryset
        return queryset.filter(title__icontains=search_term)
    except:
        return queryset

@register.filter
def get_file_size_display(file_size):
    """Format file size for display"""
    try:
        if file_size < 1024:
            return f"{file_size} B"
        elif file_size < 1024 * 1024:
            return f"{file_size / 1024:.1f} KB"
        elif file_size < 1024 * 1024 * 1024:
            return f"{file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{file_size / (1024 * 1024 * 1024):.1f} GB"
    except:
        return "Unknown"

@register.filter
def get_file_extension(file_name):
    """Get the file extension from a file name"""
    try:
        if not file_name:
            return ''
        return os.path.splitext(file_name)[1].upper().replace('.', '')
    except:
        return ''

@register.filter
def get_resource_count(subject, grade):
    """Get the number of resources for a subject in a specific grade"""
    try:
        return subject.resources.filter(subject__grades=grade, is_active=True).count()
    except:
        return 0

@register.filter
def get_download_button_text(resource, user):
    """Get appropriate download button text based on user status and resource type"""
    try:
        if not resource.allow_download:
            return "View Only"
        if resource.is_premium and not user.is_authenticated:
            return "Login to Download"
        if resource.is_premium and user.is_authenticated:
            return "Premium Download"
        return "Download"
    except:
        return "Download"

@register.filter
def can_view_resource(resource, user):
    """Check if user can view a resource"""
    try:
        # Staff can view all resources
        if user.is_staff:
            return True
        # Non-premium resources can be viewed by anyone
        if not resource.is_premium:
            return True
        # Premium resources require authentication
        return user.is_authenticated
    except:
        return False

@register.filter
def can_download_resource(resource, user):
    """Check if user can download a resource"""
    try:
        # Must allow downloads
        if not resource.allow_download:
            return False
        # Staff can download everything
        if user.is_staff:
            return True
        # Non-premium resources can be downloaded by anyone
        if not resource.is_premium:
            return True
        # Premium resources require authentication
        return user.is_authenticated
    except:
        return False

@register.filter
def get_resource_viewer_type(resource):
    """Get the appropriate viewer type for a resource"""
    try:
        extension = get_file_extension(resource.file.name).lower()
        resource_type_name = resource.resource_type.name.lower()

        # PDF files
        if extension == 'pdf' or resource_type_name == 'pdf':
            return 'pdf'

        # Video files
        video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'webm']
        if extension in video_extensions or resource_type_name == 'video':
            return 'video'

        # Audio files
        audio_extensions = ['mp3', 'wav', 'ogg', 'aac', 'flac']
        if extension in audio_extensions or resource_type_name == 'audio':
            return 'audio'

        # Image files
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg']
        if extension in image_extensions or resource_type_name == 'image':
            return 'image'

        # Document files
        doc_extensions = ['doc', 'docx', 'txt', 'rtf']
        if extension in doc_extensions or resource_type_name == 'document':
            return 'document'

        # Spreadsheet files
        spreadsheet_extensions = ['xls', 'xlsx', 'csv']
        if extension in spreadsheet_extensions or resource_type_name == 'spreadsheet':
            return 'spreadsheet'

        # Presentation files
        presentation_extensions = ['ppt', 'pptx']
        if extension in presentation_extensions or resource_type_name == 'presentation':
            return 'presentation'

        # Default to generic viewer
        return 'generic'

    except:
        return 'generic'

@register.filter
def get_subject_by_education_level(subjects, education_level_id):
    """Get subjects for a specific education level"""
    try:
        if not education_level_id:
            return subjects
        return subjects.filter(grades__education_level__id=education_level_id).distinct()
    except:
        return subjects.none()

@register.filter
def get_grade_by_education_level(grades, education_level_id):
    """Get grades for a specific education level"""
    try:
        if not education_level_id:
            return grades
        return grades.filter(education_level__id=education_level_id)
    except:
        return grades.none()

@register.filter
def get_resource_by_education_level(resources, education_level_id):
    """Get resources for a specific education level"""
    try:
        if not education_level_id:
            return resources
        return resources.filter(subject__grades__education_level__id=education_level_id).distinct()
    except:
        return resources.none()

@register.filter
def get_active_resources_count(resources):
    """Get count of active resources"""
    try:
        return resources.filter(is_active=True).count()
    except:
        return 0

@register.filter
def get_premium_resources_count(resources):
    """Get count of premium resources"""
    try:
        return resources.filter(is_premium=True, is_active=True).count()
    except:
        return 0

@register.filter
def get_downloadable_resources_count(resources):
    """Get count of downloadable resources"""
    try:
        return resources.filter(allow_download=True, is_active=True).count()
    except:
        return 0

@register.filter
def get_free_resources_count(resources):
    """Get count of free resources"""
    try:
        return resources.filter(is_premium=False, is_active=True).count()
    except:
        return 0

@register.filter
def sort_by_popularity(queryset):
    """Sort queryset by download count (popularity)"""
    try:
        return queryset.order_by('-download_count')
    except:
        return queryset

@register.filter
def sort_by_date(queryset):
    """Sort queryset by upload date"""
    try:
        return queryset.order_by('-upload_date')
    except:
        return queryset

@register.filter
def sort_by_title(queryset):
    """Sort queryset by title"""
    try:
        return queryset.order_by('title')
    except:
        return queryset

@register.filter
def limit(queryset, num):
    """Limit queryset to N items"""
    try:
        return queryset[:int(num)]
    except:
        return queryset

@register.filter
def get_recent_resources(resources, days=30):
    """Get resources uploaded in the last N days"""
    try:
        from datetime import datetime, timedelta
        time_threshold = datetime.now() - timedelta(days=days)
        return resources.filter(upload_date__gte=time_threshold)
    except:
        return resources.none()

@register.filter
def get_resource_badge(resource):
    """Get appropriate badge for resource based on type and access"""
    try:
        badge = {
            'text': '',
            'color': 'gray',
            'icon': 'fas fa-file'
        }

        # Set icon based on resource type
        if resource.resource_type.name.lower() == 'pdf':
            badge['icon'] = 'fas fa-file-pdf'
            badge['color'] = 'red'
        elif resource.resource_type.name.lower() == 'video':
            badge['icon'] = 'fas fa-file-video'
            badge['color'] = 'blue'
        elif resource.resource_type.name.lower() == 'audio':
            badge['icon'] = 'fas fa-file-audio'
            badge['color'] = 'purple'
        elif resource.resource_type.name.lower() == 'image':
            badge['icon'] = 'fas fa-file-image'
            badge['color'] = 'green'
        else:
            badge['icon'] = 'fas fa-file'
            badge['color'] = 'gray'

        # Add premium indicator
        if resource.is_premium:
            badge['text'] = 'Premium'
            badge['color'] = 'yellow'

        return badge
    except:
        return {'text': 'Unknown', 'color': 'gray', 'icon': 'fas fa-file'}

@register.filter
def get_access_status(resource, user):
    """Get access status text for a resource"""
    try:
        if resource.is_premium:
            if user.is_authenticated:
                return "Premium Access - Download Available"
            else:
                return "Premium Access - Login Required"
        else:
            if resource.allow_download:
                return "Free Access - Download Available"
            else:
                return "Free Access - View Only"
    except:
        return "Access Unknown"

@register.filter
def get_pre_primary_count(education_levels):
    """Count the number of Pre-Primary grades"""
    try:
        pre_primary_level = education_levels.filter(name='Pre-Primary').first()
        if pre_primary_level:
            return pre_primary_level.grades.count()
        return 0
    except:
        return 0

@register.filter
def get_level_count(education_levels, level_name):
    """Count the number of grades for a specific education level"""
    try:
        level = education_levels.filter(name=level_name).first()
        if level:
            return level.grades.count()
        return 0
    except:
        return 0