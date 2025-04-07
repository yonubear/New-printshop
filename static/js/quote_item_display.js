/**
 * Quote Item Form Price Display
 * Adds price display elements to quote item forms
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set up tabs to update product_type when changed
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', event => {
            // Update the active form based on tab
            const targetId = event.target.getAttribute('data-bs-target').substring(1);
            if (targetId === 'regular') {
                document.querySelector('input[name="product_type"]').value = 'regular';
            } else if (targetId === 'booklet') {
                document.querySelector('input[name="product_type"]').value = 'booklet';
            } else if (targetId === 'notepad') {
                document.querySelector('input[name="product_type"]').value = 'notepad';
            }
        });
    });
    
    // Display calculated price in the UI
    const regularForm = document.getElementById('regular-print-form');
    const bookletForm = document.getElementById('booklet-form');
    const notepadForm = document.getElementById('notepad-form');
    
    // Add price display element to each form
    if (regularForm) {
        const priceSection = document.createElement('div');
        priceSection.classList.add('mb-3', 'mt-3');
        priceSection.innerHTML = `
            <div class="card">
                <div class="card-header bg-light">Price Information</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <p><strong>Unit Price:</strong> $<span id="calculated_unit_price">0.00</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Quantity:</strong> <span id="quantity_display">1</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Total Price:</strong> $<span id="calculated_price">0.00</span></p>
                        </div>
                    </div>
                </div>
            </div>`;
        regularForm.insertBefore(priceSection, regularForm.querySelector('.d-flex.justify-content-between'));
        
        // Update quantity display when quantity is changed
        const quantityInput = document.getElementById('quantity');
        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                document.getElementById('quantity_display').textContent = this.value;
            });
        }
    }
    
    if (bookletForm) {
        const priceSection = document.createElement('div');
        priceSection.classList.add('mb-3', 'mt-3');
        priceSection.innerHTML = `
            <div class="card">
                <div class="card-header bg-light">Price Information</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <p><strong>Unit Price:</strong> $<span id="booklet_calculated_unit_price">0.00</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Quantity:</strong> <span id="booklet_quantity_display">1</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Total Price:</strong> $<span id="booklet_calculated_price">0.00</span></p>
                        </div>
                    </div>
                </div>
            </div>`;
        bookletForm.insertBefore(priceSection, bookletForm.querySelector('.d-flex.justify-content-between'));
        
        // Update quantity display when quantity is changed
        const quantityInput = document.getElementById('booklet_quantity');
        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                document.getElementById('booklet_quantity_display').textContent = this.value;
            });
        }
    }
    
    if (notepadForm) {
        const priceSection = document.createElement('div');
        priceSection.classList.add('mb-3', 'mt-3');
        priceSection.innerHTML = `
            <div class="card">
                <div class="card-header bg-light">Price Information</div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <p><strong>Unit Price:</strong> $<span id="notepad_calculated_unit_price">0.00</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Quantity:</strong> <span id="notepad_quantity_display">1</span></p>
                        </div>
                        <div class="col-md-4">
                            <p><strong>Total Price:</strong> $<span id="notepad_calculated_price">0.00</span></p>
                        </div>
                    </div>
                </div>
            </div>`;
        notepadForm.insertBefore(priceSection, notepadForm.querySelector('.d-flex.justify-content-between'));
        
        // Update quantity display when quantity is changed
        const quantityInput = document.getElementById('notepad_quantity');
        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                document.getElementById('notepad_quantity_display').textContent = this.value;
            });
        }
    }
});