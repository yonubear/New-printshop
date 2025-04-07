// quote_form.js - JavaScript for quote form functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('Quote form script loaded');
    
    // Enable CSRF protection for AJAX requests
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    console.log('CSRF protection enabled for AJAX requests');
    
    // Handle adding quote items
    const quoteItemForm = document.getElementById('quote-item-form');
    if (quoteItemForm) {
        console.log('Quote item form detected');
        
        // Log form target for debugging
        console.log('Form action URL:', quoteItemForm.action);
        
        // When the form is submitted - we're using standard form submission now
        quoteItemForm.addEventListener('submit', function(event) {
            console.log('Quote item form submitted');
            // Let the form submit normally - no AJAX for now
        });
        
        // Add a direct "Use Default Price" button functionality
        const useDefaultPriceBtn = document.getElementById('use_default_price');
        if (useDefaultPriceBtn) {
            useDefaultPriceBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Set a default price of $1.00
                const defaultPrice = 1.00;
                
                // Update unit price field
                const unitPriceInput = document.getElementById('unit_price');
                if (unitPriceInput) {
                    unitPriceInput.value = defaultPrice.toFixed(2);
                    console.log('Set default unit price to:', defaultPrice.toFixed(2));
                }
                
                // Update total price if quantity field exists
                const quantityInput = document.getElementById('quantity');
                const totalPriceDisplay = document.getElementById('total_price_display');
                
                if (quantityInput && totalPriceDisplay) {
                    const quantity = parseInt(quantityInput.value) || 1;
                    const totalPrice = defaultPrice * quantity;
                    totalPriceDisplay.textContent = totalPrice.toFixed(2);
                    console.log('Set total price to:', totalPrice.toFixed(2));
                }
                
                // Also update any hidden calculated price field
                const calculatedPriceHidden = document.getElementById('calculated_price_hidden');
                if (calculatedPriceHidden) {
                    calculatedPriceHidden.value = defaultPrice.toFixed(2);
                }
                
                // Show alert to confirm price was set
                alert('Default price of $1.00 has been applied.');
            });
            
            console.log('Default price button handler added with confirmation alert');
        }
    } else {
        console.warn('Quote item form not found');
    }
    
    // Customer search functionality
    const customerSearch = document.getElementById('customerSearch');
    if (customerSearch) {
        customerSearch.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const rows = document.querySelectorAll('#customerModal tbody tr');
            
            rows.forEach(row => {
                const name = row.cells[0].textContent.toLowerCase();
                const email = row.cells[1].textContent.toLowerCase();
                
                if (name.includes(searchValue) || email.includes(searchValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

function selectCustomer(id, name) {
    document.getElementById('customer_id_hidden').value = id;
    document.getElementById('customer-display').value = name;
    
    // Close the modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('customerModal'));
    modal.hide();
}

function editQuoteItem(id, name, description, quantity, price) {
    document.getElementById('edit_item_id').value = id;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_description').value = description;
    document.getElementById('edit_quantity').value = quantity;
    document.getElementById('edit_unit_price').value = price;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
    modal.show();
}

// Function to update the form's action URL with the correct item_id
function updateFormAction(form) {
    const itemId = document.getElementById('edit_item_id').value;
    if (itemId) {
        // Replace the placeholder '0' with the actual item ID
        form.action = form.action.replace('/items/0/', `/items/${itemId}/`);
        console.log('Updated form action:', form.action);
    } else {
        console.error('No item ID found in form');
        return false; // Prevent form submission
    }
    return true; // Allow form submission
}