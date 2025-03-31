// Print Order Management System - Main JS

// Document Ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Order status update handlers
    setupOrderStatusUpdates();
    
    // Material form handlers
    setupMaterialForms();
    
    // Order item handlers
    setupOrderItemForms();
    
    // Setup responsive handling for tables
    setupResponsiveTables();
});

/**
 * Setup order status update functionality
 */
function setupOrderStatusUpdates() {
    const statusButtons = document.querySelectorAll('.btn-update-status');
    
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const orderId = this.dataset.orderId;
            const status = this.dataset.status;
            
            if (confirm(`Are you sure you want to change the order status to ${status}?`)) {
                updateOrderStatus(orderId, status);
            }
        });
    });
}

/**
 * Update order status via AJAX
 */
function updateOrderStatus(orderId, status) {
    fetch(`/api/orders/${orderId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: status }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the UI with the new status
            const statusBadge = document.querySelector(`#order-status-${orderId}`);
            if (statusBadge) {
                statusBadge.textContent = status;
                
                // Remove old status classes
                statusBadge.classList.remove('badge-new', 'badge-in-progress', 'badge-completed', 'badge-cancelled');
                
                // Add new status class
                statusBadge.classList.add(`badge-${status}`);
            }
            
            // Update workflow steps visualization if it exists
            updateWorkflowSteps(status);
            
            // Show success message
            showNotification(`Order status updated to ${status}`, 'success');
            
            // Refresh the page after a brief delay to show updated info
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showNotification('Failed to update order status', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating order status:', error);
        showNotification('Error updating order status', 'danger');
    });
}

/**
 * Update workflow steps visualization
 */
function updateWorkflowSteps(status) {
    const workflowSteps = document.querySelectorAll('.workflow-step');
    
    if (workflowSteps.length === 0) return;
    
    // Reset all steps
    workflowSteps.forEach(step => {
        step.classList.remove('active', 'completed');
    });
    
    // Mark appropriate steps based on status
    const stepOrder = ['new', 'in-progress', 'completed', 'cancelled'];
    const statusIndex = stepOrder.indexOf(status);
    
    if (status === 'cancelled') {
        // Special case for cancelled - only mark the cancelled step
        workflowSteps.forEach(step => {
            if (step.dataset.status === 'cancelled') {
                step.classList.add('active');
            }
        });
    } else {
        // Normal workflow progression
        workflowSteps.forEach(step => {
            const stepStatus = step.dataset.status;
            const stepIndex = stepOrder.indexOf(stepStatus);
            
            if (stepIndex < statusIndex) {
                step.classList.add('completed');
            } else if (stepIndex === statusIndex) {
                step.classList.add('active');
            }
        });
    }
}

/**
 * Setup material form handlers
 */
function setupMaterialForms() {
    const addMaterialForms = document.querySelectorAll('.add-material-form');
    
    addMaterialForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const quantityInput = this.querySelector('input[name="quantity"]');
            const quantity = parseFloat(quantityInput.value);
            
            if (isNaN(quantity) || quantity <= 0) {
                e.preventDefault();
                showNotification('Please enter a valid quantity', 'warning');
                quantityInput.focus();
            }
        });
    });
}

/**
 * Setup order item forms
 */
function setupOrderItemForms() {
    const addItemForms = document.querySelectorAll('.add-item-form');
    
    addItemForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const nameInput = this.querySelector('input[name="name"]');
            const quantityInput = this.querySelector('input[name="quantity"]');
            const priceInput = this.querySelector('input[name="unit_price"]');
            
            const name = nameInput.value.trim();
            const quantity = parseInt(quantityInput.value);
            const price = parseFloat(priceInput.value);
            
            if (name === '') {
                e.preventDefault();
                showNotification('Please enter an item name', 'warning');
                nameInput.focus();
                return;
            }
            
            if (isNaN(quantity) || quantity <= 0) {
                e.preventDefault();
                showNotification('Please enter a valid quantity', 'warning');
                quantityInput.focus();
                return;
            }
            
            if (isNaN(price) || price < 0) {
                e.preventDefault();
                showNotification('Please enter a valid price', 'warning');
                priceInput.focus();
                return;
            }
        });
    });
    
    // Calculate total price based on quantity and unit price
    const quantityInputs = document.querySelectorAll('.calc-quantity');
    const priceInputs = document.querySelectorAll('.calc-price');
    
    const updateTotalPrice = (row) => {
        const quantity = parseInt(row.querySelector('.calc-quantity').value) || 0;
        const price = parseFloat(row.querySelector('.calc-price').value) || 0;
        const totalElement = row.querySelector('.calc-total');
        
        if (totalElement) {
            totalElement.textContent = `$${(quantity * price).toFixed(2)}`;
        }
    };
    
    quantityInputs.forEach(input => {
        input.addEventListener('input', function() {
            updateTotalPrice(this.closest('tr, .item-row'));
        });
    });
    
    priceInputs.forEach(input => {
        input.addEventListener('input', function() {
            updateTotalPrice(this.closest('tr, .item-row'));
        });
    });
}

/**
 * Make tables responsive for tablet view
 */
function setupResponsiveTables() {
    const tables = document.querySelectorAll('table');
    
    tables.forEach(table => {
        // Add responsive wrapper if not already present
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-responsive');
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}

/**
 * Show a notification message
 */
function showNotification(message, type) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.classList.add('toast-container', 'position-fixed', 'bottom-0', 'end-0', 'p-3');
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.classList.add('toast', 'align-items-center', 'text-white', `bg-${type}`);
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    
    // Initialize and show the toast
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: 3000
    });
    
    toast.show();
    
    // Remove the toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', function() {
        toastEl.remove();
    });
}
