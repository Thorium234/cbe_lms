$(document).ready(function() {
    $('.edit-resource').click(function(e) {
        e.preventDefault();
        const resourceId = $(this).data('id');
        $.get(window.urls.getResource + '?id=' + resourceId, function(data) {
            $('#edit-resource-id').val(data.resource.id);
            $('#edit-title').val(data.resource.title);
            $('#edit-grade').val(data.resource.grade_id);
            $('#edit-subject').empty().append('<option value="">Select Subject</option>');
            $.each(data.subjects, function(i, subject) {
                $('#edit-subject').append(`<option value="${subject.id}" ${subject.id == data.resource.subject_id ? 'selected' : ''}>${subject.name}</option>`);
            });
            $('#edit-resource-type').val(data.resource.resource_type);
            $('#edit-resource-modal').removeClass('hidden');
        }).fail(function() {
            alert('Failed to load resource data.');
        });
    });

    $('.delete-resource').click(function(e) {
        e.preventDefault();
        if (confirm('Are you sure you want to delete this resource?')) {
            const resourceId = $(this).data('id');
            $.post(window.urls.deleteResource, {
                id: resourceId,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            }, function(data) {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            }).fail(function() {
                alert('Failed to delete resource.');
            });
        }
    });

    $('.toggle-download').change(function() {
        const resourceId = $(this).data('id');
        const allowDownload = $(this).is(':checked');
        $.post(window.urls.toggleDownload, {
            id: resourceId,
            allow_download: allowDownload,
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
        }, function(data) {
            if (!data.success) {
                alert('Error: ' + data.error);
            }
        }).fail(function() {
            alert('Failed to update download permission.');
        });
    });

    $('#edit-grade').change(function() {
        const gradeId = $(this).val();
        $('#edit-subject').empty().append('<option value="">Select Subject</option>');
        if (gradeId) {
            $.get(window.urls.getSubjects + '?grade_id=' + gradeId, function(data) {
                $.each(data.subjects, function(i, subject) {
                    $('#edit-subject').append(`<option value="${subject.id}">${subject.name}</option>`);
                });
            });
        }
    });

    $('#edit-resource-form').submit(function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        $.ajax({
            url: window.urls.editResource,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
            },
            success: function(data) {
                if (data.success) {
                    $('#edit-resource-modal').addClass('hidden');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            },
            error: function() {
                alert('Failed to update resource.');
            }
        });
    });

    $('#cancel-edit-resource').click(function() {
        $('#edit-resource-modal').addClass('hidden');
    });
});