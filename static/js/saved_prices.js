/**
 * Handle saved prices functionality for order forms
 */

document.addEventListener('DOMContentLoaded', function() {
    initSavedPricesSelector();
});

/**
 * Initialize saved prices selector functionality on order forms
 */
function initSavedPricesSelector() {
    // Set up category selector on order item form
    const categorySelector = document.getElementById('price_category');
    const priceSelector = document.getElementById('saved_price');
    
    if (categorySelector && priceSelector) {
        // Initial load of saved prices
        loadSavedPrices(categorySelector.value);
        
        // Set up change event
        categorySelector.addEventListener('change', function() {
            loadSavedPrices(this.value);
        });
        
        // Set up price selection
        priceSelector.addEventListener('change', function() {
            if (this.value) {
                applySavedPrice(this.value);
            }
        });
    }
}

/**
 * Load saved prices for a specific category
 */
function loadSavedPrices(category) {
    const priceSelector = document.getElementById('saved_price');
    if (!priceSelector) return;
    
    // Clear current options
    priceSelector.innerHTML = '<option value="">-- Select a saved price --</option>';
    
    // If no category is selected, return
    if (!category) return;
    
    // Fetch prices for the selected category, including materials data
    fetch(`/api/saved-prices?category=${category}&include_materials=true`)
        .then(response => response.json())
        .then(prices => {
            // Add options for each price
            prices.forEach(price => {
                const option = document.createElement('option');
                option.value = price.id;
                
                // Add template indicator if applicable
                let displayText = `${price.name} ($${price.price.toFixed(2)} per ${price.unit})`;
                if (price.is_template) {
                    displayText += ' [Template]';
                }
                
                option.textContent = displayText;
                option.dataset.price = price.price;
                option.dataset.name = price.name;
                option.dataset.description = price.description || '';
                option.dataset.sku = price.sku || '';
                option.dataset.unit = price.unit;
                option.dataset.isTemplate = price.is_template ? 'true' : 'false';
                
                // Store materials data as JSON string in dataset
                if (price.is_template && price.materials && price.materials.length > 0) {
                    option.dataset.materials = JSON.stringify(price.materials);
                }
                
                priceSelector.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading saved prices:', error);
        });
}

/**
 * Apply selected saved price to the order item form
 */
function applySavedPrice(priceId) {
    const priceSelector = document.getElementById('saved_price');
    const selectedOption = priceSelector.options[priceSelector.selectedIndex];
    
    if (!selectedOption) return;
    
    // Fill in the form fields with the saved price data
    const itemNameField = document.getElementById('item_name');
    const itemDescriptionField = document.getElementById('item_description');
    const itemSkuField = document.getElementById('item_sku');
    const unitPriceField = document.getElementById('unit_price');
    
    if (itemNameField) {
        itemNameField.value = selectedOption.dataset.name;
    }
    
    if (itemDescriptionField && selectedOption.dataset.description) {
        itemDescriptionField.value = selectedOption.dataset.description;
    }
    
    if (itemSkuField && selectedOption.dataset.sku) {
        itemSkuField.value = selectedOption.dataset.sku;
    }
    
    if (unitPriceField) {
        unitPriceField.value = selectedOption.dataset.price;
        // Trigger change event to recalculate total
        const event = new Event('change');
        unitPriceField.dispatchEvent(event);
    }
    
    // Handle materials if this is a template with materials
    if (selectedOption.dataset.isTemplate === 'true' && selectedOption.dataset.materials) {
        try {
            const materials = JSON.parse(selectedOption.dataset.materials);
            
            // If we have a materials container in the form
            const materialsContainer = document.querySelector('.item-materials-container');
            if (materialsContainer) {
                // Clear existing materials
                materialsContainer.innerHTML = '';
                
                // Create heading
                const heading = document.createElement('h6');
                heading.className = 'mt-3 mb-2';
                heading.textContent = 'Template Materials:';
                materialsContainer.appendChild(heading);
                
                // Create materials list
                const materialsList = document.createElement('ul');
                materialsList.className = 'list-group mb-3';
                
                materials.forEach(material => {
                    const materialItem = document.createElement('li');
                    materialItem.className = 'list-group-item d-flex justify-content-between align-items-center';
                    
                    // Material name and quantity
                    const materialInfo = document.createElement('div');
                    materialInfo.innerHTML = `
                        <strong>${material.material_name}</strong>
                        <span class="ms-2 text-muted">
                            ${material.quantity} ${material.unit}
                        </span>
                    `;
                    
                    // Add cost if available
                    if (material.cost_price > 0) {
                        const costBadge = document.createElement('span');
                        costBadge.className = 'badge bg-secondary rounded-pill';
                        costBadge.textContent = `$${material.cost_price.toFixed(2)}`;
                        materialItem.appendChild(costBadge);
                    }
                    
                    materialItem.appendChild(materialInfo);
                    materialsList.appendChild(materialItem);
                    
                    // Add material to hidden inputs for form submission
                    addMaterialToForm(material);
                });
                
                materialsContainer.appendChild(materialsList);
                
                // Make materials section visible
                const materialsSection = document.querySelector('.item-materials-section');
                if (materialsSection) {
                    materialsSection.classList.remove('d-none');
                }
            }
        } catch (e) {
            console.error('Error parsing materials data:', e);
        }
    }
}

/**
 * Add material from template to form hidden inputs
 */
function addMaterialToForm(material) {
    // Get the form
    const form = document.querySelector('form');
    if (!form) return;
    
    // Create hidden input for each material property
    const materialNameInput = document.createElement('input');
    materialNameInput.type = 'hidden';
    materialNameInput.name = 'material_name[]';
    materialNameInput.value = material.material_name;
    
    const materialQuantityInput = document.createElement('input');
    materialQuantityInput.type = 'hidden';
    materialQuantityInput.name = 'material_quantity[]';
    materialQuantityInput.value = material.quantity;
    
    const materialUnitInput = document.createElement('input');
    materialUnitInput.type = 'hidden';
    materialUnitInput.name = 'material_unit[]';
    materialUnitInput.value = material.unit;
    
    const materialNotesInput = document.createElement('input');
    materialNotesInput.type = 'hidden';
    materialNotesInput.name = 'material_notes[]';
    materialNotesInput.value = material.notes || '';
    
    const materialCategoryInput = document.createElement('input');
    materialCategoryInput.type = 'hidden';
    materialCategoryInput.name = 'material_categories[]';
    materialCategoryInput.value = material.category || 'other';
    
    // Append to form
    form.appendChild(materialNameInput);
    form.appendChild(materialQuantityInput);
    form.appendChild(materialUnitInput);
    form.appendChild(materialNotesInput);
    form.appendChild(materialCategoryInput);
}