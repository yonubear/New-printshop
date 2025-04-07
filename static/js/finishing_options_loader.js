/**
 * Simple Finishing Options Loader
 * This script handles loading finishing options from the API and displaying them in the UI
 */

// Global options array
window.selectedFinishingOptions = window.selectedFinishingOptions || [];

// Function to update price calculations when finishing options change
function updateFinishingCalculations() {
    console.log("Updating finishing calculations with options:", window.selectedFinishingOptions);
    
    // First try to call updateCalculations on the window object if available
    if (typeof window.updateCalculations === 'function') {
        console.log("Calling global updateCalculations");
        window.updateCalculations();
        return;
    }
    
    // If not available, try to find elements directly and update them
    console.log("Global updateCalculations not found, using direct method");
    
    // Look for the price elements in primary calculator form
    const calculatedPriceDisplay = document.getElementById('calculated_price');
    const finishingCostDisplay = document.getElementById('finishing-cost-display');
    const calculatedPriceField = document.getElementById('calculated_price');
    const unitPriceInput = document.getElementById('unit_price');
    const useCalculatedPriceBtn = document.getElementById('use_calculated_price');
    
    // Calculate finishing cost
    const totalFinishingCost = calculateFinishingCost();
    console.log("Calculated finishing cost:", totalFinishingCost);
    
    // Get the quantity if it exists
    const quantityInput = document.getElementById('quantity');
    const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
    
    // Update finishing cost display if it exists
    if (finishingCostDisplay) {
        finishingCostDisplay.textContent = totalFinishingCost.toFixed(2);
    }
    
    // Try to calculate the total price if we have paper and printing costs
    const paperCostDisplay = document.getElementById('paper-cost-display');
    const printingCostDisplay = document.getElementById('printing-cost-display');
    
    // If we have both paper and printing costs, calculate total
    if (paperCostDisplay && printingCostDisplay && calculatedPriceDisplay) {
        const paperCost = parseFloat(paperCostDisplay.textContent) || 0;
        const printingCost = parseFloat(printingCostDisplay.textContent) || 0;
        
        // Calculate total with markup
        const totalCost = (paperCost + printingCost + totalFinishingCost) * 2.5;
        calculatedPriceDisplay.textContent = totalCost.toFixed(2);
        
        // Also update the calculated price field if it exists
        if (calculatedPriceField) {
            calculatedPriceField.value = totalCost.toFixed(2);
        }
        
        // If there's a "Use Calculated Price" button, update its data attribute
        if (useCalculatedPriceBtn) {
            useCalculatedPriceBtn.setAttribute('data-price', totalCost.toFixed(2));
        }
    } else if (calculatedPriceField) {
        // As a fallback, just add the finishing cost to any existing price
        let currentPrice = parseFloat(calculatedPriceField.value) || 0;
        const newPrice = currentPrice + (totalFinishingCost * 2.5);
        calculatedPriceField.value = newPrice.toFixed(2);
    }
    
    // Trigger a custom event that other scripts could listen for
    const event = new CustomEvent('finishingOptionsUpdated', {
        detail: { 
            options: window.selectedFinishingOptions,
            cost: totalFinishingCost
        }
    });
    document.dispatchEvent(event);
}

// Function to calculate finishing costs
function calculateFinishingCost() {
    if (!window.selectedFinishingOptions || window.selectedFinishingOptions.length === 0) {
        return 0;
    }
    
    const quantity = document.getElementById('quantity') ? 
                    parseInt(document.getElementById('quantity').value) || 1 : 1;
    
    let totalFinishingCost = 0;
    window.selectedFinishingOptions.forEach(option => {
        let optionCost = option.basePrice || 0;
        if (option.pricePerPiece && option.pricePerPiece > 0) {
            optionCost += option.pricePerPiece * quantity;
        }
        totalFinishingCost += optionCost;
    });
    
    return totalFinishingCost;
}

