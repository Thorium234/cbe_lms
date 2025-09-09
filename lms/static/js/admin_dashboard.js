$(document).ready(function() {
    // Helper function to show notifications
    function showNotification(message, type = 'info') {
        // Remove any existing notifications
        $('.notification').remove();
        
        // Create notification element
        const notification = $(`
            <div class="notification fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg max-w-md z-50 
                       ${type === 'success' ? 'bg-green-500 text-white' : 
                         type === 'error' ? 'bg-red-500 text-white' : 
                         'bg-blue-500 text-white'} 
                       flex items-center transition-all duration-300 transform translate-x-full">
                <span>${message}</span>
                <button class="ml-4 text-white opacity-70 hover:opacity-100">×</button>
            </div>
        `);
        
        $('body').append(notification);
        
        // Animate in
        setTimeout(() => {
            notification.removeClass('translate-x-full');
        }, 100);
        
        // Auto-dismiss after 5 seconds (except for errors)
        if (type !== 'error') {
            setTimeout(() => {
                notification.addClass('translate-x-full');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
        
        // Close button
        notification.find('button').click(function() {
            notification.addClass('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        });
    }

    // Show loading state
    function showLoading(element) {
        const originalContent = element.html();
        element.data('original-content', originalContent);
        element.html('<i class="fas fa-spinner fa-spin mr-2"></i>Processing...');
        element.prop('disabled', true);
        return originalContent;
    }

    // Hide loading state
    function hideLoading(element, originalContent) {
        element.html(originalContent);
        element.prop('disabled', false);
    }

    // Global AJAX error handler
    $(document).ajaxError(function(event, jqxhr, settings, thrownError) {
        if (jqxhr.status === 403) {
            showNotification('Permission denied. Please log in.', 'error');
        } else if (jqxhr.status === 404) {
            showNotification('Resource not found.', 'error');
        } else if (jqxhr.status === 500) {
            showNotification('Server error. Please try again later.', 'error');
        } else {
            showNotification('An error occurred: ' + thrownError, 'error');
        }
    });

    // Category Management
    $('#add-category-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.addCategory,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    showNotification('Category added successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to add category. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.edit-category').click(function(e) {
        e.preventDefault();
        const categoryId = $(this).data('id');
        
        // Show loading state
        const button = $(this);
        const originalContent = button.html();
        button.html('<i class="fas fa-spinner fa-spin"></i>');
        button.prop('disabled', true);

        $.get(window.urls.getCategory + '?id=' + categoryId, function(data) {
            if (data.category) {
                $('#edit-category-id').val(data.category.id);
                $('#edit-category-name').val(data.category.name);
                $('#edit-category-description').val(data.category.description);
                $('#edit-category-modal').removeClass('hidden');
            } else {
                showNotification('Failed to load category data.', 'error');
            }
        }).fail(function() {
            showNotification('Failed to load category data.', 'error');
        }).always(function() {
            // Restore button state
            button.html(originalContent);
            button.prop('disabled', false);
        });
    });

    $('#edit-category-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.editCategory,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    $('#edit-category-modal').addClass('hidden');
                    showNotification('Category updated successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to update category. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.delete-category').click(function(e) {
        e.preventDefault();
        const categoryId = $(this).data('id');
        const categoryName = $(this).data('name');
        
        if (confirm(`Are you sure you want to delete the category "${categoryName}"? This action cannot be undone.`)) {
            const button = $(this);
            const originalContent = button.html();
            button.html('<i class="fas fa-spinner fa-spin"></i>');
            button.prop('disabled', true);

            $.post(window.urls.deleteCategory, {
                id: categoryId,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            }, function(data) {
                if (data.success) {
                    showNotification('Category deleted successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    showNotification('Error: ' + data.error, 'error');
                    button.html(originalContent);
                    button.prop('disabled', false);
                }
            }).fail(function() {
                showNotification('Failed to delete category. Please try again.', 'error');
                button.html(originalContent);
                button.prop('disabled', false);
            });
        }
    });

    // Grade Management
    $('#add-grade-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.addGrade,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    showNotification('Grade added successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to add grade. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.edit-grade').click(function(e) {
        e.preventDefault();
        const gradeId = $(this).data('id');
        
        const button = $(this);
        const originalContent = button.html();
        button.html('<i class="fas fa-spinner fa-spin"></i>');
        button.prop('disabled', true);

        $.get(window.urls.getGrade + '?id=' + gradeId, function(data) {
            if (data.grade) {
                $('#edit-grade-id').val(data.grade.id);
                $('#edit-grade-name').val(data.grade.name);
                $('#edit-grade-description').val(data.grade.description);
                $('#edit-grade-modal').removeClass('hidden');
            } else {
                showNotification('Failed to load grade data.', 'error');
            }
        }).fail(function() {
            showNotification('Failed to load grade data.', 'error');
        }).always(function() {
            button.html(originalContent);
            button.prop('disabled', false);
        });
    });

    $('#edit-grade-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.editGrade,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    $('#edit-grade-modal').addClass('hidden');
                    showNotification('Grade updated successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to update grade. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.delete-grade').click(function(e) {
        e.preventDefault();
        const gradeId = $(this).data('id');
        const gradeName = $(this).data('name');
        
        if (confirm(`Are you sure you want to delete the grade "${gradeName}"? This action cannot be undone.`)) {
            const button = $(this);
            const originalContent = button.html();
            button.html('<i class="fas fa-spinner fa-spin"></i>');
            button.prop('disabled', true);

            $.post(window.urls.deleteGrade, {
                id: gradeId,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            }, function(data) {
                if (data.success) {
                    showNotification('Grade deleted successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    showNotification('Error: ' + data.error, 'error');
                    button.html(originalContent);
                    button.prop('disabled', false);
                }
            }).fail(function() {
                showNotification('Failed to delete grade. Please try again.', 'error');
                button.html(originalContent);
                button.prop('disabled', false);
            });
        }
    });

    // Subject Management
    $('#add-subject-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.addSubject,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    showNotification('Subject added successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else if (errorData.grade) {
                            errorMessage += errorData.grade[0];
                        } else if (errorData.category) {
                            errorMessage += errorData.category[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to add subject. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.edit-subject').click(function(e) {
        e.preventDefault();
        const subjectId = $(this).data('id');
        
        const button = $(this);
        const originalContent = button.html();
        button.html('<i class="fas fa-spinner fa-spin"></i>');
        button.prop('disabled', true);

        $.get(window.urls.getSubject + '?id=' + subjectId, function(data) {
            if (data.subject) {
                $('#edit-subject-id').val(data.subject.id);
                $('#edit-subject-name').val(data.subject.name);
                $('#edit-subject-grade').val(data.subject.grade_id);
                $('#edit-subject-category').val(data.subject.category_id);
                $('#edit-subject-modal').removeClass('hidden');
            } else {
                showNotification('Failed to load subject data.', 'error');
            }
        }).fail(function() {
            showNotification('Failed to load subject data.', 'error');
        }).always(function() {
            button.html(originalContent);
            button.prop('disabled', false);
        });
    });

    $('#edit-subject-form').submit(function(e) {
        e.preventDefault();
        const form = $(this);
        const submitBtn = form.find('button[type="submit"]');
        const originalContent = showLoading(submitBtn);

        const formData = new FormData(this);
        
        $.ajax({
            url: window.urls.editSubject,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    $('#edit-subject-modal').addClass('hidden');
                    showNotification('Subject updated successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    let errorMessage = 'Error: ';
                    try {
                        const errorData = JSON.parse(data.error);
                        if (errorData.name) {
                            errorMessage += errorData.name[0];
                        } else if (errorData.grade) {
                            errorMessage += errorData.grade[0];
                        } else if (errorData.category) {
                            errorMessage += errorData.category[0];
                        } else {
                            errorMessage += data.error;
                        }
                    } catch (e) {
                        errorMessage += data.error;
                    }
                    showNotification(errorMessage, 'error');
                    hideLoading(submitBtn, originalContent);
                }
            },
            error: function() {
                showNotification('Failed to update subject. Please try again.', 'error');
                hideLoading(submitBtn, originalContent);
            }
        });
    });

    $('.delete-subject').click(function(e) {
        e.preventDefault();
        const subjectId = $(this).data('id');
        const subjectName = $(this).data('name');
        
        if (confirm(`Are you sure you want to delete the subject "${subjectName}"? This action cannot be undone.`)) {
            const button = $(this);
            const originalContent = button.html();
            button.html('<i class="fas fa-spinner fa-spin"></i>');
            button.prop('disabled', true);

            $.post(window.urls.deleteSubject, {
                id: subjectId,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            }, function(data) {
                if (data.success) {
                    showNotification('Subject deleted successfully!', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    showNotification('Error: ' + data.error, 'error');
                    button.html(originalContent);
                    button.prop('disabled', false);
                }
            }).fail(function() {
                showNotification('Failed to delete subject. Please try again.', 'error');
                button.html(originalContent);
                button.prop('disabled', false);
            });
        }
    });

    // Close modals when clicking outside
    $(document).click(function(e) {
        if ($(e.target).hasClass('modal')) {
            $(e.target).addClass('hidden');
        }
    });

    // Close modals with escape key
    $(document).keydown(function(e) {
        if (e.key === 'Escape') {
            $('.modal').addClass('hidden');
        }
    });
});