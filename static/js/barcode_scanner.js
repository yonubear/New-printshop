/**
 * Barcode Scanner Functionality for Order/Quote Numbers
 */

let scannerIsRunning = false;

/**
 * Play a beep sound using Web Audio API
 */
function playBeepSound() {
    try {
        // Create audio context
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        // Configure oscillator
        oscillator.type = 'square';
        oscillator.frequency.value = 800; // Set frequency to 800Hz
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        // Set volume
        gainNode.gain.value = 0.3;

        // Start and stop the beep
        const startTime = audioContext.currentTime;
        oscillator.start(startTime);
        oscillator.stop(startTime + 0.15); // Beep for 150ms
    } catch (error) {
        console.error('Error playing beep sound:', error);
    }
}

/**
 * Initialize barcode scanner
 */
function initBarcodeScanner() {
    // Set up barcode scan buttons
    document.querySelectorAll('.barcode-scan-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const targetInput = document.getElementById(this.dataset.target);
            openScannerModal(targetInput);
        });
    });

    // Close scanner modal when clicking on close button
    document.getElementById('closeScannerModal').addEventListener('click', function() {
        closeScannerModal();
    });
}

/**
 * Open the scanner modal and initialize camera
 */
function openScannerModal(targetInput) {
    const modal = document.getElementById('barcodeModal');
    modal.classList.add('show');
    modal.style.display = 'block';
    document.body.classList.add('modal-open');
    
    const modalBackdrop = document.createElement('div');
    modalBackdrop.className = 'modal-backdrop fade show';
    document.body.appendChild(modalBackdrop);
    
    // Store the target input in a data attribute
    modal.dataset.targetInput = targetInput.id;
    
    // Start the scanner
    startScanner();
}

/**
 * Close the scanner modal and stop camera
 */
function closeScannerModal() {
    const modal = document.getElementById('barcodeModal');
    modal.classList.remove('show');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    
    // Remove modal backdrop
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    
    // Stop scanner if running
    if (scannerIsRunning) {
        Quagga.stop();
        scannerIsRunning = false;
    }
}

/**
 * Start the barcode scanner
 */
function startScanner() {
    if (scannerIsRunning) {
        Quagga.stop();
    }

    const scannerContainer = document.getElementById('scanner-container');
    scannerContainer.innerHTML = ''; // Clear previous instances

    Quagga.init({
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: scannerContainer,
            constraints: {
                width: 480,
                height: 320,
                facingMode: "environment" // Use the back camera
            },
        },
        frequency: 2,
        decoder: {
            readers: [
                "code_128_reader",
                "ean_reader",
                "ean_8_reader",
                "code_39_reader",
                "code_39_vin_reader",
                "codabar_reader",
                "upc_reader",
                "upc_e_reader",
                "i2of5_reader"
            ],
            debug: {
                showCanvas: true,
                showPatches: true,
                showFoundPatches: true,
                showSkeleton: true,
                showLabels: true,
                showPatchLabels: true,
                showRemainingPatchLabels: true,
                boxFromPatches: {
                    showTransformed: true,
                    showTransformedBox: true,
                    showBB: true
                }
            }
        },
    }, function(err) {
        if (err) {
            console.error(err);
            alert("Error initializing the barcode scanner: " + err);
            closeScannerModal();
            return;
        }

        console.log("Barcode scanner is initialized. Camera should be active now.");
        scannerIsRunning = true;
        Quagga.start();
    });

    // When a barcode is detected
    Quagga.onDetected(function(result) {
        if (result && result.codeResult) {
            const code = result.codeResult.code;
            console.log("Barcode detected:", code);
            
            const modal = document.getElementById('barcodeModal');
            const targetInputId = modal.dataset.targetInput;
            const targetInput = document.getElementById(targetInputId);
            
            if (targetInput) {
                targetInput.value = code;
                // Create a change event to trigger any event listeners
                const event = new Event('change', { bubbles: true });
                targetInput.dispatchEvent(event);
            }
            
            // Play a success sound using Web Audio API
            playBeepSound();
            
            // Close the scanner
            closeScannerModal();
        }
    });
}

// Initialize scanner when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if necessary elements exist
    if (document.querySelector('.barcode-scan-btn')) {
        initBarcodeScanner();
    }
});