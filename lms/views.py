import os
import logging
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError



from .forms import ResourceUploadForm

import logging



# Use absolute imports
from .models import (
    EducationLevel,
    Grade,
    Subject,
    SubjectCategory,
    Resource,
    ResourceType,
    Pathway
)
from .forms import (
    ResourceUploadForm,
    SubjectCategoryForm,
    GradeForm,
    SubjectForm,
    EducationLevelForm,
    PathwayForm,
    ResourceTypeForm,
    CustomUserCreationForm
)

logger = logging.getLogger(__name__)



def is_admin(user):
    """Check if user is an admin"""
    return user.is_staff

def page_not_found(request, exception):
    """Custom 404 page"""
    return render(request, 'lms/404.html', status=404)

def server_error(request):
    """Custom 500 page"""
    return render(request, 'lms/500.html', status=500)

def error(request):
    """Generic error page"""
    return render(request, 'lms/error.html', {'message': 'An unexpected error occurred.'})

def loading_page(request):
    """Display loading page with optional redirect"""
    redirect_url = request.GET.get('next', '')
    return render(request, 'lms/loading.html', {'redirect_url': redirect_url})

def success_page(request, content_type=None, content_id=None):
    """Display success page with context-specific message"""
    messages_dict = {
        'resource': {
            'title': 'Resource Uploaded Successfully!',
            'message': 'Your resource has been successfully uploaded and is now available to users.',
            'icon': 'document'
        },
        'delete': {
            'title': 'Content Deleted Successfully!',
            'message': 'The selected content has been permanently removed from the system.',
            'icon': 'trash'
        },
        'update': {
            'title': 'Content Updated Successfully!',
            'message': 'Your changes have been saved successfully.',
            'icon': 'edit'
        },
        'signup': {
            'title': 'Account Created Successfully!',
            'message': 'Welcome to our platform! You can now access all resources.',
            'icon': 'user'
        },
        'login': {
            'title': 'Logged In Successfully!',
            'message': 'Welcome back! You are now logged in to your account.',
            'icon': 'login'
        },
        'logout': {
            'title': 'Logged Out Successfully!',
            'message': 'You have been logged out successfully. See you next time!',
            'icon': 'logout'
        }
    }

    message_data = {
        'title': 'Operation Completed!',
        'message': 'Your request has been processed successfully.',
        'icon': 'check'
    }

    if content_type in messages_dict:
        message_data = messages_dict[content_type]
    elif content_type:
        message_data['title'] = f'{content_type.replace("_", " ").title()} Successful!'

    return render(request, 'lms/success.html', {
        'message_data': message_data,
        'content_type': content_type,
        'content_id': content_id
    })

def summary(request):
    """Home page displaying all education levels"""
    try:
        education_levels = EducationLevel.objects.prefetch_related('grades').all().order_by('order')
        total_grades = Grade.objects.count()
        total_subjects = Subject.objects.count()
        total_resources = Resource.objects.filter(is_active=True).count()
        featured_resources = Resource.objects.filter(
            is_active=True
        ).select_related('subject', 'subject__category').order_by('-download_count', '-upload_date')[:6]

        context = {
            'education_levels': education_levels,
            'total_grades': total_grades,
            'total_subjects': total_subjects,
            'total_resources': total_resources,
            'featured_resources': featured_resources,
        }

        return render(request, 'lms/summary.html', context)
    except Exception as e:
        logger.error(f"Error loading summary page: {str(e)}")
        messages.error(request, 'An error occurred while loading the page. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load summary page.'})

def grade_level_dashboard(request):
    """Display all education levels as the main landing page"""
    try:
        education_levels = EducationLevel.objects.prefetch_related('grades').all().order_by('order')
        total_grades = Grade.objects.count()
        total_subjects = Subject.objects.count()
        total_resources = Resource.objects.filter(is_active=True).count()
        featured_resources = Resource.objects.filter(
            is_active=True
        ).select_related('subject', 'subject__category').order_by('-download_count', '-upload_date')[:8]

        context = {
            'education_levels': education_levels,
            'total_grades': total_grades,
            'total_subjects': total_subjects,
            'total_resources': total_resources,
            'featured_resources': featured_resources,
        }

        return render(request, 'lms/grade_level_dashboard.html', context)
    except Exception as e:
        logger.error(f"Error loading grade level dashboard: {str(e)}")
        messages.error(request, 'An error occurred while loading the grade levels. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load grade levels.'})

@login_required
@user_passes_test(is_admin)
def superuser_dashboard(request):
    """Superuser dashboard for managing content"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to superuser dashboard by {request.user.username}")
        return render(request, 'lms/access_denied.html', status=403)

    education_levels = EducationLevel.objects.all().order_by('order')
    grades = Grade.objects.select_related('education_level').all().order_by('education_level__order', 'order')
    categories = SubjectCategory.objects.all().order_by('name')
    subjects = Subject.objects.select_related('category').prefetch_related('grades').all().order_by('category__name', 'name')
    resource_types = ResourceType.objects.all().order_by('name')
    resources = Resource.objects.select_related('subject', 'resource_type', 'uploaded_by').all().order_by('-upload_date')
    pathways = Pathway.objects.select_related('grade').all().order_by('name')

    context = {
        'education_levels': education_levels,
        'grades': grades,
        'categories': categories,
        'subjects': subjects,
        'resource_types': resource_types,
        'resources': resources,
        'pathways': pathways,
    }

    return render(request, 'lms/superuser_dashboard.html', context)


def education_level_dashboard(request, level_id):
    """Display grades for a specific education level"""
    try:
        logger.debug(f"Loading education level with ID {level_id}")
        education_level = get_object_or_404(EducationLevel, id=level_id)
        logger.debug(f"Found education level: {education_level.name}")

        grades = Grade.objects.filter(education_level=education_level).order_by('order')
        logger.debug(f"Found {grades.count()} grades")
        if not grades:
            logger.warning(f"No grades found for education level {level_id}")
            messages.warning(request, "No grades available for this education level.")

        subjects_count = Subject.objects.filter(grades__in=grades).distinct().count()
        resources_count = Resource.objects.filter(subject__grades__in=grades, is_active=True).distinct().count()
        average_subjects_per_grade = subjects_count / grades.count() if grades.count() > 0 else 0

        context = {
            'education_level': education_level,
            'grades': grades,
            'subjects_count': subjects_count,
            'resources_count': resources_count,
            'average_subjects_per_grade': average_subjects_per_grade,
        }
        template = 'lms/senior_grade_dashboard.html' if education_level.name == 'Senior Secondary' else 'lms/grade_dashboard.html'
        logger.debug(f"Rendering {template}")
        return render(request, template, context)
    except Http404:
        logger.error(f"Education level {level_id} not found")
        messages.error(request, "Education level not found.")
        return render(request, 'lms/error.html', {'message': 'Education level not found.'})
    except Exception as e:
        logger.error(f"Error loading education level {level_id}: {str(e)}")
        messages.error(request, 'An error occurred while loading the education level. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load education level.'})

def grade_pathways_dashboard(request, grade_id):
    """Display pathways for a specific grade"""
    try:
        logger.debug(f"Loading pathways for grade ID {grade_id}")
        grade = get_object_or_404(Grade, id=grade_id)
        logger.debug(f"Found grade: {grade.name}")
        pathways = Pathway.objects.filter(grade=grade).distinct()
        logger.debug(f"Found {pathways.count()} pathways")

        context = {
            'grade': grade,
            'education_level': grade.education_level,
            'pathways': pathways,
        }
        logger.debug("Rendering pathways_dashboard.html")
        return render(request, 'lms/pathways_dashboard.html', context)
    except Http404:
        logger.error(f"Grade {grade_id} not found")
        messages.error(request, "Grade not found.")
        return render(request, 'lms/error.html', {'message': 'Grade not found.'})
    except Exception as e:
        logger.error(f"Error loading pathways for grade {grade_id}: {str(e)}")
        messages.error(request, 'An error occurred while loading pathways. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load pathways.'})



def pathways_dashboard(request, level_id):
    """Display pathways for Senior Secondary"""
    education_level = get_object_or_404(EducationLevel, id=level_id)
    pathways = Pathway.objects.filter(grade__education_level=education_level).distinct()
    context = {
        'education_level': education_level,
        'pathways': pathways,
    }
    return render(request, 'lms/pathways_dashboard.html', context)

def pathway_subjects(request, pathway_id):
    """Display subjects for a specific pathway"""
    pathway = get_object_or_404(Pathway, id=pathway_id)
    subjects = pathway.subjects.all().order_by('name')
    # Use the first grade in senior secondary for subject dashboard links
    senior_grade = Grade.objects.filter(education_level__name='Senior Secondary').first()
    context = {
        'pathway': pathway,
        'subjects': subjects,
        'grade': senior_grade,
    }
    return render(request, 'lms/pathway_subjects.html', context)



def grade_dashboard(request, grade_id):
    """Display subjects for a specific grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        subjects = Subject.objects.filter(grades=grade).select_related('category')
        pathways = Pathway.objects.filter(grade=grade).prefetch_related('subjects') if grade.education_level.name == 'Senior Secondary' else []
        has_pathways = len(pathways) > 0

        categories = {}
        for subject in subjects:
            category_name = subject.category.name
            if category_name not in categories:
                categories[category_name] = []
            categories[category_name].append(subject)

        context = {
            'grade': grade,
            'categories': categories,
            'has_pathways': has_pathways,
            'pathways': pathways,
        }

        return render(request, 'lms/grade_dashboard.html', context)
    except Http404:
        messages.error(request, "Grade not found.")
        return render(request, 'lms/error.html', {'message': 'Grade not found.'})
    except Exception as e:
        logger.error(f"Error loading grade {grade_id}: {str(e)}")
        messages.error(request, 'An error occurred while loading the grade. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load grade.'})

