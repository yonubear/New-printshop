/**
 * Simple Signature Pad - A lightweight digital signature for the Print Shop Management System
 * Provides a reliable, simplified signature capture and photo capture functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Simple Signature JS loaded");
    
    // Elements for signature pad
    const canvasContainer = document.getElementById('signature-pad-container');
    const canvas = document.getElementById('signature-pad');
    const clearButton = document.getElementById('clear-signature');
    const signatureDataInput = document.getElementById('signature-data');
    
    // Elements for camera
    const cameraContainer = document.getElementById('camera-container');
    const cameraFeed = document.getElementById('camera-feed');
    const cameraOutput = document.getElementById('camera-output');
    const captureButton = document.getElementById('capture-photo');
    const retakeButton = document.getElementById('retake-photo');
    const photoDataInput = document.getElementById('photo-data');
    
    // Form elements
    const pickupForm = document.getElementById('pickup-form');
    const methodOptions = document.querySelectorAll('.method-option');

    // Set up the canvas for drawing
    if (canvas && canvas.getContext) {
        // Set canvas dimensions
        resizeCanvas();
        
        // Canvas variables
        const ctx = canvas.getContext('2d');
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        
        // Set initial canvas state
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = '#000000';
        
        // Setup color picker
        const colorOptions = document.querySelectorAll('.color-option');
        if (colorOptions) {
            colorOptions.forEach(option => {
                option.addEventListener('click', function() {
                    colorOptions.forEach(opt => opt.classList.remove('active'));
                    this.classList.add('active');
                    const color = this.getAttribute('data-color');
                    ctx.strokeStyle = color;
                });
            });
        }
        
        // Drawing functions
        function startDrawing(e) {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            [lastX, lastY] = [
                e.clientX - rect.left, 
                e.clientY - rect.top
            ];
        }
        
        function draw(e) {
            if (!isDrawing) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(x, y);
            ctx.stroke();
            
            [lastX, lastY] = [x, y];
        }
        
        function stopDrawing() {
            isDrawing = false;
        }
        
        // Touch events
        function handleTouchStart(e) {
            if (e.touches.length !== 1) return;
            e.preventDefault();
            
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        }
        
        function handleTouchMove(e) {
            if (e.touches.length !== 1) return;
            e.preventDefault();
            
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        }
        
        function handleTouchEnd(e) {
            e.preventDefault();
            const mouseEvent = new MouseEvent('mouseup', {});
            canvas.dispatchEvent(mouseEvent);
        }
        
        // Clear function
        function clearCanvas() {
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        
        // Check if the signature pad has content
        function isSignatureEmpty() {
            const pixelBuffer = new Uint32Array(
                ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
            );
            
            // Find a non-white, non-transparent pixel
            return !pixelBuffer.some(color => color !== 0 && color !== 0xffffffff);
        }
        
        // Ensure the canvas size fits the container
        function resizeCanvas() {
            if (!canvas || !canvasContainer) return;
            
            const width = canvasContainer.clientWidth;
            const height = canvasContainer.clientHeight;
            
            canvas.width = width;
            canvas.height = height;
            
            // Reset to white background after resize
            if (canvas.getContext) {
                const ctx = canvas.getContext('2d');
                ctx.fillStyle = 'white';
                ctx.fillRect(0, 0, width, height);
            }
        }
        
        // Add event listeners for drawing
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);
        
        // Touch support
        canvas.addEventListener('touchstart', handleTouchStart);
        canvas.addEventListener('touchmove', handleTouchMove);
        canvas.addEventListener('touchend', handleTouchEnd);
        
        // Clear button
        if (clearButton) {
            clearButton.addEventListener('click', clearCanvas);
        }
        
        // Window resize handler
        window.addEventListener('resize', resizeCanvas);
    } else {
        console.error("Canvas context not available");
    }
    
    // Camera functionality
    let stream = null;
    
    function initCamera() {
        if (!cameraContainer || !cameraFeed) {
            console.error("Camera elements not found");
            return;
        }
        
        // Display the camera container
        cameraContainer.style.display = 'block';
        
        // If already initialized, just show it
        if (stream) {
            cameraFeed.style.display = 'block';
            cameraOutput.style.display = 'none';
            return;
        }
        
        // Access the camera
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'environment' }, 
                audio: false 
            })
            .then(function(mediaStream) {
                stream = mediaStream;
                cameraFeed.srcObject = stream;
                cameraFeed.style.display = 'block';
                cameraOutput.style.display = 'none';
                captureButton.style.display = 'inline-block';
                retakeButton.style.display = 'none';
                console.log("Camera initialized successfully");
            })
            .catch(function(error) {
                console.error('Error accessing camera:', error);
                alert('Could not access camera. Please ensure you have given camera permission to this site.');
            });
        } else {
            console.error("getUserMedia not supported");
            alert('Your browser does not support camera access. Please try a different browser.');
        }
    }
    
    // Capture photo
    if (captureButton) {
        captureButton.addEventListener('click', function() {
            if (!cameraFeed || !cameraFeed.videoWidth) {
                console.error("Video stream not ready");
                alert("Camera is not ready yet. Please wait a moment and try again.");
                return;
            }
            
            const canvas = document.createElement('canvas');
            canvas.width = cameraFeed.videoWidth;
            canvas.height = cameraFeed.videoHeight;
            
            const context = canvas.getContext('2d');
            context.drawImage(cameraFeed, 0, 0, canvas.width, canvas.height);
            
            // Get image as data URL
            const imageDataUrl = canvas.toDataURL('image/png');
            
            // Set the photo data
            if (photoDataInput) {
                photoDataInput.value = imageDataUrl;
            }
            
            // Display the captured image
            if (cameraOutput) {
                cameraOutput.src = imageDataUrl;
                cameraOutput.style.display = 'block';
                cameraFeed.style.display = 'none';
            }
            
            // Toggle buttons
            if (captureButton && retakeButton) {
                captureButton.style.display = 'none';
                retakeButton.style.display = 'inline-block';
            }
            
            console.log("Photo captured successfully");
        });
    }
    
    // Retake photo
    if (retakeButton) {
        retakeButton.addEventListener('click', function() {
            if (cameraFeed && cameraOutput) {
                cameraFeed.style.display = 'block';
                cameraOutput.style.display = 'none';
            }
            
            if (captureButton && retakeButton) {
                captureButton.style.display = 'inline-block';
                retakeButton.style.display = 'none';
            }
            
            if (photoDataInput) {
                photoDataInput.value = '';
            }
            
            console.log("Reset for retaking photo");
        });
    }
    
    // Method selector
    if (methodOptions && methodOptions.length > 0) {
        methodOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Remove active class from all options
                methodOptions.forEach(opt => opt.classList.remove('active'));
                
                // Add active class to clicked option
                this.classList.add('active');
                
                // Hide all method contents
                const methodContents = document.querySelectorAll('.method-content');
                if (methodContents) {
                    methodContents.forEach(content => {
                        content.style.display = 'none';
                    });
                }
                
                // Show selected method content
                const method = this.getAttribute('data-method');
                const methodEl = document.getElementById(method + '-method');
                if (methodEl) {
                    methodEl.style.display = 'block';
                }
                
                // Initialize camera if photo method is selected
                if (method === 'photo') {
                    initCamera();
                }
            });
        });
    }
    
    // Form submission
    if (pickupForm) {
        pickupForm.addEventListener('submit', function(e) {
            console.log("Form submission handler called");
            
            // Prevent default submission to handle data
            e.preventDefault();
            
            // Get active method
            const activeOption = document.querySelector('.method-option.active');
            if (!activeOption) {
                console.error("No active method found");
                alert('Please select a confirmation method (signature or photo).');
                return false;
            }
            
            const activeMethod = activeOption.getAttribute('data-method');
            console.log("Active method:", activeMethod);
            
            if (activeMethod === 'signature') {
                // Check if canvas exists
                if (!canvas || !canvas.getContext) {
                    console.error("Canvas not available");
                    alert('Signature pad not available. Please try reloading the page.');
                    return false;
                }
                
                // Check if signature is empty
                if (isSignatureEmpty()) {
                    console.log("Signature is empty");
                    alert('Please provide a signature.');
                    return false;
                }
                
                // Get signature data
                const signatureImage = canvas.toDataURL('image/png');
                
                // Set signature data in hidden field
                if (signatureDataInput) {
                    signatureDataInput.value = signatureImage;
                    console.log("Signature data set successfully");
                } else {
                    console.error("Signature data input not found");
                    alert('There was a problem processing your signature. Please try again.');
                    return false;
                }
            } else if (activeMethod === 'photo') {
                // Check for photo data
                if (!photoDataInput || !photoDataInput.value) {
                    console.log("No photo data");
                    alert('Please capture a photo.');
                    return false;
                }
                
                // Copy photo data to signature data field for server processing
                if (signatureDataInput) {
                    signatureDataInput.value = photoDataInput.value;
                    console.log("Photo data copied to signature data field");
                } else {
                    console.error("Signature data input not found");
                    alert('There was a problem processing your photo. Please try again.');
                    return false;
                }
            } else {
                console.error("Unknown method:", activeMethod);
                alert('Please select a valid confirmation method.');
                return false;
            }
            
            // Final check to ensure we have data
            if (!signatureDataInput || !signatureDataInput.value) {
                console.error("No signature data available");
                alert('Missing confirmation data. Please try again.');
                return false;
            }
            
            // Submit the form
            console.log("Form validation passed, submitting form");
            this.submit();
        });
    }
    
    // Clean up camera when leaving page
    window.addEventListener('beforeunload', function() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
});