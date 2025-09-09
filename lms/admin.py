# lms/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import (
    EducationLevel, Grade, SubjectCategory, Subject, 
    Pathway, ResourceType, Resource
)
import logging

# Get the custom user model
User = get_user_model()

# Set up logging
logger = logging.getLogger(__name__)

# Register your models here
@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'get_grade_count']
    list_filter = ['order']
    search_fields = ['name']
    ordering = ['order', 'name']
    list_per_page = 20
    
    fieldsets = (
        ('Education Level Information', {
            'fields': ('name', 'order', 'description', 'icon')
        }),
    )
    
    def get_grade_count(self, obj):
        count = obj.grades.count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_grade_count.short_description = 'Grades'
    get_grade_count.admin_order_field = 'grades__count'

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'education_level', 'order', 'get_subject_count']
    list_filter = ['education_level', 'order']
    search_fields = ['name', 'education_level__name']
    ordering = ['education_level__order', 'order', 'name']
    list_per_page = 20
    
    fieldsets = (
        ('Grade Information', {
            'fields': ('name', 'education_level', 'order', 'description')
        }),
    )
    
    def get_subject_count(self, obj):
        count = Subject.objects.filter(grades=obj).count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_subject_count.short_description = 'Subjects'
    get_subject_count.admin_order_field = 'subjects__count'

@admin.register(SubjectCategory)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_preview', 'get_subject_count']
    list_filter = []
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 20
    
    fieldsets = (
        ('Subject Category Information', {
            'fields': ('name', 'icon', 'description')
        }),
    )
    
    def get_subject_count(self, obj):
        count = obj.subjects.count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_subject_count.short_description = 'Subjects'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{} text-xl"></i>', obj.icon)
        return format_html('<span style="color: #9CA3AF;">No icon</span>')
    icon_preview.short_description = 'Icon'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'get_grade_count', 'get_resource_count']
    list_filter = ['category']
    search_fields = ['name', 'category__name']
    ordering = ['category__name', 'name']
    list_per_page = 20
    
    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'category', 'description', 'image')
        }),
        ('Grades', {
            'fields': ('grades',)
        }),
    )
    
    filter_horizontal = ('grades',)
    
    def get_grade_count(self, obj):
        count = obj.grades.count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_grade_count.short_description = 'Grades'
    get_grade_count.admin_order_field = 'grades__count'
    
    def get_resource_count(self, obj):
        count = obj.resources.count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_resource_count.short_description = 'Resources'
    get_resource_count.admin_order_field = 'resources__count'

@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ['name', 'grade', 'get_subject_count']
    list_filter = ['grade', 'name']
    search_fields = ['name', 'grade__name']
    ordering = ['grade__education_level__order', 'grade__order', 'name']
    list_per_page = 20
    
    fieldsets = (
        ('Pathway Information', {
            'fields': ('name', 'grade', 'description')
        }),
        ('Subjects', {
            'fields': ('subjects',)
        }),
    )
    
    filter_horizontal = ('subjects',)
    
    def get_subject_count(self, obj):
        count = obj.subjects.count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_subject_count.short_description = 'Subjects'
    get_subject_count.admin_order_field = 'subjects__count'

@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_preview', 'get_resource_count']
    list_filter = []
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 20
    
    fieldsets = (
        ('Resource Type Information', {
            'fields': ('name', 'icon', 'description')
        }),
    )
    
    def get_resource_count(self, obj):
        count = Resource.objects.filter(resource_type=obj).count()
        return format_html('<span style="color: #10B981;">{}</span>', count)
    get_resource_count.short_description = 'Resources'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{} text-xl"></i>', obj.icon)
        return format_html('<span style="color: #9CA3AF;">No icon</span>')
    icon_preview.short_description = 'Icon'

class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'subject', 'resource_type', 'get_file_size', 
        'download_count', 'view_count', 'is_active', 'is_premium', 
        'allow_download', 'uploaded_by', 'upload_date'
    ]
    list_filter = [
        'subject', 'resource_type', 'is_active', 'is_premium', 
        'allow_download', 'upload_date'
    ]
    search_fields = ['title', 'subject__name', 'uploaded_by__username']
    ordering = ['-upload_date']
    list_per_page = 20
    
    fieldsets = (
        ('Resource Information', {
            'fields': ('title', 'description', 'subject', 'resource_type', 'file')
        }),
        ('Access Control', {
            'fields': ('is_active', 'is_premium', 'allow_download')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'upload_date', 'download_count', 'view_count', 'file_size')
        }),
    )
    
    readonly_fields = ['upload_date', 'download_count', 'view_count', 'file_size']
    autocomplete_fields = ['uploaded_by', 'subject']
    
    def get_file_size(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                size = f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                size = f"{obj.file_size / 1024:.1f} KB"
            elif obj.file_size < 1024 * 1024 * 1024:
                size = f"{obj.file_size / (1024 * 1024):.1f} MB"
            else:
                size = f"{obj.file_size / (1024 * 1024 * 1024):.1f} GB"
            return format_html('<span style="color: #6366F1;">{}</span>', size)
        return format_html('<span style="color: #9CA3AF;">No file</span>')
    get_file_size.short_description = 'File Size'
    
    def save_model(self, request, obj, form, change):
        # Update file size when saving
        if obj.file and obj.file.size:
            obj.file_size = obj.file.size
        
        # Log the action
        if change:
            logger.info(f"Resource {obj.id} updated by {request.user.username}")
        else:
            logger.info(f"Resource {obj.id} created by {request.user.username}")
            
        super().save_model(request, obj, form, change)

# Register the Resource model with the custom admin class
admin.site.register(Resource, ResourceAdmin)

# # AdminProfile admin
# @admin.register(AdminProfile)
# class AdminProfileAdmin(admin.ModelAdmin):
#     list_display = ['user', 'admin_level', 'can_manage_users', 'can_manage_content']
#     list_filter = ['admin_level', 'can_manage_users', 'can_manage_content']
#     search_fields = ['user__username', 'user__email']
#     ordering = ['user__username']
    
#     fieldsets = (
#         ('User Information', {
#             'fields': ('user',)
#         }),
#         ('Permissions', {
#             'fields': ('admin_level', 'can_manage_users', 'can_manage_content', 'can_manage_settings')
#         }),
#     )

# Custom admin site header and title
admin.site.site_header = "CBC Curriculum Management"
admin.site.site_title = "CBC Admin Portal"
admin.site.index_title = "Welcome to CBC Curriculum Administration"