def subject_dashboard(request, grade_id, subject_id):
    """Display resources for a specific subject and grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        subject = get_object_or_404(Subject, id=subject_id)

        # Ensure subject is associated with the grade
        if not subject.grades.filter(id=grade_id).exists():
            messages.error(request, f"The subject {subject.name} is not associated with {grade.name}.")
            return redirect('lms:grade_dashboard', grade_id=grade_id)

        # Filter resources by subject, grade, and is_active
        resources = Resource.objects.filter(
            subject=subject,
            subject__grades=grade,  # Ensure resources are linked to the grade
            is_active=True
        ).select_related('resource_type', 'uploaded_by').order_by('-download_count', '-upload_date')

        # Group resources by type for template
        resource_types = {}
        for resource in resources:
            type_name = resource.resource_type.name
            if type_name not in resource_types:
                resource_types[type_name] = []
            resource_types[type_name].append(resource)

        # Get all resource types for filter buttons
        all_resource_types = ResourceType.objects.all()

        # Get new_resource_id for highlighting
        new_resource_id = request.GET.get('new_resource_id')
        new_resource = None
        if new_resource_id:
            try:
                new_resource = Resource.objects.get(id=new_resource_id, subject=subject, subject__grades=grade, is_active=True)
            except Resource.DoesNotExist:
                logger.warning(f"New resource ID {new_resource_id} not found or invalid for subject {subject_id}, grade {grade_id}")

        paginator = Paginator(resources, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'grade': grade,
            'subject': subject,
            'page_obj': page_obj,
            'new_resource_id': new_resource_id if new_resource else None,
            'resource_types': resource_types,
            'all_resource_types': all_resource_types,
            'selected_type': request.GET.get('type', ''),
        }

        return render(request, 'lms/subject_dashboard.html', context)
    except Http404:
        messages.error(request, "Subject or grade not found.")
        return render(request, 'lms/error.html', {'message': 'Subject or grade not found.'})
    except Exception as e:
        logger.error(f"Error loading subject {subject_id} for grade {grade_id}: {str(e)}")
        messages.error(request, 'An error occurred while loading the subject. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load subject.'}, status=500)


def view_resource(request, resource_id):
    """View resource details"""
    try:
        resource = get_object_or_404(Resource, id=resource_id, is_active=True)
        resource.view_count += 1
        resource.save(update_fields=['view_count'])

        # Determine viewer type based on file extension
        file_extension = os.path.splitext(resource.file.name)[1].lower()
        viewer_type = None
        file_url = resource.file.url

        if file_extension == '.pdf':
            viewer_type = 'pdf'
        elif file_extension in ['.mp4', '.webm', '.ogg', '.mov']:
            viewer_type = 'video'
        elif file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
            viewer_type = 'image'
        elif file_extension in ['.mp3', '.wav', '.ogg']:
            viewer_type = 'audio'
        elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            viewer_type = 'document'
        else:
            viewer_type = 'other'

        # Check if user can download
        can_download = resource.allow_download and (not resource.is_premium or request.user.is_authenticated)

        context = {
            'resource': resource,
            'viewer_type': viewer_type,
            'file_url': file_url,
            'can_download': can_download,
        }

        logger.debug(f"Rendering resource {resource_id}: viewer_type={viewer_type}, file_url={file_url}")

        return render(request, 'lms/view_resource.html', context)

    except Http404:
        logger.error(f"Resource {resource_id} not found")
        messages.error(request, "Resource not found.")
        return render(request, 'lms/error.html', {'message': 'Resource not found.'})
    except Exception as e:
        logger.error(f"Error viewing resource {resource_id}: {str(e)}")
        messages.error(request, 'An error occurred while viewing the resource.')
        return render(request, 'lms/error.html', {'message': 'Failed to view resource.'})


def download_resource(request, resource_id):
    """Download a resource file"""
    try:
        resource = get_object_or_404(Resource, id=resource_id, is_active=True)
        resource.download_count += 1
        resource.save(update_fields=['download_count'])

        logger.info(f"Resource {resource_id} downloaded by {request.user.username if request.user.is_authenticated else 'anonymous'}")
        file_path = resource.file.path
        if os.path.exists(file_path):
            response = FileResponse(
                open(file_path, 'rb'),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{resource.filename}"'
            return response
        else:
            messages.error(request, "Resource file not found.")
            return render(request, 'lms/error.html', {'message': 'Resource file not found.'})

    except Http404:
        messages.error(request, "Resource not found.")
        return render(request, 'lms/error.html', {'message': 'Resource not found.'})
    except Exception as e:
        logger.error(f"Error downloading resource {resource_id}: {str(e)}")
        messages.error(request, 'An error occurred while downloading the resource.')
        return render(request, 'lms/error.html', {'message': 'Failed to download resource.'})




@login_required
@user_passes_test(is_admin)
def upload_resource(request):
    """Upload a new resource with preselected grade and subject"""
    grade = None
    subject = None
    grade_id = request.GET.get('grade_id')
    subject_id = request.GET.get('subject_id')

    logger.debug(f"Upload resource request: grade_id={grade_id}, subject_id={subject_id}")

    # Validate grade and subject if provided
    if grade_id:
        try:
            grade = get_object_or_404(Grade, id=grade_id)
        except Http404:
            logger.error(f"Invalid grade_id {grade_id}")
            messages.error(request, "Invalid grade selected.")
            return redirect('lms:grade_level_dashboard')

    if subject_id:
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            # Ensure subject belongs to the grade if both are provided
            if grade and not subject.grades.filter(id=grade.id).exists():
                logger.error(f"Subject {subject_id} does not belong to grade {grade_id}")
                messages.error(request, "Selected subject does not belong to the grade.")
                return redirect('lms:grade_level_dashboard')
        except Http404:
            logger.error(f"Invalid subject_id {subject_id}")
            messages.error(request, "Invalid subject selected.")
            return redirect('lms:grade_level_dashboard')

    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES, initial={'subject': subject, 'grade': grade})
        if form.is_valid():
            try:
                resource = form.save(commit=False)
                resource.uploaded_by = request.user
                resource.file_size = request.FILES['file'].size if request.FILES.get('file') else resource.file_size
                resource.save()

                # Use the grade from the form for the redirect
                form_grade = form.cleaned_data['grade']
                logger.info(f"Resource {resource.id} uploaded by {request.user.username} for subject {resource.subject.id}, grade {form_grade.id}")
                messages.success(request, f'Resource "{resource.title}" uploaded successfully!')
                next_url = f"/subject/{form_grade.id}/{resource.subject.id}/?new_resource_id={resource.id}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f"/loading/?next={next_url}"
                    })
                return redirect(f"/loading/?next={next_url}")

            except ValidationError as e:
                logger.error(f"Validation error uploading resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f"Validation error: {str(e)}"}, status=400)
                messages.error(request, f"Validation error: {str(e)}")
                return render(request, 'lms/upload_resource.html', {'form': form, 'grade': grade, 'subject': subject})
            except Exception as e:
                logger.error(f"Unexpected error uploading resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again.'}, status=500)
                messages.error(request, "An unexpected error occurred. Please try again.")
                return render(request, 'lms/error.html', {'message': 'Failed to upload resource.'}, status=500)
        else:
            logger.error(f"Form validation failed: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Please correct the errors below.', 'errors': form.errors.as_json()}, status=400)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceUploadForm(initial={'subject': subject, 'grade': grade} if subject or grade else {})

    context = {
        'form': form,
        'grade': grade,
        'subject': subject,
    }
    return render(request, 'lms/upload_resource.html', context)
# @login_required
# @user_passes_test(is_admin)
# def upload_resource(request):
#     """Upload a new resource"""
#     try:
#         if request.method == 'POST':
#             title = request.POST.get('title')
#             description = request.POST.get('description')
#             file = request.FILES.get('file')
#             subject_id = request.POST.get('subject_id')
#             grade_id = request.POST.get('grade_id')
#             resource_type_id = request.POST.get('resource_type_id')
#             allow_download = request.POST.get('allow_download') == 'on'
#             is_premium = request.POST.get('is_premium') == 'on'

#             subject = get_object_or_404(Subject, id=subject_id)
#             grade = get_object_or_404(Grade, id=grade_id)
#             resource_type = get_object_or_404(ResourceType, id=resource_type_id)

#             resource = Resource.objects.create(
#                 title=title,
#                 description=description,
#                 file=file,
#                 subject=subject,
#                 resource_type=resource_type,
#                 uploaded_by=request.user,
#                 is_active=True,
#                 allow_download=allow_download,
#                 is_premium=is_premium,
#                 file_size=file.size if file else 0
#             )

#             # Add grade to resource
#             resource.grades.add(grade)

#             logger.debug(f"Resource {resource.id} uploaded successfully for subject {subject_id}, grade {grade_id}")

#             # Redirect to loading page with next_url set to subject dashboard
#             next_url = reverse('lms:subject_dashboard', kwargs={'grade_id': grade_id, 'subject_id': subject_id})
#             return render(request, 'lms/loading.html', {'next_url': next_url})

#         # GET request: render upload form
#         subjects = Subject.objects.all()
#         grades = Grade.objects.all()
#         resource_types = ResourceType.objects.all()
#         context = {
#             'subjects': subjects,
#             'grades': grades,
#             'resource_types': resource_types,
#             'grade_id': request.GET.get('grade_id'),
#             'subject_id': request.GET.get('subject_id'),
#         }
#         return render(request, 'lms/upload_resource.html', context)

#     except Exception as e:
#         logger.error(f"Error uploading resource: {str(e)}")
#         messages.error(request, 'An error occurred while uploading the resource.')
#         return render(request, 'lms/error.html', {'message': 'Failed to upload resource.'})



@login_required
@user_passes_test(is_admin)
def edit_resource(request, resource_id=None):
    """Edit an existing resource"""
    # Get resource_id from path parameter or query parameter
    resource_id = resource_id or request.GET.get('resource_id')
    if not resource_id:
        logger.error("No resource_id provided")
        messages.error(request, "No resource specified for editing.")
        return redirect('lms:grade_level_dashboard')

    resource = get_object_or_404(Resource, id=resource_id)
    grade_id = request.GET.get('grade_id')
    subject_id = request.GET.get('subject_id')
    grade = None
    subject = None

    logger.debug(f"Edit resource request: resource_id={resource_id}, grade_id={grade_id}, subject_id={subject_id}")

    # Validate grade and subject if provided
    if grade_id:
        try:
            grade = get_object_or_404(Grade, id=grade_id)
        except Http404:
            logger.error(f"Invalid grade_id {grade_id}")
            messages.error(request, "Invalid grade selected.")
            return redirect('lms:grade_level_dashboard')

    if subject_id:
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            # Ensure subject belongs to the grade if both are provided
            if grade and not subject.grades.filter(id=grade.id).exists():
                logger.error(f"Subject {subject_id} does not belong to grade {grade_id}")
                messages.error(request, "Selected subject does not belong to the grade.")
                return redirect('lms:grade_level_dashboard')
        except Http404:
            logger.error(f"Invalid subject_id {subject_id}")
            messages.error(request, "Invalid subject selected.")
            return redirect('lms:grade_level_dashboard')

    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES, instance=resource, initial={'subject': subject or resource.subject, 'grade': grade})
        if form.is_valid():
            try:
                resource = form.save(commit=False)
                # Update file_size only if a new file is uploaded
                if request.FILES.get('file'):
                    resource.file_size = request.FILES['file'].size
                resource.uploaded_by = request.user
                resource.save()

                form_grade = form.cleaned_data['grade']
                logger.info(f"Resource {resource.id} edited by {request.user.username} for subject {resource.subject.id}, grade {form_grade.id}")
                messages.success(request, f'Resource "{resource.title}" updated successfully!')
                next_url = f"/subject/{form_grade.id}/{resource.subject.id}/?resource_id={resource.id}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f"/loading/?next={next_url}"
                    })
                return redirect(f"/loading/?next={next_url}")

            except ValidationError as e:
                logger.error(f"Validation error editing resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f"Validation error: {str(e)}"}, status=400)
                messages.error(request, f"Validation error: {str(e)}")
                return render(request, 'lms/edit_resource.html', {'form': form, 'grade': grade, 'subject': subject, 'resource': resource})
            except Exception as e:
                logger.error(f"Unexpected error editing resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again.'}, status=500)
                messages.error(request, "An unexpected error occurred. Please try again.")
                return render(request, 'lms/error.html', {'message': 'Failed to edit resource.'}, status=500)
        else:
            logger.error(f"Form validation failed: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Please correct the errors below.', 'errors': form.errors.as_json()}, status=400)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceUploadForm(instance=resource, initial={'subject': subject or resource.subject, 'grade': grade})

    context = {
        'form': form,
        'grade': grade,
        'subject': subject,
        'resource': resource,
    }
    return render(request, 'lms/edit_resource.html', context)





@login_required
@user_passes_test(is_admin)
def edit_resource(request):
    """Edit an existing resource"""
    resource_id = request.GET.get('resource_id')
    resource = get_object_or_404(Resource, id=resource_id)
    grade_id = request.GET.get('grade_id')
    subject_id = request.GET.get('subject_id')
    grade = None
    subject = None

    logger.debug(f"Edit resource request: resource_id={resource_id}, grade_id={grade_id}, subject_id={subject_id}")

    # Validate grade and subject if provided
    if grade_id:
        try:
            grade = get_object_or_404(Grade, id=grade_id)
        except Http404:
            logger.error(f"Invalid grade_id {grade_id}")
            messages.error(request, "Invalid grade selected.")
            return redirect('lms:grade_level_dashboard')

    if subject_id:
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            # Ensure subject belongs to the grade if both are provided
            if grade and not subject.grades.filter(id=grade.id).exists():
                logger.error(f"Subject {subject_id} does not belong to grade {grade_id}")
                messages.error(request, "Selected subject does not belong to the grade.")
                return redirect('lms:grade_level_dashboard')
        except Http404:
            logger.error(f"Invalid subject_id {subject_id}")
            messages.error(request, "Invalid subject selected.")
            return redirect('lms:grade_level_dashboard')

    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES, instance=resource, initial={'subject': subject or resource.subject, 'grade': grade})
        if form.is_valid():
            try:
                resource = form.save(commit=False)
                # Update filename and file_size only if a new file is uploaded
                if request.FILES.get('file'):
                    resource.filename = request.FILES['file'].name
                    resource.file_size = request.FILES['file'].size
                resource.uploaded_by = request.user
                resource.save()

                form_grade = form.cleaned_data['grade']
                logger.info(f"Resource {resource.id} edited by {request.user.username} for subject {resource.subject.id}, grade {form_grade.id}")
                messages.success(request, f'Resource "{resource.title}" updated successfully!')
                next_url = f"/subject/{form_grade.id}/{resource.subject.id}/?resource_id={resource.id}"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': f"/loading/?next={next_url}"
                    })
                return redirect(f"/loading/?next={next_url}")

            except ValidationError as e:
                logger.error(f"Validation error editing resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': f"Validation error: {str(e)}"}, status=400)
                messages.error(request, f"Validation error: {str(e)}")
                return render(request, 'lms/edit_resource.html', {'form': form, 'grade': grade, 'subject': subject, 'resource': resource})
            except Exception as e:
                logger.error(f"Unexpected error editing resource: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'An unexpected error occurred. Please try again.'}, status=500)
                messages.error(request, "An unexpected error occurred. Please try again.")
                return render(request, 'lms/error.html', {'message': 'Failed to edit resource.'}, status=500)
        else:
            logger.error(f"Form validation failed: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Please correct the errors below.', 'errors': form.errors.as_json()}, status=400)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceUploadForm(instance=resource, initial={'subject': subject or resource.subject, 'grade': grade})

    context = {
        'form': form,
        'grade': grade,
        'subject': subject,
        'resource': resource,
    }
    return render(request, 'lms/edit_resource.html', context)


@login_required
@user_passes_test(is_admin)
def delete_resource(request, resource_id):
    """Delete a resource"""
    try:
        resource = get_object_or_404(Resource, id=resource_id)
        if request.method == 'POST':
            resource_title = resource.title
            subject_id = resource.subject.id
            grade_id = resource.subject.grades.first().id if resource.subject.grades.exists() else None
            resource.delete()

            logger.info(f"Resource {resource_id} ({resource_title}) deleted by {request.user.username}")
            messages.success(request, f'Resource "{resource_title}" deleted successfully!')
            next_url = request.GET.get('next', f"/subject/{grade_id}/{subject_id}/" if grade_id else "/superuser/")
            return redirect(f"/loading/?next={next_url}")

        context = {
            'resource': resource,
        }

        return render(request, 'lms/delete_resource.html', context)

    except Http404:
        messages.error(request, "Resource not found.")
        return render(request, 'lms/error.html', {'message': 'Resource not found.'})
    except Exception as e:
        logger.error(f"Error deleting resource {resource_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the resource.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete resource.'})

@login_required
@user_passes_test(is_admin)
def admin_add_education_level(request):
    """Add a new education level"""
    if request.method == 'POST':
        form = EducationLevelForm(request.POST)
        if form.is_valid():
            education_level = form.save()
            logger.info(f"Education level {education_level.id} added by {request.user.username}")
            messages.success(request, f'Education level "{education_level.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EducationLevelForm()

    return render(request, 'lms/admin_add_education_level.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_education_level(request, education_level_id):
    """Edit an existing education level"""
    try:
        education_level = get_object_or_404(EducationLevel, id=education_level_id)
        if request.method == 'POST':
            form = EducationLevelForm(request.POST, instance=education_level)
            if form.is_valid():
                updated_education_level = form.save()
                logger.info(f"Education level {education_level_id} updated by {request.user.username}")
                messages.success(request, f'Education level "{updated_education_level.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = EducationLevelForm(instance=education_level)

        context = {
            'form': form,
            'education_level': education_level,
        }

        return render(request, 'lms/admin_edit_education_level.html', context)

    except Http404:
        messages.error(request, "Education level not found.")
        return render(request, 'lms/error.html', {'message': 'Education level not found.'})
    except Exception as e:
        logger.error(f"Error editing education level {education_level_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the education level.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit education level.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_education_level(request, education_level_id):
    """Delete an education level"""
    try:
        education_level = get_object_or_404(EducationLevel, id=education_level_id)
        if request.method == 'POST':
            education_level_name = education_level.name
            education_level.delete()

            logger.info(f"Education level {education_level_id} ({education_level_name}) deleted by {request.user.username}")
            messages.success(request, f'Education level "{education_level_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'education_level': education_level,
        }

        return render(request, 'lms/admin_delete_education_level.html', context)

    except Http404:
        messages.error(request, "Education level not found.")
        return render(request, 'lms/error.html', {'message': 'Education level not found.'})
    except Exception as e:
        logger.error(f"Error deleting education level {education_level_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the education level.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete education level.'})

@login_required
@user_passes_test(is_admin)
def admin_add_category(request):
    """Add a new subject category"""
    if request.method == 'POST':
        form = SubjectCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            logger.info(f"Category {category.id} added by {request.user.username}")
            messages.success(request, f'Category "{category.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectCategoryForm()

    return render(request, 'lms/admin_add_category.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_category(request, category_id):
    """Edit an existing category"""
    try:
        category = get_object_or_404(SubjectCategory, id=category_id)
        if request.method == 'POST':
            form = SubjectCategoryForm(request.POST, instance=category)
            if form.is_valid():
                updated_category = form.save()
                logger.info(f"Category {category_id} updated by {request.user.username}")
                messages.success(request, f'Category "{updated_category.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = SubjectCategoryForm(instance=category)

        context = {
            'form': form,
            'category': category,
        }

        return render(request, 'lms/admin_edit_category.html', context)

    except Http404:
        messages.error(request, "Category not found.")
        return render(request, 'lms/error.html', {'message': 'Category not found.'})
    except Exception as e:
        logger.error(f"Error editing category {category_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the category.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit category.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_category(request, category_id):
    """Delete a category"""
    try:
        category = get_object_or_404(SubjectCategory, id=category_id)
        if request.method == 'POST':
            category_name = category.name
            category.delete()

            logger.info(f"Category {category_id} ({category_name}) deleted by {request.user.username}")
            messages.success(request, f'Category "{category_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'category': category,
        }

        return render(request, 'lms/admin_delete_category.html', context)

    except Http404:
        messages.error(request, "Category not found.")
        return render(request, 'lms/error.html', {'message': 'Category not found.'})
    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the category.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete category.'})

@login_required
@user_passes_test(is_admin)
def admin_add_grade(request):
    """Add a new grade"""
    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            grade = form.save()
            logger.info(f"Grade {grade.id} added by {request.user.username}")
            messages.success(request, f'Grade "{grade.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GradeForm()

    return render(request, 'lms/admin_add_grade.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_grade(request, grade_id):
    """Edit an existing grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        if request.method == 'POST':
            form = GradeForm(request.POST, instance=grade)
            if form.is_valid():
                updated_grade = form.save()
                logger.info(f"Grade {grade_id} updated by {request.user.username}")
                messages.success(request, f'Grade "{updated_grade.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = GradeForm(instance=grade)

        context = {
            'form': form,
            'grade': grade,
        }

        return render(request, 'lms/admin_edit_grade.html', context)

    except Http404:
        messages.error(request, "Grade not found.")
        return render(request, 'lms/error.html', {'message': 'Grade not found.'})
    except Exception as e:
        logger.error(f"Error editing grade {grade_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the grade.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit grade.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_grade(request, grade_id):
    """Delete a grade"""
    try:
        grade = get_object_or_404(Grade, id=grade_id)
        if request.method == 'POST':
            grade_name = grade.name
            grade.delete()

            logger.info(f"Grade {grade_id} ({grade_name}) deleted by {request.user.username}")
            messages.success(request, f'Grade "{grade_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'grade': grade,
        }

        return render(request, 'lms/admin_delete_grade.html', context)

    except Http404:
        messages.error(request, "Grade not found.")
        return render(request, 'lms/error.html', {'message': 'Grade not found.'})
    except Exception as e:
        logger.error(f"Error deleting grade {grade_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the grade.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete grade.'})

@login_required
@user_passes_test(is_admin)
def admin_add_subject(request):
    """Add a new subject"""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            logger.info(f"Subject {subject.id} added by {request.user.username}")
            messages.success(request, f'Subject "{subject.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SubjectForm()

    return render(request, 'lms/admin_add_subject.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_subject(request, subject_id):
    """Edit an existing subject"""
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        if request.method == 'POST':
            form = SubjectForm(request.POST, instance=subject)
            if form.is_valid():
                updated_subject = form.save()
                logger.info(f"Subject {subject_id} updated by {request.user.username}")
                messages.success(request, f'Subject "{updated_subject.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = SubjectForm(instance=subject)

        context = {
            'form': form,
            'subject': subject,
        }

        return render(request, 'lms/admin_edit_subject.html', context)

    except Http404:
        messages.error(request, "Subject not found.")
        return render(request, 'lms/error.html', {'message': 'Subject not found.'})
    except Exception as e:
        logger.error(f"Error editing subject {subject_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the subject.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit subject.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_subject(request, subject_id):
    """Delete a subject"""
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        if request.method == 'POST':
            subject_name = subject.name
            subject.delete()

            logger.info(f"Subject {subject_id} ({subject_name}) deleted by {request.user.username}")
            messages.success(request, f'Subject "{subject_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'subject': subject,
        }

        return render(request, 'lms/admin_delete_subject.html', context)

    except Http404:
        messages.error(request, "Subject not found.")
        return render(request, 'lms/error.html', {'message': 'Subject not found.'})
    except Exception as e:
        logger.error(f"Error deleting subject {subject_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the subject.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete subject.'})

@login_required
@user_passes_test(is_admin)
def admin_add_resource_type(request):
    """Add a new resource type"""
    if request.method == 'POST':
        form = ResourceTypeForm(request.POST)
        if form.is_valid():
            resource_type = form.save()
            logger.info(f"Resource type {resource_type.id} added by {request.user.username}")
            messages.success(request, f'Resource type "{resource_type.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ResourceTypeForm()

    return render(request, 'lms/admin_add_resource_type.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_resource_type(request, resource_type_id):
    """Edit an existing resource type"""
    try:
        resource_type = get_object_or_404(ResourceType, id=resource_type_id)
        if request.method == 'POST':
            form = ResourceTypeForm(request.POST, instance=resource_type)
            if form.is_valid():
                updated_resource_type = form.save()
                logger.info(f"Resource type {resource_type_id} updated by {request.user.username}")
                messages.success(request, f'Resource type "{updated_resource_type.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = ResourceTypeForm(instance=resource_type)

        context = {
            'form': form,
            'resource_type': resource_type,
        }

        return render(request, 'lms/admin_edit_resource_type.html', context)

    except Http404:
        messages.error(request, "Resource type not found.")
        return render(request, 'lms/error.html', {'message': 'Resource type not found.'})
    except Exception as e:
        logger.error(f"Error editing resource type {resource_type_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the resource type.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit resource type.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_resource_type(request, resource_type_id):
    """Delete a resource type"""
    try:
        resource_type = get_object_or_404(ResourceType, id=resource_type_id)
        if request.method == 'POST':
            resource_type_name = resource_type.name
            resource_type.delete()

            logger.info(f"Resource type {resource_type_id} ({resource_type_name}) deleted by {request.user.username}")
            messages.success(request, f'Resource type "{resource_type_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'resource_type': resource_type,
        }

        return render(request, 'lms/admin_delete_resource_type.html', context)

    except Http404:
        messages.error(request, "Resource type not found.")
        return render(request, 'lms/error.html', {'message': 'Resource type not found.'})
    except Exception as e:
        logger.error(f"Error deleting resource type {resource_type_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the resource type.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete resource type.'})

@login_required
@user_passes_test(is_admin)
def admin_add_pathway(request):
    """Add a new pathway"""
    if request.method == 'POST':
        form = PathwayForm(request.POST)
        if form.is_valid():
            pathway = form.save()
            logger.info(f"Pathway {pathway.id} added by {request.user.username}")
            messages.success(request, f'Pathway "{pathway.name}" added successfully!')
            return redirect("/loading/?next=/superuser/")
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PathwayForm()

    return render(request, 'lms/admin_add_pathway.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def admin_edit_pathway(request, pathway_id):
    """Edit an existing pathway"""
    try:
        pathway = get_object_or_404(Pathway, id=pathway_id)
        if request.method == 'POST':
            form = PathwayForm(request.POST, instance=pathway)
            if form.is_valid():
                updated_pathway = form.save()
                logger.info(f"Pathway {pathway_id} updated by {request.user.username}")
                messages.success(request, f'Pathway "{updated_pathway.name}" updated successfully!')
                return redirect("/loading/?next=/superuser/")
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = PathwayForm(instance=pathway)

        context = {
            'form': form,
            'pathway': pathway,
        }

        return render(request, 'lms/admin_edit_pathway.html', context)

    except Http404:
        messages.error(request, "Pathway not found.")
        return render(request, 'lms/error.html', {'message': 'Pathway not found.'})
    except Exception as e:
        logger.error(f"Error editing pathway {pathway_id}: {str(e)}")
        messages.error(request, 'An error occurred while editing the pathway.')
        return render(request, 'lms/error.html', {'message': 'Failed to edit pathway.'})

@login_required
@user_passes_test(is_admin)
def admin_delete_pathway(request, pathway_id):
    """Delete a pathway"""
    try:
        pathway = get_object_or_404(Pathway, id=pathway_id)
        if request.method == 'POST':
            pathway_name = pathway.name
            pathway.delete()

            logger.info(f"Pathway {pathway_id} ({pathway_name}) deleted by {request.user.username}")
            messages.success(request, f'Pathway "{pathway_name}" deleted successfully!')
            return redirect("/loading/?next=/superuser/")

        context = {
            'pathway': pathway,
        }

        return render(request, 'lms/admin_delete_pathway.html', context)

    except Http404:
        messages.error(request, "Pathway not found.")
        return render(request, 'lms/error.html', {'message': 'Pathway not found.'})
    except Exception as e:
        logger.error(f"Error deleting pathway {pathway_id}: {str(e)}")
        messages.error(request, 'An error occurred while deleting the pathway.')
        return render(request, 'lms/error.html', {'message': 'Failed to delete pathway.'})

def category_dashboard(request, category_id):
    """Display subjects for a specific category"""
    try:
        category = get_object_or_404(SubjectCategory, id=category_id)
        subjects = Subject.objects.filter(category=category).order_by('name')
        grades = Grade.objects.filter(subjects__category=category).distinct().order_by('order')
        resources = Resource.objects.filter(subject__category=category, is_active=True).order_by('-created_at')

        context = {
            'category': category,
            'subjects': subjects,
            'grades': grades,
            'resources': resources,
        }

        return render(request, 'lms/category_dashboard.html', context)

    except Http404:
        messages.error(request, "Category not found.")
        return render(request, 'lms/error.html', {'message': 'Category not found.'})
    except Exception as e:
        logger.error(f"Error loading category {category_id}: {str(e)}")
        messages.error(request, 'An error occurred while loading the category. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load category.'})

def resource_list(request):
    """Display a paginated list of all resources"""
    try:
        resources = Resource.objects.filter(is_active=True).select_related('subject', 'resource_type').order_by('-created_at')
        paginator = Paginator(resources, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'resources': page_obj.object_list,
        }

        return render(request, 'lms/resource_list.html', context)

    except Exception as e:
        logger.error(f"Error loading resource list: {str(e)}")
        messages.error(request, 'An error occurred while loading the resource list. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load resource list.'})

def debug_grades(request):
    """Debug view to display all grades"""
    try:
        grades = Grade.objects.select_related('education_level').all().order_by('education_level__order', 'order')
        context = {
            'grades': grades,
        }
        return render(request, 'lms/debug_grades.html', context)

    except Exception as e:
        logger.error(f"Error loading debug grades: {str(e)}")
        messages.error(request, 'An error occurred while loading grades. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load grades.'})

# AJAX views for dynamic content loading
@require_http_methods(["GET"])
def admin_get_subjects(request):
    """Get subjects for a specific grade (AJAX)"""
    grade_id = request.GET.get('grade_id')
    if grade_id:
        try:
            grade = Grade.objects.get(id=grade_id)
            subjects = Subject.objects.filter(grades=grade).order_by('name')
            data = [
                {
                    'id': subject.id,
                    'name': subject.name,
                    'category': subject.category.name if subject.category else ''
                }
                for subject in subjects
            ]
            return JsonResponse({'subjects': data})
        except Grade.DoesNotExist:
            return JsonResponse({'error': 'Grade not found'}, status=404)
    return JsonResponse({'error': 'Grade ID required'}, status=400)

@require_http_methods(["GET"])
def admin_get_grades(request):
    """Get grades for a specific education level (AJAX)"""
    level_id = request.GET.get('level_id')
    if level_id:
        try:
            level = EducationLevel.objects.get(id=level_id)
            grades = Grade.objects.filter(education_level=level).order_by('order')
            data = [
                {
                    'id': grade.id,
                    'name': grade.name,
                    'order': grade.order
                }
                for grade in grades
            ]
            return JsonResponse({'grades': data})
        except EducationLevel.DoesNotExist:
            return JsonResponse({'error': 'Education level not found'}, status=404)
    return JsonResponse({'error': 'Level ID required'}, status=400)

@require_http_methods(["GET"])
def admin_get_education_levels(request):
    """Get all education levels for admin interface"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_education_levels by {request.user.username}")
        raise Http404

    try:
        education_levels = EducationLevel.objects.all().order_by('order')
        education_level_data = [
            {
                'id': el.id,
                'name': el.name,
                'description': el.description,
                'order': el.order,
                'icon': el.icon
            }
            for el in education_levels
        ]
        return JsonResponse({'success': True, 'education_levels': education_level_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["GET"])
def admin_get_education_level(request):
    """Get a specific education level for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_education_level by {request.user.username}")
        raise Http404

    education_level_id = request.GET.get('education_level_id')
    if not education_level_id:
        return JsonResponse({'success': False, 'error': 'Education level ID required'}, status=400)

    try:
        education_level = EducationLevel.objects.get(id=education_level_id)
        return JsonResponse({
            'success': True,
            'id': education_level.id,
            'name': education_level.name,
            'description': education_level.description,
            'order': education_level.order,
            'icon': education_level.icon
        })
    except EducationLevel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Education level not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_grade(request):
    """Get a specific grade for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_grade by {request.user.username}")
        raise Http404

    grade_id = request.GET.get('grade_id')
    if not grade_id:
        return JsonResponse({'success': False, 'error': 'Grade ID required'}, status=400)

    try:
        grade = Grade.objects.get(id=grade_id)
        return JsonResponse({
            'success': True,
            'id': grade.id,
            'name': grade.name,
            'education_level_id': grade.education_level.id,
            'order': grade.order,
            'description': grade.description
        })
    except Grade.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Grade not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_category(request):
    """Get a specific category for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_category by {request.user.username}")
        raise Http404

    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'success': False, 'error': 'Category ID required'}, status=400)

    try:
        category = SubjectCategory.objects.get(id=category_id)
        return JsonResponse({
            'success': True,
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon
        })
    except SubjectCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_subject(request):
    """Get a specific subject for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_subject by {request.user.username}")
        raise Http404

    subject_id = request.GET.get('subject_id')
    if not subject_id:
        return JsonResponse({'success': False, 'error': 'Subject ID required'}, status=400)

    try:
        subject = Subject.objects.get(id=subject_id)
        return JsonResponse({
            'success': True,
            'id': subject.id,
            'name': subject.name,
            'category_id': subject.category.id if subject.category else None,
            'description': subject.description,
            'grade_ids': [grade.id for grade in subject.grades.all()]
        })
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_resource_type(request):
    """Get a specific resource type for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_resource_type by {request.user.username}")
        raise Http404

    resource_type_id = request.GET.get('resource_type_id')
    if not resource_type_id:
        return JsonResponse({'success': False, 'error': 'Resource type ID required'}, status=400)

    try:
        resource_type = ResourceType.objects.get(id=resource_type_id)
        return JsonResponse({
            'success': True,
            'id': resource_type.id,
            'name': resource_type.name,
            'description': resource_type.description,
            'mime_type': resource_type.mime_type,
            'file_extension': resource_type.file_extension
        })
    except ResourceType.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource type not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_pathway(request):
    """Get a specific pathway for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_pathway by {request.user.username}")
        raise Http404

    pathway_id = request.GET.get('pathway_id')
    if not pathway_id:
        return JsonResponse({'success': False, 'error': 'Pathway ID required'}, status=400)

    try:
        pathway = Pathway.objects.get(id=pathway_id)
        return JsonResponse({
            'success': True,
            'id': pathway.id,
            'name': pathway.name,
            'description': pathway.description,
            'grade_id': pathway.grade.id
        })
    except Pathway.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pathway not found'}, status=404)

@require_http_methods(["GET"])
def admin_get_resource(request):
    """Get a specific resource for editing"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_resource by {request.user.username}")
        raise Http404

    resource_id = request.GET.get('resource_id')
    if not resource_id:
        return JsonResponse({'success': False, 'error': 'Resource ID required'}, status=400)

    try:
        resource = Resource.objects.get(id=resource_id)
        return JsonResponse({
            'success': True,
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'subject_id': resource.subject.id,
            'resource_type_id': resource.resource_type.id if resource.resource_type else None,
            'is_active': resource.is_active
        })
    except Resource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource not found'}, status=404)

@require_http_methods(["POST"])
@csrf_exempt
def admin_toggle_download(request):
    """Toggle the download availability (is_active) of a resource"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_toggle_download by {request.user.username}")
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    resource_id = request.POST.get('resource_id')
    if not resource_id:
        return JsonResponse({'success': False, 'error': 'Resource ID required'}, status=400)

    try:
        resource = Resource.objects.get(id=resource_id)
        resource.is_active = not resource.is_active
        resource.save()

        logger.info(f"Resource {resource_id} download toggled to {resource.is_active} by {request.user.username}")
        return JsonResponse({
            'success': True,
            'is_active': resource.is_active,
            'resource_id': resource.id
        })
    except Resource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_get_resource_types(request):
    """Get all resource types for admin interface"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_resource_types by {request.user.username}")
        raise Http404

    try:
        resource_types = ResourceType.objects.all().order_by('name')
        resource_type_data = [
            {
                'id': rt.id,
                'name': rt.name,
                'description': rt.description,
                'mime_type': rt.mime_type,
                'file_extension': rt.file_extension
            }
            for rt in resource_types
        ]
        return JsonResponse({'success': True, 'resource_types': resource_type_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_get_pathways(request):
    """Get all pathways for admin interface"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_pathways by {request.user.username}")
        raise Http404

    try:
        pathways = Pathway.objects.all().order_by('name')
        pathway_data = [
            {
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'grade_id': p.grade.id if p.grade else None
            }
            for p in pathways
        ]
        return JsonResponse({'success': True, 'pathways': pathway_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def admin_get_categories(request):
    """Get all categories for admin interface"""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized access to admin_get_categories by {request.user.username}")
        raise Http404

    try:
        categories = SubjectCategory.objects.all().order_by('name')
        category_data = [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'icon': c.icon
            }
            for c in categories
        ]
        return JsonResponse({'success': True, 'categories': category_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def search(request):
    """Search for resources, subjects, and grades"""
    query = request.GET.get('q', '').strip()
    resource_type = request.GET.get('type', '')

    results = {
        'resources': [],
        'subjects': [],
        'grades': [],
        'education_levels': []
    }

    if query:
        resource_query = Resource.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).filter(is_active=True)

        if resource_type:
            resource_query = resource_query.filter(resource_type__id=resource_type)

        resources = resource_query.select_related('subject', 'uploaded_by')[:10]
        results['resources'] = [
            {
                'id': r.id,
                'title': r.title,
                'description': r.description,
                'subject': r.subject.name,
                'grade': r.subject.grades.first().name if r.subject.grades.exists() else '',
                'type': r.get_resource_type_display(),
                'uploaded_by': r.uploaded_by.username,
                'upload_date': r.upload_date.strftime('%Y-%m-%d'),
                'url': f'/subject/{r.subject.grades.first().id}/{r.subject.id}/'
            }
            for r in resources
        ]

        subjects = Subject.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).prefetch_related('grades')[:10]

        results['subjects'] = [
            {
                'id': s.id,
                'name': s.name,
                'description': s.description,
                'grades': [g.name for g in s.grades.all()],
                'url': f'/subject/{s.grades.first().id}/{s.id}/' if s.grades.exists() else '#'
            }
            for s in subjects
        ]

        grades = Grade.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        ).select_related('education_level')[:10]

        results['grades'] = [
            {
                'id': g.id,
                'name': g.name,
                'description': g.description,
                'education_level': g.education_level.name,
                'url': f'/grade/{g.id}/'
            }
            for g in grades
        ]

        education_levels = EducationLevel.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:10]

        results['education_levels'] = [
            {
                'id': el.id,
                'name': el.name,
                'description': el.description,
                'url': f'/education-level/{el.id}/'
            }
            for el in education_levels
        ]

    context = {
        'query': query,
        'results': results,
        'resource_type': resource_type,
        'all_resource_types': ResourceType.objects.all(),
    }

    return render(request, 'lms/search_results.html', context)

def my_downloads(request):
    """Display user's downloaded resources"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your downloads.")
        return redirect('lms:grade_level_dashboard')

    try:
        downloaded_resources = Resource.objects.filter(
            download_logs__user=request.user
        ).select_related('subject', 'uploaded_by').order_by('-download_logs__downloaded_at')[:50]

        downloads_by_date = {}
        for resource in downloaded_resources:
            download_log = resource.download_logs.filter(user=request.user).first()
            if download_log:
                date_str = download_log.downloaded_at.strftime('%Y-%m-%d')
                if date_str not in downloads_by_date:
                    downloads_by_date[date_str] = []
                downloads_by_date[date_str].append({
                    'resource': resource,
                    'downloaded_at': download_log.downloaded_at
                })

        context = {
            'downloads_by_date': downloads_by_date,
        }

        return render(request, 'lms/my_downloads.html', context)

    except Exception as e:
        logger.error(f"Error loading my downloads: {str(e)}")
        messages.error(request, 'An error occurred while loading your downloads. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load downloads.'})

def my_uploads(request):
    """Display user's uploaded resources"""
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your uploads.")
        return redirect('lms:grade_level_dashboard')

    try:
        uploaded_resources = Resource.objects.filter(
            uploaded_by=request.user
        ).select_related('subject').order_by('-upload_date')

        uploads_by_subject = {}
        for resource in uploaded_resources:
            subject_name = resource.subject.name
            if subject_name not in uploads_by_subject:
                uploads_by_subject[subject_name] = []
            uploads_by_subject[subject_name].append(resource)

        context = {
            'uploads_by_subject': uploads_by_subject,
        }

        return render(request, 'lms/my_uploads.html', context)

    except Exception as e:
        logger.error(f"Error loading my uploads: {str(e)}")
        messages.error(request, 'An error occurred while loading your uploads. Please try again.')
        return render(request, 'lms/error.html', {'message': 'Failed to load uploads.'})

# AJAX views for dynamic updates
@require_http_methods(["POST"])
@csrf_exempt
def admin_add_education_level_ajax(request):
    """Add a new education level (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    order = request.POST.get('order', '').strip()
    icon = request.POST.get('icon', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

    if EducationLevel.objects.filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'error': 'Education level with this name already exists'}, status=400)

    try:
        education_level = EducationLevel.objects.create(
            name=name,
            description=description,
            order=order if order else None,
            icon=icon
        )
        logger.info(f"Education level {education_level.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': education_level.id,
            'name': education_level.name,
            'description': education_level.description,
            'order': education_level.order,
            'icon': education_level.icon
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_education_level(request):
    """Edit an existing education level (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    education_level_id = request.POST.get('education_level_id')
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    order = request.POST.get('order', '').strip()
    icon = request.POST.get('icon', '').strip()

    if not all([education_level_id, name]):
        return JsonResponse({'success': False, 'error': 'Name and education level ID are required'}, status=400)

    try:
        education_level = EducationLevel.objects.get(id=education_level_id)
        if education_level.name != name and EducationLevel.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Education level with this name already exists'}, status=400)

        education_level.name = name
        education_level.description = description
        education_level.order = order if order else None
        education_level.icon = icon
        education_level.save()

        logger.info(f"Education level {education_level_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except EducationLevel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Education level not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_education_level(request):
    """Delete an education level (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    education_level_id = request.POST.get('education_level_id')
    if not education_level_id:
        return JsonResponse({'success': False, 'error': 'Education level ID required'}, status=400)

    try:
        education_level = EducationLevel.objects.get(id=education_level_id)
        education_level_name = education_level.name
        education_level.delete()

        logger.info(f"Education level {education_level_id} ({education_level_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except EducationLevel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Education level not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_add_grade(request):
    """Add a new grade (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    education_level_id = request.POST.get('education_level_id')
    order = request.POST.get('order', '').strip()
    description = request.POST.get('description', '').strip()

    if not all([name, education_level_id]):
        return JsonResponse({'success': False, 'error': 'Name and education level ID are required'}, status=400)

    try:
        education_level = EducationLevel.objects.get(id=education_level_id)
        if Grade.objects.filter(name__iexact=name, education_level=education_level).exists():
            return JsonResponse({'success': False, 'error': 'Grade with this name already exists for this education level'}, status=400)

        grade = Grade.objects.create(
            name=name,
            education_level=education_level,
            order=order if order else None,
            description=description
        )
        logger.info(f"Grade {grade.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': grade.id,
            'name': grade.name,
            'education_level_id': grade.education_level.id,
            'order': grade.order,
            'description': grade.description
        })
    except EducationLevel.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Education level not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_grade(request):
    """Edit an existing grade (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    grade_id = request.POST.get('grade_id')
    name = request.POST.get('name', '').strip()
    education_level_id = request.POST.get('education_level_id')
    order = request.POST.get('order', '').strip()
    description = request.POST.get('description', '').strip()

    if not all([grade_id, name, education_level_id]):
        return JsonResponse({'success': False, 'error': 'Name, grade ID, and education level ID are required'}, status=400)

    try:
        grade = Grade.objects.get(id=grade_id)
        education_level = EducationLevel.objects.get(id=education_level_id)
        if grade.name != name and Grade.objects.filter(name__iexact=name, education_level=education_level).exists():
            return JsonResponse({'success': False, 'error': 'Grade with this name already exists for this education level'}, status=400)

        grade.name = name
        grade.education_level = education_level
        grade.order = order if order else None
        grade.description = description
        grade.save()

        logger.info(f"Grade {grade_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except (Grade.DoesNotExist, EducationLevel.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Grade or education level not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_grade(request):
    """Delete a grade (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    grade_id = request.POST.get('grade_id')
    if not grade_id:
        return JsonResponse({'success': False, 'error': 'Grade ID required'}, status=400)

    try:
        grade = Grade.objects.get(id=grade_id)
        grade_name = grade.name
        grade.delete()

        logger.info(f"Grade {grade_id} ({grade_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except Grade.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Grade not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_add_category(request):
    """Add a new category (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    icon = request.POST.get('icon', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

    if SubjectCategory.objects.filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'error': 'Category with this name already exists'}, status=400)

    try:
        category = SubjectCategory.objects.create(
            name=name,
            description=description,
            icon=icon
        )
        logger.info(f"Category {category.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'icon': category.icon
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_category(request):
    """Edit an existing category (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    category_id = request.POST.get('category_id')
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    icon = request.POST.get('icon', '').strip()

    if not all([category_id, name]):
        return JsonResponse({'success': False, 'error': 'Name and category ID are required'}, status=400)

    try:
        category = SubjectCategory.objects.get(id=category_id)
        if category.name != name and SubjectCategory.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Category with this name already exists'}, status=400)

        category.name = name
        category.description = description
        category.icon = icon
        category.save()

        logger.info(f"Category {category_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except SubjectCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_category(request):
    """Delete a category (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    category_id = request.POST.get('category_id')
    if not category_id:
        return JsonResponse({'success': False, 'error': 'Category ID required'}, status=400)

    try:
        category = SubjectCategory.objects.get(id=category_id)
        category_name = category.name
        category.delete()

        logger.info(f"Category {category_id} ({category_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except SubjectCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_add_subject(request):
    """Add a new subject (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    category_id = request.POST.get('category_id')
    description = request.POST.get('description', '').strip()
    grade_ids = request.POST.getlist('grades')

    if not all([name, category_id]):
        return JsonResponse({'success': False, 'error': 'Name and category ID are required'}, status=400)

    try:
        category = SubjectCategory.objects.get(id=category_id)
        if Subject.objects.filter(name__iexact=name, category=category).exists():
            return JsonResponse({'success': False, 'error': 'Subject with this name already exists in this category'}, status=400)

        subject = Subject.objects.create(
            name=name,
            category=category,
            description=description
        )
        if grade_ids:
            subject.grades.set(grade_ids)

        logger.info(f"Subject {subject.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': subject.id,
            'name': subject.name,
            'category_id': subject.category.id,
            'description': subject.description,
            'grade_ids': [int(gid) for gid in grade_ids]
        })
    except SubjectCategory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_subject(request):
    """Edit an existing subject (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    subject_id = request.POST.get('subject_id')
    name = request.POST.get('name', '').strip()
    category_id = request.POST.get('category_id')
    description = request.POST.get('description', '').strip()
    grade_ids = request.POST.getlist('grades')

    if not all([subject_id, name, category_id]):
        return JsonResponse({'success': False, 'error': 'Name, subject ID, and category ID are required'}, status=400)

    try:
        subject = Subject.objects.get(id=subject_id)
        category = SubjectCategory.objects.get(id=category_id)
        if subject.name != name and Subject.objects.filter(name__iexact=name, category=category).exists():
            return JsonResponse({'success': False, 'error': 'Subject with this name already exists in this category'}, status=400)

        subject.name = name
        subject.category = category
        subject.description = description
        subject.save()
        subject.grades.set(grade_ids)

        logger.info(f"Subject {subject_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except (Subject.DoesNotExist, SubjectCategory.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Subject or category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_subject(request):
    """Delete a subject (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    subject_id = request.POST.get('subject_id')
    if not subject_id:
        return JsonResponse({'success': False, 'error': 'Subject ID required'}, status=400)

    try:
        subject = Subject.objects.get(id=subject_id)
        subject_name = subject.name
        subject.delete()

        logger.info(f"Subject {subject_id} ({subject_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting subject {subject_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_add_resource_type(request):
    """Add a new resource type (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    mime_type = request.POST.get('mime_type', '').strip()
    file_extension = request.POST.get('file_extension', '').strip()

    if not name:
        return JsonResponse({'success': False, 'error': 'Name is required'}, status=400)

    if ResourceType.objects.filter(name__iexact=name).exists():
        return JsonResponse({'success': False, 'error': 'Resource type with this name already exists'}, status=400)

    try:
        resource_type = ResourceType.objects.create(
            name=name,
            description=description,
            mime_type=mime_type,
            file_extension=file_extension
        )
        logger.info(f"Resource type {resource_type.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': resource_type.id,
            'name': resource_type.name,
            'description': resource_type.description,
            'mime_type': resource_type.mime_type,
            'file_extension': resource_type.file_extension
        })
    except Exception as e:
        logger.error(f"Error adding resource type: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_resource_type(request):
    """Edit an existing resource type (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    resource_type_id = request.POST.get('resource_type_id')
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    mime_type = request.POST.get('mime_type', '').strip()
    file_extension = request.POST.get('file_extension', '').strip()

    if not all([resource_type_id, name]):
        return JsonResponse({'success': False, 'error': 'Name and resource type ID are required'}, status=400)

    try:
        resource_type = ResourceType.objects.get(id=resource_type_id)
        if resource_type.name != name and ResourceType.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Resource type with this name already exists'}, status=400)

        resource_type.name = name
        resource_type.description = description
        resource_type.mime_type = mime_type
        resource_type.file_extension = file_extension
        resource_type.save()

        logger.info(f"Resource type {resource_type_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except ResourceType.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource type not found'}, status=404)
    except Exception as e:
        logger.error(f"Error editing resource type {resource_type_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_resource_type(request):
    """Delete a resource type (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    resource_type_id = request.POST.get('resource_type_id')
    if not resource_type_id:
        return JsonResponse({'success': False, 'error': 'Resource type ID required'}, status=400)

    try:
        resource_type = ResourceType.objects.get(id=resource_type_id)
        resource_type_name = resource_type.name
        resource_type.delete()

        logger.info(f"Resource type {resource_type_id} ({resource_type_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except ResourceType.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource type not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting resource type {resource_type_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_add_pathway(request):
    """Add a new pathway (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    grade_id = request.POST.get('grade_id')

    if not all([name, grade_id]):
        return JsonResponse({'success': False, 'error': 'Name and grade ID are required'}, status=400)

    try:
        grade = Grade.objects.get(id=grade_id)
        if Pathway.objects.filter(name__iexact=name, grade=grade).exists():
            return JsonResponse({'success': False, 'error': 'Pathway with this name already exists for this grade'}, status=400)

        pathway = Pathway.objects.create(
            name=name,
            description=description,
            grade=grade
        )
        logger.info(f"Pathway {pathway.id} added by {request.user.username}")
        return JsonResponse({
            'success': True,
            'id': pathway.id,
            'name': pathway.name,
            'description': pathway.description,
            'grade_id': pathway.grade.id
        })
    except Grade.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Grade not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding pathway: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_edit_pathway(request):
    """Edit an existing pathway (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    pathway_id = request.POST.get('pathway_id')
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    grade_id = request.POST.get('grade_id')

    if not all([pathway_id, name, grade_id]):
        return JsonResponse({'success': False, 'error': 'Name, pathway ID, and grade ID are required'}, status=400)

    try:
        pathway = Pathway.objects.get(id=pathway_id)
        grade = Grade.objects.get(id=grade_id)
        if pathway.name != name and Pathway.objects.filter(name__iexact=name, grade=grade).exists():
            return JsonResponse({'success': False, 'error': 'Pathway with this name already exists for this grade'}, status=400)

        pathway.name = name
        pathway.description = description
        pathway.grade = grade
        pathway.save()

        logger.info(f"Pathway {pathway_id} edited by {request.user.username}")
        return JsonResponse({'success': True})
    except (Pathway.DoesNotExist, Grade.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Pathway or grade not found'}, status=404)
    except Exception as e:
        logger.error(f"Error editing pathway {pathway_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_delete_pathway(request):
    """Delete a pathway (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    pathway_id = request.POST.get('pathway_id')
    if not pathway_id:
        return JsonResponse({'success': False, 'error': 'Pathway ID required'}, status=400)

    try:
        pathway = Pathway.objects.get(id=pathway_id)
        pathway_name = pathway.name
        pathway.delete()

        logger.info(f"Pathway {pathway_id} ({pathway_name}) deleted by {request.user.username}")
        return JsonResponse({'success': True})
    except Pathway.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pathway not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting pathway {pathway_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["POST"])
@csrf_exempt
def admin_toggle_resource_visibility(request):
    """Toggle resource visibility (is_active) for admin (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    resource_id = request.POST.get('resource_id')
    if not resource_id:
        return JsonResponse({'success': False, 'error': 'Resource ID required'}, status=400)

    try:
        resource = Resource.objects.get(id=resource_id)
        resource.is_active = not resource.is_active
        resource.save()

        logger.info(f"Resource {resource_id} visibility toggled to {resource.is_active} by {request.user.username}")
        return JsonResponse({
            'success': True,
            'is_active': resource.is_active,
            'resource_id': resource.id
        })
    except Resource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource not found'}, status=404)
    except Exception as e:
        logger.error(f"Error toggling resource visibility {resource_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_resource_stats(request):
    """Get statistics for a specific resource (AJAX)"""
    resource_id = request.GET.get('resource_id')
    if not resource_id:
        return JsonResponse({'success': False, 'error': 'Resource ID required'}, status=400)

    try:
        resource = Resource.objects.get(id=resource_id)
        stats = {
            'view_count': resource.view_count,
            'download_count': resource.download_count,
            'upload_date': resource.upload_date.strftime('%Y-%m-%d'),
            'last_download': resource.download_logs.order_by('-downloaded_at').first().downloaded_at.strftime('%Y-%m-%d %H:%M:%S') if resource.download_logs.exists() else None
        }
        return JsonResponse({'success': True, 'stats': stats})
    except Resource.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Resource not found'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching resource stats {resource_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """Get overall dashboard statistics (AJAX)"""
    try:
        stats = {
            'total_resources': Resource.objects.filter(is_active=True).count(),
            'total_subjects': Subject.objects.count(),
            'total_grades': Grade.objects.count(),
            'total_education_levels': EducationLevel.objects.count(),
            'recent_uploads': Resource.objects.filter(is_active=True).order_by('-upload_date')[:5].values(
                'id', 'title', 'upload_date', 'subject__name'
            ),
            'most_downloaded': Resource.objects.filter(is_active=True).order_by('-download_count')[:5].values(
                'id', 'title', 'download_count', 'subject__name'
            )
        }
        return JsonResponse({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
