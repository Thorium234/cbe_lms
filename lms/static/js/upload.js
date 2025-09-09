$(document).ready(function() {
    const dropZone = $('#drop-zone');
    const fileInput = $('#id_file');
    const fileNameDisplay = $('#file-name');
    const progressBar = $('#progress-bar');
    const progressBarContainer = $('#progress-bar-container');
    const progressText = $('#progress-text');
    const uploadForm = $('#upload-form');
    const gradeSelect = $('#id_grade');
    const subjectSelect = $('#id_subject');
    const selectFileBtn = $('#select-file-btn');

    // Validate file type and size
    function validateFile(file) {
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'video/mp4',
            'video/quicktime',
            'video/x-msvideo'
        ];
        const maxSize = 314572800; // 300MB
        const fileExt = file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(file.type) && !['pdf', 'doc', 'docx', 'mp4', 'mov', 'avi'].includes(fileExt)) {
            alert('Invalid file type. Allowed: PDF, DOC, DOCX, MP4, MOV, AVI');
            return false;
        }
        if (file.size > maxSize) {
            alert('File too large. Maximum size: 300MB');
            return false;
        }
        return true;
    }

    // Drag and drop events
    dropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('border-green-500');
    });

    dropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('border-green-500');
    });

    dropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('border-green-500');
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0 && validateFile(files[0])) {
            fileInput[0].files = files;
            fileNameDisplay.text(files[0].name);
            console.log('Dropped file:', files[0].name, 'Type:', files[0].type, 'Size:', files[0].size);
        }
    });

    // File input change
    fileInput.on('change', function() {
        if (this.files.length > 0 && validateFile(this.files[0])) {
            fileNameDisplay.text(this.files[0].name);
            console.log('Selected file:', this.files[0].name, 'Type:', this.files[0].type, 'Size:', this.files[0].size);
        } else {
            fileInput.val('');
            fileNameDisplay.text('Drag and drop a file here or click to select');
        }
    });

    // Select file button
    selectFileBtn.on('click', function() {
        fileInput.click();
    });

    // Populate subjects
    gradeSelect.on('change', function() {
        const gradeId = $(this).val();
        subjectSelect.empty().append('<option value="">Select Subject</option>');
        if (gradeId) {
            $.ajax({
                url: window.urls.getSubjects,
                type: 'GET',
                data: { grade_id: gradeId },
                success: function(data) {
                    console.log('Subjects loaded:', data);
                    if (data.success) {
                        $.each(data.subjects, function(i, subject) {
                            subjectSelect.append(`<option value="${subject.id}">${subject.name}</option>`);
                        });
                    } else {
                        console.error('Failed to load subjects:', data.error);
                        alert('Failed to load subjects: ' + data.error);
                    }
                },
                error: function(xhr) {
                    console.error('Failed to load subjects:', xhr.status, xhr.statusText, xhr.responseText);
                    let errorMsg = 'Unknown error';
                    if (xhr.status === 404) {
                        errorMsg = 'Subjects endpoint not found. Check URL configuration.';
                    } else if (xhr.responseJSON && xhr.responseJSON.error) {
                        errorMsg = xhr.responseJSON.error;
                    }
                    alert('Failed to load subjects: ' + errorMsg);
                }
            });
        }
    });

    // Form submission
    uploadForm.on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        if (!formData.get('file')) {
            alert('Please select a file.');
            return;
        }
        if (!formData.get('subject')) {
            alert('Please select a subject.');
            return;
        }
        if (!formData.get('title')) {
            alert('Please enter a title.');
            return;
        }

        progressBarContainer.removeClass('hidden');
        progressBar.css('width', '0%');
        progressText.text('Uploading...');

        $.ajax({
            url: window.urls.uploadResource,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            xhr: function() {
                const xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener('progress', function(evt) {
                    if (evt.lengthComputable) {
                        const percentComplete = (evt.loaded / evt.total) * 100;
                        progressBar.css('width', percentComplete + '%');
                        progressText.text(`Uploading... ${Math.round(percentComplete)}%`);
                    }
                }, false);
                return xhr;
            },
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $('[name=csrfmiddlewaretoken]').val());
                console.log('Uploading to:', window.urls.uploadResource, 'File:', formData.get('file').name);
            },
            success: function(data) {
                console.log('Upload response:', data);
                if (data.success) {
                    alert('File uploaded successfully!');
                    window.location.href = data.redirect_url;
                } else {
                    console.error('Upload error:', data.error);
                    alert('Upload failed: ' + data.error);
                    progressBarContainer.addClass('hidden');
                }
            },
            error: function(xhr) {
                console.error('AJAX error:', xhr.status, xhr.statusText, xhr.responseText);
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'Server error';
                alert('Upload failed: ' + errorMsg);
                progressBarContainer.addClass('hidden');
            }
        });
    });
});