// Print Order Management System - File Preview JS

document.addEventListener('DOMContentLoaded', function() {
    // Initialize file preview functionality
    initFilePreview();
});

/**
 * Initialize file preview functionality
 */
function initFilePreview() {
    const previewButtons = document.querySelectorAll('.btn-preview-file');
    const previewModal = document.getElementById('filePreviewModal');
    
    if (!previewModal) return;
    
    // Initialize Bootstrap modal
    const modal = new bootstrap.Modal(previewModal);
    
    previewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const fileId = this.dataset.fileId;
            const fileName = this.dataset.fileName;
            const fileType = this.dataset.fileType;
            
            // Set modal title
            const modalTitle = previewModal.querySelector('.modal-title');
            if (modalTitle) {
                modalTitle.textContent = fileName;
            }
            
            // Clear existing preview content
            const previewContainer = previewModal.querySelector('.preview-container');
            previewContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div><p class="mt-2">Loading preview...</p></div>';
            
            // Show modal
            modal.show();
            
            // Load file preview
            loadFilePreview(fileId, previewContainer);
        });
    });
}

/**
 * Load file preview content
 */
function loadFilePreview(fileId, container) {
    fetch(`/files/${fileId}/preview`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load preview');
            }
            return response.text();
        })
        .then(html => {
            // Create a temporary element to parse the HTML
            const temp = document.createElement('div');
            temp.innerHTML = html;
            
            // Extract the preview URL from the HTML response
            const previewUrl = temp.querySelector('#preview-url')?.value;
            
            if (previewUrl) {
                // Create preview iframe
                const iframe = document.createElement('iframe');
                iframe.classList.add('file-preview-frame');
                iframe.src = previewUrl;
                
                // Clear container and add iframe
                container.innerHTML = '';
                container.appendChild(iframe);
            } else {
                throw new Error('Preview URL not found');
            }
        })
        .catch(error => {
            console.error('Error loading preview:', error);
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Error loading preview. The file may not be compatible with preview or Nextcloud preview service may be unavailable.
                </div>
                <div class="text-center mt-3">
                    <a href="/files/${fileId}/download" class="btn btn-primary">
                        <i class="bi bi-download me-2"></i>Download file instead
                    </a>
                </div>
            `;
        });
}

/**
 * Handle file uploads with preview
 */
function setupFileUploadPreview() {
    const fileInput = document.getElementById('file-upload');
    const previewContainer = document.getElementById('file-preview');
    
    if (!fileInput || !previewContainer) return;
    
    fileInput.addEventListener('change', function() {
        // Clear existing preview
        previewContainer.innerHTML = '';
        
        if (this.files && this.files[0]) {
            const file = this.files[0];
            const reader = new FileReader();
            
            // Show file info
            const fileInfo = document.createElement('div');
            fileInfo.classList.add('alert', 'alert-info', 'mt-3');
            fileInfo.innerHTML = `
                <strong>File:</strong> ${file.name}<br>
                <strong>Size:</strong> ${formatFileSize(file.size)}<br>
                <strong>Type:</strong> ${file.type || 'Unknown'}
            `;
            previewContainer.appendChild(fileInfo);
            
            // If it's an image, show image preview
            if (file.type.match('image.*')) {
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.classList.add('img-fluid', 'img-thumbnail', 'mt-2');
                    img.style.maxHeight = '300px';
                    img.src = e.target.result;
                    previewContainer.appendChild(img);
                };
                
                reader.readAsDataURL(file);
            } 
            // If it's a PDF, show PDF preview 
            else if (file.type === 'application/pdf') {
                const pdfMessage = document.createElement('div');
                pdfMessage.classList.add('alert', 'alert-success', 'mt-2');
                pdfMessage.innerHTML = `
                    <i class="bi bi-file-earmark-pdf me-2"></i>
                    PDF file selected. Preview will be available after upload.
                `;
                previewContainer.appendChild(pdfMessage);
            }
        }
    });
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Call setup file upload preview when document is ready
document.addEventListener('DOMContentLoaded', function() {
    setupFileUploadPreview();
});
