from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'lms'

urlpatterns = [
    # Public pages
    path('', views.loading_page, name='loading_page'),
    path('home/', views.grade_level_dashboard, name='home'),  # Backward compatibility
    path('dashboard/', views.grade_level_dashboard, name='grade_level_dashboard'),
    path('summary/', views.summary, name='summary'),
    path('education-level/<int:level_id>/', views.education_level_dashboard, name='education_level_dashboard'),
    path('grade/<int:grade_id>/', views.grade_dashboard, name='grade_dashboard'),
    path('subject/<int:grade_id>/<int:subject_id>/', views.subject_dashboard, name='subject_dashboard'),
    path('view/<int:resource_id>/', views.view_resource, name='view_resource'),
    path('download/<int:resource_id>/', views.download_resource, name='download_resource'),
    path('search/', views.search, name='search'),
    path('my-downloads/', views.my_downloads, name='my_downloads'),
    path('my-uploads/', views.my_uploads, name='my_uploads'),
    path('category/<int:category_id>/', views.category_dashboard, name='category_dashboard'),
    path('resources/', views.resource_list, name='resource_list'),
    path('debug-grades/', views.debug_grades, name='debug_grades'),
    path('error/', views.error, name='error'),

    # Upload page
    path('upload/', views.upload_resource, name='upload_resource'),

    # Admin management pages
    path('superuser/', views.superuser_dashboard, name='superuser_dashboard'),
    path('admin/add-education-level/', views.admin_add_education_level, name='admin_add_education_level'),
    path('admin/add-category/', views.admin_add_category, name='admin_add_category'),
    path('admin/add-grade/', views.admin_add_grade, name='admin_add_grade'),
    path('admin/add-subject/', views.admin_add_subject, name='admin_add_subject'),
    path('admin/add-resource-type/', views.admin_add_resource_type, name='admin_add_resource_type'),
    path('admin/add-pathway/', views.admin_add_pathway, name='admin_add_pathway'),

    # AJAX API endpoints for admin interface
    path('admin/get-grades/', views.admin_get_grades, name='admin_get_grades'),
    path('admin/get-grade/', views.admin_get_grade, name='admin_get_grade'),
    path('admin/edit-grade/', views.admin_edit_grade, name='admin_edit_grade'),
    path('admin/delete-grade/', views.admin_delete_grade, name='admin_delete_grade'),
    path('admin/get-categories/', views.admin_get_categories, name='admin_get_categories'),
    path('admin/get-category/', views.admin_get_category, name='admin_get_category'),
    path('admin/edit-category/', views.admin_edit_category, name='admin_edit_category'),
    path('admin/delete-category/', views.admin_delete_category, name='admin_delete_category'),
    path('admin/get-subjects/', views.admin_get_subjects, name='admin_get_subjects'),
    path('admin/get-subject/', views.admin_get_subject, name='admin_get_subject'),
    path('admin/edit-subject/', views.admin_edit_subject, name='admin_edit_subject'),
    path('admin/delete-subject/', views.admin_delete_subject, name='admin_delete_subject'),
    path('admin/get-resource-types/', views.admin_get_resource_types, name='admin_get_resource_types'),
    path('admin/get-resource-type/', views.admin_get_resource_type, name='admin_get_resource_type'),
    path('admin/edit-resource-type/', views.admin_edit_resource_type, name='admin_edit_resource_type'),
    path('admin/delete-resource-type/', views.admin_delete_resource_type, name='admin_delete_resource_type'),
    path('admin/get-pathways/', views.admin_get_pathways, name='admin_get_pathways'),
    path('admin/get-pathway/', views.admin_get_pathway, name='admin_get_pathway'),
    path('admin/edit-pathway/', views.admin_edit_pathway, name='admin_edit_pathway'),
    path('admin/delete-pathway/', views.admin_delete_pathway, name='admin_delete_pathway'),
    path('admin/get-education-levels/', views.admin_get_education_levels, name='admin_get_education_levels'),
    path('admin/get-education-level/', views.admin_get_education_level, name='admin_get_education_level'),
    path('admin/edit-education-level/', views.admin_edit_education_level, name='admin_edit_education_level'),
    path('admin/delete-education-level/', views.admin_delete_education_level, name='admin_delete_education_level'),
    path('admin/get-resource/', views.admin_get_resource, name='admin_get_resource'),
    path('admin/edit-resource/', views.edit_resource, name='admin_edit_resource'),
    path('admin/delete-resource/', views.delete_resource, name='admin_delete_resource'),
    path('admin/toggle-download/', views.admin_toggle_download, name='admin_toggle_download'),

    # CRUD operation pages for editing and deleting
    path('resource/edit/<int:resource_id>/', views.edit_resource, name='edit_resource'),
    path('resource/delete/<int:resource_id>/', views.delete_resource, name='delete_resource'),
    path('category/edit/<int:category_id>/', views.admin_edit_category, name='edit_category'),
    path('category/delete/<int:category_id>/', views.admin_delete_category, name='delete_category'),
    path('grade/edit/<int:grade_id>/', views.admin_edit_grade, name='edit_grade'),
    path('grade/delete/<int:grade_id>/', views.admin_delete_grade, name='delete_grade'),
    path('subject/edit/<int:subject_id>/', views.admin_edit_subject, name='edit_subject'),
    path('subject/delete/<int:subject_id>/', views.admin_delete_subject, name='delete_subject'),
    path('education-level/edit/<int:education_level_id>/', views.admin_edit_education_level, name='edit_education_level'),
    path('education-level/delete/<int:education_level_id>/', views.admin_delete_education_level, name='delete_education_level'),
    path('pathway/edit/<int:pathway_id>/', views.admin_edit_pathway, name='edit_pathway'),
    path('pathway/delete/<int:pathway_id>/', views.admin_delete_pathway, name='delete_pathway'),

    # Loading and success pages
    path('loading/', views.loading_page, name='loading_page'),
    path('success/upload/<int:resource_id>/', views.success_page, name='success_upload'),
    path('success/delete/<str:content_type>/<int:content_id>/', views.success_page, name='success_delete'),
    path('success/update/<str:content_type>/<int:content_id>/', views.success_page, name='success_update'),
    path('success/signup/', views.success_page, name='success_signup'),
    path('success/login/', views.success_page, name='success_login'),
    path('success/logout/', views.success_page, name='success_logout'),


    path('pathways/<int:level_id>/', views.pathways_dashboard, name='pathways_dashboard'),
    path('pathway/<int:pathway_id>/subjects/', views.pathway_subjects, name='pathway_subjects'),

    path('education-level/<int:level_id>/', views.education_level_dashboard, name='education_level_dashboard'),
    path('grade/<int:grade_id>/pathways/', views.grade_pathways_dashboard, name='grade_pathways_dashboard'),
    path('pathway/<int:pathway_id>/subjects/', views.pathway_subjects, name='pathway_subjects'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'lms.views.page_not_found'
handler500 = 'lms.views.server_error'