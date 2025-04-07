/**
 * Drag and Drop File Upload with Material Preview
 * Print Order Management System
 */

document.addEventListener('DOMContentLoaded', function() {
    initDragDropUpload();
});

/**
 * Initialize drag and drop file upload functionality
 */
function initDragDropUpload() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-upload');
    const filePreview = document.getElementById('file-preview');
    const materialPreview = document.getElementById('material-preview');
    
    if (!dropArea || !fileInput) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    // Handle file selection via file input
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    // Helper functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    function handleFiles(files) {
        if (files.length === 0) return;
        
        // Clear previous previews
        filePreview.innerHTML = '';
        if (materialPreview) materialPreview.innerHTML = '';
        
        // If more than one file, show count
        if (files.length > 1) {
            const multiFileAlert = document.createElement('div');
            multiFileAlert.classList.add('alert', 'alert-warning', 'mb-3');
            multiFileAlert.innerHTML = `<i class="bi bi-exclamation-triangle-fill me-2"></i> Multiple files selected. Only the first file will be used.`;
            filePreview.appendChild(multiFileAlert);
        }
        
        // Process the first file
        const file = files[0];
        previewFile(file);
        
        // Set the file to the file input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        // Trigger change event on file input
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
        
        // Show material estimation if available
        if (materialPreview) {
            estimateMaterialUsage(file);
        }
    }
    
    function previewFile(file) {
        // Create file info card
        const fileCard = document.createElement('div');
        fileCard.classList.add('card', 'mb-3');
        
        const fileHeader = document.createElement('div');
        fileHeader.classList.add('card-header', 'd-flex', 'align-items-center', 'gap-2');
        
        // File icon based on type
        let fileIcon = 'bi-file-earmark';
        if (file.type.match('image.*')) {
            fileIcon = 'bi-file-earmark-image';
        } else if (file.type === 'application/pdf') {
            fileIcon = 'bi-file-earmark-pdf';
        } else if (file.type.match('text.*')) {
            fileIcon = 'bi-file-earmark-text';
        }
        
        fileHeader.innerHTML = `
            <i class="bi ${fileIcon} fs-4 me-2"></i>
            <div>
                <h5 class="mb-0">${file.name}</h5>
                <span class="text-muted small">${formatFileSize(file.size)}</span>
            </div>
        `;
        
        fileCard.appendChild(fileHeader);
        
        // Create card body for preview
        const fileBody = document.createElement('div');
        fileBody.classList.add('card-body');
        
        // Add preview content based on file type
        if (file.type.match('image.*')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.classList.add('img-fluid', 'rounded');
                img.style.maxHeight = '300px';
                img.src = e.target.result;
                fileBody.appendChild(img);
            };
            reader.readAsDataURL(file);
        } else if (file.type === 'application/pdf') {
            fileBody.innerHTML = `
                <div class="d-flex align-items-center justify-content-center p-3 bg-light rounded">
                    <i class="bi bi-file-earmark-pdf fs-1 text-danger me-3"></i>
                    <div>
                        <h5 class="mb-1">PDF Document</h5>
                        <p class="mb-0 text-muted">Preview will be available after upload</p>
                    </div>
                </div>
            `;
        } else {
            fileBody.innerHTML = `
                <div class="alert alert-info mb-0">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    No preview available for this file type.
                </div>
            `;
        }
        
        fileCard.appendChild(fileBody);
        filePreview.appendChild(fileCard);
    }
    
    function estimateMaterialUsage(file) {
        if (!materialPreview) return;
        
        // Clear previous content
        materialPreview.innerHTML = '';
        
        // Show loading state
        materialPreview.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="bi bi-grid-3x3-gap me-2"></i>
                        Material Estimation
                    </h5>
                </div>
                <div class="card-body">
                    <div class="material-estimation-content">
                        <div class="d-flex align-items-center p-3">
                            <div class="spinner-border text-primary me-3" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <div>
                                <h6 class="mb-1">Analyzing file...</h6>
                                <p class="text-muted mb-0">Estimating material requirements</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Simulate material analysis (in a real implementation, this would analyze the file content)
        setTimeout(function() {
            // Get the file type and based on that, show different material estimations
            let materialHTML = '';
            
            if (file.type.match('image.*')) {
                const sizeEstimate = getImageSizeEstimate(file.size);
                materialHTML = createImageMaterialEstimate(sizeEstimate);
            } else if (file.type === 'application/pdf') {
                materialHTML = createPdfMaterialEstimate();
            } else {
                materialHTML = `
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle-fill me-2"></i>
                        Material estimation not available for this file type.
                    </div>
                `;
            }
            
            document.querySelector('.material-estimation-content').innerHTML = materialHTML;
        }, 1500);
    }
    
    function getImageSizeEstimate(fileSize) {
        // Very simplified estimation just for demonstration
        if (fileSize < 500000) { // < 500KB
            return 'small';
        } else if (fileSize < 2000000) { // < 2MB
            return 'medium';
        } else {
            return 'large';
        }
    }
    
    function createImageMaterialEstimate(sizeEstimate) {
        let paperType, inkEstimate, paperCount;
        
        switch(sizeEstimate) {
            case 'small':
                paperType = 'Standard Copy Paper';
                inkEstimate = 'Low (5-10%)';
                paperCount = '1 sheet';
                break;
            case 'medium':
                paperType = 'Photo Paper';
                inkEstimate = 'Medium (20-30%)';
                paperCount = '1-2 sheets';
                break;
            case 'large':
                paperType = 'Premium Photo Paper';
                inkEstimate = 'High (40-60%)';
                paperCount = '2-4 sheets';
                break;
            default:
                paperType = 'Standard Paper';
                inkEstimate = 'Unknown';
                paperCount = 'Unknown';
        }
        
        return `
            <div class="mb-3">
                <h6 class="fw-bold">Estimated Materials:</h6>
                <div class="table-responsive">
                    <table class="table table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th>Material</th>
                                <th>Estimated Usage</th>
                                <th>Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="bg-light rounded p-2 me-2">
                                            <i class="bi bi-file-earmark text-primary"></i>
                                        </div>
                                        <span>${paperType}</span>
                                    </div>
                                </td>
                                <td>${paperCount}</td>
                                <td>$${(sizeEstimate === 'small' ? 0.10 : (sizeEstimate === 'medium' ? 0.25 : 0.50)).toFixed(2)}</td>
                            </tr>
                            <tr>
                                <td>
                                    <div class="d-flex align-items-center">
                                        <div class="bg-light rounded p-2 me-2">
                                            <i class="bi bi-droplet-fill text-dark"></i>
                                        </div>
                                        <span>Ink Usage</span>
                                    </div>
                                </td>
                                <td>${inkEstimate}</td>
                                <td>$${(sizeEstimate === 'small' ? 0.05 : (sizeEstimate === 'medium' ? 0.15 : 0.35)).toFixed(2)}</td>
                            </tr>
                        </tbody>
                        <tfoot class="table-light">
                            <tr>
                                <th colspan="2" class="text-end">Estimated Total:</th>
                                <th>$${(sizeEstimate === 'small' ? 0.15 : (sizeEstimate === 'medium' ? 0.40 : 0.85)).toFixed(2)}</th>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            </div>
            <div class="alert alert-info small mb-0">
                <i class="bi bi-info-circle-fill me-2"></i>
                This is an estimated material usage based on the file properties. Actual usage may vary based on print settings and material selection.
            </div>
        `;
    }
    
    function createPdfMaterialEstimate() {
        return `
            <div class="alert alert-warning mb-3">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                PDF analysis requires additional processing. Material estimation will be available after upload.
            </div>
            <div class="d-flex justify-content-center">
                <button class="btn btn-outline-primary btn-sm">
                    <i class="bi bi-file-earmark-pdf me-1"></i>
                    Analyze PDF Content
                </button>
            </div>
        `;
    }
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