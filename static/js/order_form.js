// Print Order Management System - Order Form JS

document.addEventListener('DOMContentLoaded', function() {
    initOrderForm();
    initItemMaterials();
});

/**
 * Initialize order form functionality
 */
function initOrderForm() {
    const orderForm = document.getElementById('order-form');
    
    if (!orderForm) return;
    
    // Customer select2 initialization (if needed)
    if (typeof $.fn.select2 !== 'undefined') {
        $('.customer-select').select2({
            placeholder: 'Select a customer',
            width: '100%'
        });
    }
    
    // Due date picker initialization
    const dueDateInput = document.getElementById('due-date');
    
    if (dueDateInput) {
        // Set min date to today
        const today = new Date();
        const todayFormatted = today.toISOString().split('T')[0];
        dueDateInput.min = todayFormatted;
    }
    
    // Form validation
    orderForm.addEventListener('submit', function(e) {
        if (!validateOrderForm()) {
            e.preventDefault();
        }
    });
    
    // Dynamic item addition
    const addItemBtn = document.getElementById('add-item-btn');
    const itemsContainer = document.getElementById('items-container');
    const itemTemplate = document.getElementById('item-template');
    
    if (addItemBtn && itemsContainer && itemTemplate) {
        let itemCounter = document.querySelectorAll('.item-row').length;
        
        addItemBtn.addEventListener('click', function() {
            itemCounter++;
            
            // Clone the template
            const template = itemTemplate.content.cloneNode(true);
            const newRow = template.querySelector('.item-row');
            
            // Update IDs and names for the new item
            updateElementAttributes(newRow, 'item', itemCounter);
            
            // Add the new row
            itemsContainer.appendChild(newRow);
            
            // Setup calculation handlers
            setupItemCalculations(newRow);
            
            // Setup remove button
            const removeBtn = newRow.querySelector('.remove-item-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', function() {
                    newRow.remove();
                    recalculateOrderTotal();
                });
            }
        });
    }
}

/**
 * Update element IDs and names with new index
 */
function updateElementAttributes(container, prefix, index) {
    const elements = container.querySelectorAll('input, select, textarea');
    
    elements.forEach(element => {
        if (element.id) {
            element.id = element.id.replace(new RegExp(`${prefix}-\\d+`), `${prefix}-${index}`);
        }
        
        if (element.name) {
            element.name = element.name.replace(new RegExp(`${prefix}\\[\\d+\\]`), `${prefix}[${index}]`);
        }
    });
    
    const labels = container.querySelectorAll('label');
    labels.forEach(label => {
        if (label.htmlFor) {
            label.htmlFor = label.htmlFor.replace(new RegExp(`${prefix}-\\d+`), `${prefix}-${index}`);
        }
    });
}

/**
 * Setup calculation handlers for item row
 */
function setupItemCalculations(itemRow) {
    const quantityInput = itemRow.querySelector('.item-quantity');
    const priceInput = itemRow.querySelector('.item-price');
    const totalElement = itemRow.querySelector('.item-total');
    
    const calculateTotal = () => {
        const quantity = parseInt(quantityInput.value) || 0;
        const price = parseFloat(priceInput.value) || 0;
        const total = quantity * price;
        
        if (totalElement) {
            totalElement.textContent = `$${total.toFixed(2)}`;
            totalElement.dataset.value = total;
        }
        
        recalculateOrderTotal();
    };
    
    if (quantityInput) {
        quantityInput.addEventListener('input', calculateTotal);
    }
    
    if (priceInput) {
        priceInput.addEventListener('input', calculateTotal);
    }
}

/**
 * Recalculate order total from all items
 */
function recalculateOrderTotal() {
    const totalElements = document.querySelectorAll('.item-total');
    const orderTotalElement = document.getElementById('order-total');
    
    if (!orderTotalElement) return;
    
    let total = 0;
    
    totalElements.forEach(element => {
        total += parseFloat(element.dataset.value || 0);
    });
    
    orderTotalElement.textContent = `$${total.toFixed(2)}`;
}

/**
 * Validate order form
 */
function validateOrderForm() {
    const customerId = document.getElementById('customer-id');
    const title = document.getElementById('order-title');
    const itemRows = document.querySelectorAll('.item-row');
    
    let isValid = true;
    
    // Check customer
    if (customerId && !customerId.value) {
        highlightInvalidField(customerId, 'Please select a customer');
        isValid = false;
    }
    
    // Check title
    if (title && !title.value.trim()) {
        highlightInvalidField(title, 'Please enter an order title');
        isValid = false;
    }
    
    // Check items (if any)
    if (itemRows.length > 0) {
        itemRows.forEach(row => {
            const nameInput = row.querySelector('.item-name');
            const quantityInput = row.querySelector('.item-quantity');
            
            if (nameInput && !nameInput.value.trim()) {
                highlightInvalidField(nameInput, 'Please enter an item name');
                isValid = false;
            }
            
            if (quantityInput) {
                const quantity = parseInt(quantityInput.value);
                if (isNaN(quantity) || quantity <= 0) {
                    highlightInvalidField(quantityInput, 'Please enter a valid quantity');
                    isValid = false;
                }
            }
        });
    }
    
    return isValid;
}

