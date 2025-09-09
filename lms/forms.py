from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import EducationLevel, Grade, SubjectCategory, Subject, ResourceType, Resource, Pathway
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)





class ResourceUploadForm(forms.ModelForm):
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        empty_label="Select a grade",
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300'
        })
    )

    class Meta:
        model = Resource
        fields = ['title', 'subject', 'resource_type', 'file', 'description', 'allow_download', 'is_premium']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300',
                'placeholder': 'Enter resource title'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300'
            }),
            'resource_type': forms.Select(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300 hidden'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-300',
                'placeholder': 'Describe the resource content, learning objectives, etc.',
                'rows': 5
            }),
            'allow_download': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
            }),
            'is_premium': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        grade = cleaned_data.get('grade')

        if subject and grade:
            if not subject.grades.filter(id=grade.id).exists():
                raise ValidationError(
                    "The selected subject does not belong to the selected grade."
                )

        if not subject:
            raise ValidationError("A subject is required to upload/edit a resource.")

        if not grade:
            raise ValidationError("A grade is required to upload/edit a resource.")

        return cleaned_data


class SubjectCategoryForm(forms.ModelForm):
    """Form for creating/editing subject categories"""
    class Meta:
        model = SubjectCategory
        fields = ['name', 'icon', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Category name (e.g., Languages, Mathematics)',
                'required': 'required'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Font Awesome icon class (e.g., fas fa-language)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Brief description of this category'
            })
        }

class GradeForm(forms.ModelForm):
    """Form for creating/editing grades"""
    class Meta:
        model = Grade
        fields = ['name', 'education_level', 'order', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Grade name (e.g., Grade 1, PP1)',
                'required': 'required'
            }),
            'education_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': 'required'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': '1',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Description of this grade level'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['education_level'].queryset = EducationLevel.objects.all().order_by('order')
        self.fields['education_level'].empty_label = "Select an education level"
        if not self.fields['education_level'].queryset.exists():
            raise forms.ValidationError("No education levels are available. Please contact an administrator.")

class SubjectForm(forms.ModelForm):
    """Form for creating/editing subjects"""
    class Meta:
        model = Subject
        fields = ['name', 'category', 'grades', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Subject name (e.g., English, Mathematics)',
                'required': 'required'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': 'required'
            }),
            'grades': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Brief description of this subject'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = SubjectCategory.objects.all().order_by('name')
        self.fields['category'].empty_label = "Select a category"
        self.fields['grades'].queryset = Grade.objects.all().order_by('order')
        self.fields['grades'].empty_label = None  # Multiple select doesn't need empty label
        if not self.fields['category'].queryset.exists():
            raise forms.ValidationError("No subject categories are available. Please contact an administrator.")
        if not self.fields['grades'].queryset.exists():
            raise forms.ValidationError("No grades are available. Please contact an administrator.")

class ResourceTypeForm(forms.ModelForm):
    """Form for creating/editing resource types"""
    class Meta:
        model = ResourceType
        fields = ['name', 'icon', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Resource type name (e.g., PDF, Video)',
                'required': 'required'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Font Awesome icon class (e.g., fas fa-file-pdf)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Description of this resource type'
            })
        }

class EducationLevelForm(forms.ModelForm):
    """Form for creating/editing education levels"""
    class Meta:
        model = EducationLevel
        fields = ['name', 'order', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Education level name (e.g., Pre-Primary, Lower Primary)',
                'required': 'required'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'min': '1',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Description of this education level'
            })
        }

class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with email field"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter a valid email address'
        }),
        help_text='Required. Enter a valid email address.'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter a username'
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter password'
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Confirm password'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = 'Your password must contain at least 8 characters and cannot be entirely numeric.'
        self.fields['password2'].help_text = 'Enter the same password as before, for verification.'

class PathwayForm(forms.ModelForm):
    """Form for creating/editing pathways"""
    class Meta:
        model = Pathway
        fields = ['name', 'grade', 'subjects', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Pathway name (e.g., STEM, Arts)',
                'required': 'required'
            }),
            'grade': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': 'required'
            }),
            'subjects': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Brief description of this pathway'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['grade'].queryset = Grade.objects.all().order_by('order')
        self.fields['grade'].empty_label = "Select a grade"
        self.fields['subjects'].queryset = Subject.objects.all().order_by('name')
        self.fields['subjects'].empty_label = None  # Multiple select doesn't need empty label
        if not self.fields['grade'].queryset.exists():
            raise forms.ValidationError("No grades are available. Please contact an administrator.")
        if not self.fields['subjects'].queryset.exists():
            raise forms.ValidationError("No subjects are available. Please contact an administrator.")
