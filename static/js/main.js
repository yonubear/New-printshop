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
    setupMaterialPanel();
    setupMaterialForms();
    
    // Order item handlers
    setupOrderItemForms();
    
    // Initialize any modals that might need calculation
    setupModalCalculations();
    
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
        // Get the closest container that has both quantity and price inputs
        let container = row;
        
        // If it's a modal, find the parent modal instead of row
        if (row.classList.contains('modal-content') || row.closest('.modal-content')) {
            container = row.classList.contains('modal-content') ? row : row.closest('.modal-content');
        }
        
        const quantityInput = container.querySelector('.calc-quantity');
        const priceInput = container.querySelector('.calc-price');
        const totalElement = container.querySelector('.calc-total');
        
        if (quantityInput && priceInput && totalElement) {
            const quantity = parseInt(quantityInput.value) || 0;
            const price = parseFloat(priceInput.value) || 0;
            const total = quantity * price;
            totalElement.textContent = `$${total.toFixed(2)}`;
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
 * Setup material panel toggle buttons
 */
function setupMaterialPanel() {
    const toggleButtons = document.querySelectorAll('.toggle-materials-btn');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const targetId = this.getAttribute('data-target');
            console.log("Target ID:", targetId);
            
            if (!targetId) {
                console.error("No target ID found in button");
                return;
            }
            
            // First try finding the panel by ID
            let panel = document.getElementById(targetId);
            
            // If not found by ID, try finding it by a more complex selector
            if (!panel) {
                console.log("Panel not found by ID, trying alternative selector");
                // Try to find it by a more specific selector - maybe the ID has a different format
                panel = document.querySelector(`tr[id='${targetId}'], tr[id*='${targetId}']`);
            }
            
            if (!panel) {
                console.error("Target panel not found:", targetId);
                // Try to log all table rows to help debug
                const allRows = document.querySelectorAll('tr');
                console.log("All table rows:", Array.from(allRows).map(row => row.id));
                return;
            }
            
            panel.classList.toggle('d-none');
            
            // Update button text
            if (panel.classList.contains('d-none')) {
                this.innerHTML = '<i class="bi bi-plus-circle me-1"></i> Show Materials';
            } else {
                this.innerHTML = '<i class="bi bi-dash-circle me-1"></i> Hide Materials';
            }
        });
    });
}

/**
 * Setup calculation updates for modals
 */
function setupModalCalculations() {
    // Initialize price calculations when edit modals are shown
    const editModals = document.querySelectorAll('.modal');
    
    editModals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const quantityInputs = this.querySelectorAll('.calc-quantity');
            const priceInputs = this.querySelectorAll('.calc-price');
            
            // Update totals when the modal is shown
            const updateAllTotals = () => {
                const container = this;
                const quantityInput = container.querySelector('.calc-quantity');
                const priceInput = container.querySelector('.calc-price');
                const totalElement = container.querySelector('.calc-total');
                
                if (quantityInput && priceInput && totalElement) {
                    const quantity = parseInt(quantityInput.value) || 0;
                    const price = parseFloat(priceInput.value) || 0;
                    const total = quantity * price;
                    totalElement.textContent = `$${total.toFixed(2)}`;
                }
            };
            
            // Initialize totals
            updateAllTotals();
            
            // Add event listeners to quantity and price inputs
            quantityInputs.forEach(input => {
                input.addEventListener('input', updateAllTotals);
            });
            
            priceInputs.forEach(input => {
                input.addEventListener('input', updateAllTotals);
            });
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