/**
 * Highlight invalid field with error message
 */
function highlightInvalidField(field, message) {
    field.classList.add('is-invalid');
    
    // Check for existing error message
    let errorElement = field.nextElementSibling;
    if (!errorElement || !errorElement.classList.contains('invalid-feedback')) {
        errorElement = document.createElement('div');
        errorElement.classList.add('invalid-feedback');
        field.parentNode.insertBefore(errorElement, field.nextSibling);
    }
    
    errorElement.textContent = message;
    
    // Remove invalid status on input
    field.addEventListener('input', function() {
        this.classList.remove('is-invalid');
    }, { once: true });
}

/**
 * Initialize materials management for order items
 */
function initItemMaterials() {
    const addMaterialForms = document.querySelectorAll('.add-material-form');
    const materialPanels = document.querySelectorAll('.materials-panel');
    
    // Note: Material panel toggle buttons are now handled in main.js
    
    // Handle material type selection
    const materialSelectors = document.querySelectorAll('.material-selector');
    materialSelectors.forEach(selector => {
        // Initial state - hide or show custom fields
        const form = selector.closest('form');
        const customFields = form.querySelectorAll('.custom-material-field');
        
        // Initial setup - if custom, show fields, otherwise hide them
        if (selector.value === 'custom') {
            customFields.forEach(field => field.style.display = 'block');
        } else {
            customFields.forEach(field => field.style.display = 'none');
        }
        
        // Add change event
        selector.addEventListener('change', function() {
            const customFields = this.closest('form').querySelectorAll('.custom-material-field');
            if (this.value === 'custom') {
                customFields.forEach(field => field.style.display = 'block');
                // Make material_name required
                const nameInput = this.closest('form').querySelector('input[name="material_name"]');
                if (nameInput) nameInput.required = true;
            } else {
                customFields.forEach(field => field.style.display = 'none');
                // Remove required from material_name
                const nameInput = this.closest('form').querySelector('input[name="material_name"]');
                if (nameInput) nameInput.required = false;
            }
        });
    });
    
    // Material form validation
    addMaterialForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const materialSelector = this.querySelector('.material-selector');
            const nameInput = this.querySelector('input[name="material_name"]');
            const quantityInput = this.querySelector('input[name="quantity"]');
            
            let isValid = true;
            
            // First validate that we have a material selection or custom input
            if (materialSelector && materialSelector.value === 'custom') {
                if (nameInput && !nameInput.value.trim()) {
                    highlightInvalidField(nameInput, 'Please enter a material name');
                    isValid = false;
                }
            }
            
            // Validate quantity (this is always required)
            if (quantityInput) {
                const quantity = parseFloat(quantityInput.value);
                if (isNaN(quantity) || quantity <= 0) {
                    highlightInvalidField(quantityInput, 'Please enter a valid quantity');
                    isValid = false;
                }
            } else {
                console.error("Quantity input is missing from the form");
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
    
    // Handle add custom material functionality for templates
    const addCustomMaterialButtons = document.querySelectorAll('.add-custom-material');
    if (addCustomMaterialButtons.length) {
        addCustomMaterialButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get the materials container
                const materialsContainer = this.closest('.item-materials-section')
                    .querySelector('.item-materials-container');
                
                // Create custom material form
                const customMaterialForm = document.createElement('div');
                customMaterialForm.className = 'card mt-3 mb-3 custom-material-form';
                customMaterialForm.innerHTML = `
                    <div class="card-body">
                        <h6 class="mb-3">Add Custom Material</h6>
                        <div class="row mb-2">
                            <div class="col-md-4">
                                <label class="form-label">Material Name</label>
                                <input type="text" class="form-control" name="material_name[]" required>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Category</label>
                                <select class="form-select" name="material_categories[]">
                                    <option value="paper">Paper</option>
                                    <option value="ink">Ink</option>
                                    <option value="substrate">Substrate</option>
                                    <option value="laminate">Laminate</option>
                                    <option value="binding">Binding</option>
                                    <option value="other" selected>Other</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Quantity</label>
                                <input type="number" class="form-control" name="material_quantity[]" value="1" min="0" step="0.01">
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Unit</label>
                                <select class="form-select" name="material_unit[]">
                                    <option value="pcs">Piece(s)</option>
                                    <option value="sheets">Sheet(s)</option>
                                    <option value="sqft">Sq. Foot</option>
                                    <option value="yards">Yard(s)</option>
                                    <option value="meters">Meter(s)</option>
                                    <option value="liters">Liter(s)</option>
                                    <option value="gallons">Gallon(s)</option>
                                </select>
                            </div>
                        </div>
                        <div class="mb-2">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="material_notes[]" rows="1"></textarea>
                        </div>
                        <div class="text-end">
                            <button type="button" class="btn btn-sm btn-outline-danger remove-custom-material">
                                <i class="bi bi-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                `;
                
                // Add event listener to remove button
                const removeButton = customMaterialForm.querySelector('.remove-custom-material');
                removeButton.addEventListener('click', function() {
                    customMaterialForm.remove();
                });
                
                // Add the form to the container
                materialsContainer.appendChild(customMaterialForm);
            });
        });
    }
}
