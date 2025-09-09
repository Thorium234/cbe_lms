# lms/models.py
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os

class EducationLevel(models.Model):
    """
    Represents the main education levels like Pre-Primary, Lower Primary, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-graduation-cap')
    
    class Meta:
        verbose_name = 'Education Level'
        verbose_name_plural = 'Education Levels'
        ordering = ['order']
    
    def __str__(self):
        return self.name

class Grade(models.Model):
    """
    Represents individual grades within an education level.
    Examples: PP1, PP2, G1, G2, G10, G11, G12, etc.
    """
    name = models.CharField(max_length=100)
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='grades')
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Grade'
        verbose_name_plural = 'Grades'
        unique_together = ['name', 'education_level']
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} ({self.education_level.name})"

class SubjectCategory(models.Model):
    """
    Represents categories of subjects that group related subjects together.
    Examples: Languages, Mathematics, Science, etc.
    """
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='fas fa-book')
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Subject Category'
        verbose_name_plural = 'Subject Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    """
    Represents individual subjects.
    Examples: Mathematics, English, Biology, etc.
    """
    name = models.CharField(max_length=100)
    category = models.ForeignKey(SubjectCategory, on_delete=models.CASCADE, related_name='subjects')
    grades = models.ManyToManyField(Grade, related_name='subjects')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='subject_images/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        unique_together = ['name', 'category']
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Pathway(models.Model):
    """
    Represents educational pathways in Senior Secondary (STEM, Social Sciences, Arts & Sports).
    """
    name = models.CharField(max_length=100)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='pathways')
    subjects = models.ManyToManyField(Subject, related_name='pathways')
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Pathway'
        verbose_name_plural = 'Pathways'
        unique_together = ['name', 'grade']
    
    def __str__(self):
        return f"{self.name} ({self.grade.name})"

class ResourceType(models.Model):
    """
    Represents types of resources (PDF, Video, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=50, default='fas fa-file')
    description = models.TextField()
    
    class Meta:
        verbose_name = 'Resource Type'
        verbose_name_plural = 'Resource Types'
        ordering = ['name']
    
    def __str__(self):
        return self.name

def resource_file_path(instance, filename):
    """Generate file path for a resource file based on education level and grade"""
    # Get the education level name and replace spaces with underscores
    level_name = instance.subject.grades.first().education_level.name.replace(' ', '_').lower()
    
    # Get the grade name and replace spaces with underscores
    grade_name = instance.subject.grades.first().name.replace(' ', '_').lower()
    
    # Get the resource type and replace spaces with underscores
    resource_type = instance.resource_type.name.lower().replace(' ', '_')
    
    # Create the path: media/education_level/grade/resource_type/filename
    return f'{level_name}/{grade_name}/{resource_type}/{filename}'

class Resource(models.Model):
    """
    Represents educational resources uploaded to the system.
    """
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='resources')
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=resource_file_path,
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'mp3', 'wav'
        ])]
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    allow_download = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    file_size = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        ordering = ['-upload_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file and self.file.size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1][1:].upper()