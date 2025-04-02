/**
 * Material Handler for Template Price Items
 * This script manages the addition and removal of materials to template price items
 */

// Initialize material handling functionality
function initMaterialHandler() {
    console.log("Initializing material handler...");
    
    // Show/hide template materials section based on checkbox
    const templateCheckbox = document.getElementById('is_template');
    const materialsSection = document.getElementById('template_materials_section');
    
    if (templateCheckbox && materialsSection) {
        // Initial state
        if (templateCheckbox.checked) {
            materialsSection.classList.remove('d-none');
        } else {
            materialsSection.classList.add('d-none');
        }

        // Change event
        templateCheckbox.addEventListener('change', function() {
            console.log("Template checkbox changed:", this.checked);
            if (this.checked) {
                materialsSection.classList.remove('d-none');
            } else {
                materialsSection.classList.add('d-none');
            }
        });
    }
    
    // Setup add button
    const addButton = document.getElementById('add_template_material');
    if (addButton) {
        console.log("Add button found, attaching click handler");
        addButton.addEventListener('click', function(e) {
            e.preventDefault();
            addMaterial();
            return false;
        });
    } else {
        console.warn("Add material button not found");
    }
    
    // Setup initial remove buttons
    setupRemoveButtons();

    // Validate form submission
    setupFormValidation();
}

// Add a new material to the template
function addMaterial() {
    console.log("Adding material...");
    
    // Get selected material
    const materialSelect = document.getElementById('material_select');
    const quantityInput = document.getElementById('material_quantity');
    
    if (!materialSelect || !quantityInput) {
        console.error("Form elements not found", {
            materialSelect: materialSelect ? "found" : "missing",
            quantityInput: quantityInput ? "found" : "missing"
        });
        return;
    }
    
    const materialId = materialSelect.value;
    const materialText = materialSelect.options[materialSelect.selectedIndex].text;
    const quantity = parseFloat(quantityInput.value) || 0;
    
    console.log(`Material: ${materialId} - ${materialText}, Quantity: ${quantity}`);
    
    // Validate selection
    if (materialId === "" || materialId === "0") {
        alert("Please select a material");
        return;
    }
    
    if (quantity <= 0) {
        alert("Please enter a valid quantity");
        return;
    }
    
    // Get container
    const container = document.getElementById('selected_materials_container');
    if (!container) {
        console.error("Materials container not found");
        return;
    }
    
    // Remove "no materials" message if it exists
    const noMaterialsMsg = container.querySelector('.text-muted.text-center');
    if (noMaterialsMsg) {
        noMaterialsMsg.remove();
    }
    
    // Check for existing material
    const existingInputs = document.querySelectorAll('input[name="template_material_ids[]"]');
    let exists = false;
    
    for (let i = 0; i < existingInputs.length; i++) {
        if (existingInputs[i].value === materialId) {
            exists = true;
            
            // Update existing quantity
            const parent = existingInputs[i].closest('.selected-material-item');
            const qtySpan = parent.querySelector('.material-quantity');
            const qtyInput = parent.querySelector('input[name="template_material_quantities[]"]');
            
            if (qtySpan && qtyInput) {
                const oldQty = parseFloat(qtyInput.value) || 0;
                const newQty = oldQty + quantity;
                
                qtySpan.textContent = newQty.toFixed(2);
                qtyInput.value = newQty;
            }
            
            break;
        }
    }
    
    // Add new material if it doesn't exist
    if (!exists) {
        // Create the HTML for the material item
        const materialItem = document.createElement('div');
        materialItem.className = 'selected-material-item d-flex justify-content-between align-items-center p-2 mb-2 border rounded';
        
        materialItem.innerHTML = `
            <input type="hidden" name="template_material_ids[]" value="${materialId}">
            <input type="hidden" name="template_material_quantities[]" value="${quantity}">
            <div>
                <strong>${materialText}</strong>
                <span class="badge bg-secondary ms-2 material-quantity">${quantity}</span>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger remove-material">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        container.appendChild(materialItem);
        
        // Add click handler to remove button
        const removeBtn = materialItem.querySelector('.remove-material');
        if (removeBtn) {
            removeBtn.onclick = function() {
                materialItem.remove();
            };
        }
    }
    
    // Reset the quantity input
    quantityInput.value = "1";
    
    // Debug: log all current materials
    console.log("Current materials:");
    document.querySelectorAll('input[name="template_material_ids[]"]').forEach((input, index) => {
        const qtyInput = document.querySelectorAll('input[name="template_material_quantities[]"]')[index];
        console.log(`- Material ID: ${input.value}, Quantity: ${qtyInput.value}`);
    });
}

// Setup click handlers for remove buttons
function setupRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-material');
    
    removeButtons.forEach(function(button) {
        button.onclick = function() {
            const item = this.closest('.selected-material-item');
            if (item) {
                item.remove();
            }
        };
    });
}

// Setup form validation to ensure form data includes materials
function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const isTemplate = document.getElementById('is_template');
            if (isTemplate && isTemplate.checked) {
                const materials = document.querySelectorAll('input[name="template_material_ids[]"]');
                
                console.log(`Form submit: template checked=${isTemplate.checked}, materials count=${materials.length}`);
                
                // Debug current form data that will be submitted
                const formData = new FormData(form);
                console.log("Form data to be submitted:");
                for (let [key, value] of formData.entries()) {
                    console.log(`${key}: ${value}`);
                }
            }
        });
    });
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded, initializing material handler");
    initMaterialHandler();
});