// Wait for the DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("Finishing options loader initialized");
    
    // Find the finishing options container
    const finishingCategoriesContainer = document.getElementById('finishing-categories');
    if (!finishingCategoriesContainer) {
        console.error("Finishing categories container not found");
        return;
    }
    
    // Show loading message
    finishingCategoriesContainer.innerHTML = '<div class="text-muted small mb-2">Loading finishing options... <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></div>';
    
    // Load the finishing options categories
    loadFinishingCategories(finishingCategoriesContainer);
    
    /**
     * Load finishing categories from API and create UI
     */
    function loadFinishingCategories(container) {
        console.log("Loading finishing categories from API...");
        
        fetch('/api/finishing-categories')
            .then(response => {
                console.log("API Response Status:", response.status);
                if (!response.ok) {
                    throw new Error(`API returned status ${response.status}`);
                }
                return response.json();
            })
            .then(categories => {
                console.log("Finishing categories loaded:", categories);
                
                if (!categories || categories.length === 0) {
                    container.innerHTML = '<div class="alert alert-warning">No finishing options available.</div>';
                    return;
                }
                
                // Create container for categories
                const categoriesHTML = [];
                
                // Create basic accordions for each category
                categories.forEach(category => {
                    const categoryId = category.replace(/\s+/g, '-').toLowerCase();
                    
                    categoriesHTML.push(`
                        <div class="card mb-2">
                            <div class="card-header p-1">
                                <div class="form-check">
                                    <input class="form-check-input category-toggle" type="checkbox" 
                                           id="category-${categoryId}" data-category="${category}">
                                    <label class="form-check-label" for="category-${categoryId}">
                                        ${category}
                                    </label>
                                </div>
                            </div>
                            <div id="options-container-${categoryId}" class="collapse options-container">
                                <div class="card-body p-2">
                                    <div class="text-muted small">Select to show options</div>
                                </div>
                            </div>
                        </div>
                    `);
                });
                
                // Set the HTML content
                container.innerHTML = categoriesHTML.join('');
                
                // Add event listeners to category checkboxes
                document.querySelectorAll('.category-toggle').forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const category = this.dataset.category;
                        const categoryId = category.replace(/\s+/g, '-').toLowerCase();
                        const optionsContainer = document.getElementById(`options-container-${categoryId}`);
                        
                        if (this.checked) {
                            // Show options container
                            if (optionsContainer) {
                                optionsContainer.classList.add('show');
                                loadOptionsForCategory(category, optionsContainer);
                            }
                        } else {
                            // Hide options container and clear selection
                            if (optionsContainer) {
                                optionsContainer.classList.remove('show');
                                
                                // Reset any selected options for this category
                                const selects = optionsContainer.querySelectorAll('select');
                                selects.forEach(select => {
                                    select.value = '';
                                });
                                
                                // Update global selectedFinishingOptions array if it exists
                                if (window.selectedFinishingOptions !== undefined) {
                                    window.selectedFinishingOptions = window.selectedFinishingOptions.filter(opt => opt.category !== category);
                                    
                                    // Trigger price recalculation
                                    updateFinishingCalculations();
                                }
                            }
                        }
                    });
                });
            })
            .catch(error => {
                console.error("Error loading finishing categories:", error);
                container.innerHTML = '<div class="alert alert-danger">Error loading finishing options: ' + error.message + '</div>';
            });
    }
    
    /**
     * Load options for a specific category
     */
    function loadOptionsForCategory(category, container) {
        console.log(`Loading options for category: ${category}`);
        
        // Show loading indicator
        container.querySelector('.card-body').innerHTML = `
            <div class="text-muted small">
                Loading ${category} options... 
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            </div>
        `;
        
        // Fetch options from API
        fetch(`/api/finishing-options?category=${encodeURIComponent(category)}`)
            .then(response => {
                console.log(`API Response for ${category}:`, response.status);
                if (!response.ok) {
                    throw new Error(`API returned status ${response.status}`);
                }
                return response.json();
            })
            .then(options => {
                console.log(`Options for ${category}:`, options);
                
                if (!options || options.length === 0) {
                    container.querySelector('.card-body').innerHTML = `<div class="alert alert-warning">No options available for ${category}.</div>`;
                    return;
                }
                
                // Create select dropdown for options
                const selectHTML = `
                    <div class="form-group">
                        <label for="select-${category.replace(/\s+/g, '-').toLowerCase()}" class="form-label">
                            Select ${category} Option:
                        </label>
                        <select class="form-select finishing-option" 
                                id="select-${category.replace(/\s+/g, '-').toLowerCase()}"
                                name="finishing_option_${category.replace(/\s+/g, '-').toLowerCase()}"
                                data-category="${category}">
                            <option value="">-- Select Option --</option>
                            ${options.map(option => `
                                <option value="${option.id}" 
                                        data-base-price="${option.base_price || 0}"
                                        data-price-per-piece="${option.price_per_piece || 0}">
                                    ${option.name} ($${option.base_price} + $${option.price_per_piece}/each)
                                </option>
                            `).join('')}
                        </select>
                    </div>
                `;
                
                container.querySelector('.card-body').innerHTML = selectHTML;
                
                // Add event listeners for option changes
                const select = container.querySelector('select.finishing-option');
                if (select) {
                    select.addEventListener('change', function() {
                        console.log(`Selected ${category} option:`, this.value);
                        
                        // Get the option details from the selected option
                        const optionId = this.value;
                        const selectedOption = this.options[this.selectedIndex];
                        
                        // Update the global selectedFinishingOptions array if it exists
                        if (window.selectedFinishingOptions !== undefined) {
                            // Remove any existing option for this category
                            window.selectedFinishingOptions = window.selectedFinishingOptions.filter(opt => opt.category !== category);
                            
                            // Add the new selection if an option was selected
                            if (optionId) {
                                window.selectedFinishingOptions.push({
                                    id: optionId,
                                    name: selectedOption.text,
                                    category: category,
                                    basePrice: parseFloat(selectedOption.dataset.basePrice) || 0,
                                    pricePerPiece: parseFloat(selectedOption.dataset.pricePerPiece) || 0
                                });
                            }
                            
                            // Trigger price recalculation
                            updateFinishingCalculations();
                        } else {
                            console.warn("selectedFinishingOptions array not found in global scope");
                        }
                    });
                }
            })
            .catch(error => {
                console.error(`Error loading options for ${category}:`, error);
                container.querySelector('.card-body').innerHTML = `<div class="alert alert-danger">Error loading options: ${error.message}</div>`;
            });
    }
});