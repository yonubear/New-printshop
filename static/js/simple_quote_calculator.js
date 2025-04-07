/**
 * Simple Quote Calculator for Print Shop
 * This script handles price calculations for print jobs based on real database values
 */

// Global variables for data stores
let paperOptionsData = [];
let printPricingData = [];
let finishingCategories = [];
let finishingOptionsData = {};
let selectedFinishingOptions = [];

// Make selectedFinishingOptions accessible globally for other scripts
window.selectedFinishingOptions = selectedFinishingOptions;

// Make updateCalculations accessible globally for other scripts
window.updateCalculations = function() {
    // If our calculator is initialized, call its function
    if (typeof updateCalculations === 'function') {
        console.log("Calling local updateCalculations from global function");
        updateCalculations();
    } else {
        console.warn("Local updateCalculations not available");
    }
};

// Form and display element references
let quoteForm;
let nameInput, quantityInput, unitPriceInput, descriptionInput;
let paperSizeSelect, paperTypeSelect, paperWeightSelect, paperColorSelect;
let printTypeBW, printTypeColor, sidesSingle, sidesDouble, nUpSelect, finishingOptions;
let calculatedPriceField, basePriceDisplay, paperCostDisplay, printingCostDisplay;
let finishingCostDisplay, unitPriceDisplay, quantityDisplay, totalPriceDisplay, useCalculatedPriceBtn;
let presetBWCopiesBtn, presetColorCopiesBtn, presetBusinessCardsBtn, presetFlyersBtn;

// Global initialization function
function initializeQuoteCalculator() {
    console.log("Simple quote calculator initialization called");
    
    // Main form elements
    quoteForm = document.getElementById('quote-item-form');
    if (!quoteForm) {
        console.error("Quote form not found in DOM!");
        return false;
    }
    
    // Initialize form elements
    initializeFormElements();
    
    // Initialize the calculator
    initializeCalculator();
    
    return true;
}

// Initialize the form element references
function initializeFormElements() {
    // Input elements
    nameInput = document.getElementById('name');
    quantityInput = document.getElementById('quantity');
    unitPriceInput = document.getElementById('unit_price');
    descriptionInput = document.getElementById('description');
    
    // Paper selection elements
    paperSizeSelect = document.getElementById('paper_size');
    paperTypeSelect = document.getElementById('paper_type');
    paperWeightSelect = document.getElementById('paper_weight');
    paperColorSelect = document.getElementById('paper_color');
    
    // Print options elements
    printTypeBW = document.getElementById('print_type_bw');
    printTypeColor = document.getElementById('print_type_color');
    sidesSingle = document.getElementById('sides_single');
    sidesDouble = document.getElementById('sides_double'); 
    nUpSelect = document.getElementById('n_up');
    finishingOptions = document.querySelectorAll('input[name="finishing_options"]');
    
    // Price calculation display elements
    calculatedPriceField = document.getElementById('calculated_price');
    basePriceDisplay = document.getElementById('base_price');
    paperCostDisplay = document.getElementById('paper_cost');
    printingCostDisplay = document.getElementById('printing_cost');
    finishingCostDisplay = document.getElementById('finishing_cost');
    unitPriceDisplay = document.getElementById('unit_price_display');
    quantityDisplay = document.getElementById('quantity_display');
    totalPriceDisplay = document.getElementById('total_price_display');
    useCalculatedPriceBtn = document.getElementById('use_calculated_price');
    
    // Preset buttons
    presetBWCopiesBtn = document.getElementById('preset_bw_copies');
    presetColorCopiesBtn = document.getElementById('preset_color_copies');
    presetBusinessCardsBtn = document.getElementById('preset_business_cards');
    presetFlyersBtn = document.getElementById('preset_flyers');
}

// Make functions globally accessible
window.initializeCalculator = initializeCalculator;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded - Auto-initializing quote calculator");
    initializeQuoteCalculator();
    
    function initializeCalculator() {
        console.log("Initializing quote calculator...");
        
        // Fetch data from the API endpoints
        fetchPaperOptions();
        fetchPrintPricing();
        
        // Check if finishing categories container exists
        const finishingCategoriesContainer = document.getElementById('finishing-categories');
        if (finishingCategoriesContainer) {
            console.log("Found finishing categories container, fetching categories...");
            fetchFinishingCategories();
        } else {
            console.warn("Finishing categories container not found!");
        }
        
        // Add event listeners for form elements
        if (quantityInput) {
            quantityInput.addEventListener('input', function() {
                updateCalculations();
                if (quantityDisplay) quantityDisplay.textContent = this.value;
            });
        }
        
        if (unitPriceInput) {
            unitPriceInput.addEventListener('input', function() {
                if (unitPriceDisplay) unitPriceDisplay.textContent = parseFloat(this.value).toFixed(2);
                updateTotalPrice();
            });
        }
        
        // Add listeners to all form controls that should trigger recalculations
        const formControls = document.querySelectorAll('#quote-item-form select, #quote-item-form input[type="radio"], #quote-item-form input[type="checkbox"]');
        formControls.forEach(control => {
            control.addEventListener('change', function(e) {
                console.log(`Change event on form control: ${e.target.id || e.target.name}`);
                
                // Force recalculation of prices
                updateCalculations();
            });
        });
        
        // Add explicit listeners for important controls to ensure they trigger recalculations
        const criticalControls = [
            'paper_size', 'paper_type', 'paper_weight', 'paper_color',
            'print_type_bw', 'print_type_color', 'sides_single', 'sides_double',
            'n_up'
        ];
        
        criticalControls.forEach(controlId => {
            const element = document.getElementById(controlId);
            if (element) {
                element.addEventListener('change', function() {
                    console.log(`Critical control changed: ${controlId}`);
                    // Trigger immediate recalculation
                    updateCalculations();
                });
            }
        });
        
        // Set up the "Use Calculated Price" button
        if (useCalculatedPriceBtn) {
            useCalculatedPriceBtn.addEventListener('click', function() {
                console.log("Use Calculated Price button clicked");
                
                // Get the price from either the data attribute or the calculated price field
                let calculatedPrice = 0;
                
                if (this.hasAttribute('data-price')) {
                    calculatedPrice = parseFloat(this.getAttribute('data-price')) || 0;
                    console.log("Using price from button data attribute:", calculatedPrice);
                } else if (calculatedPriceField) {
                    calculatedPrice = parseFloat(calculatedPriceField.value) || 0;
                    console.log("Using price from calculated price field:", calculatedPrice);
                } else {
                    console.warn("No calculated price found!");
                    // Try to get price from display element if it exists
                    const calcPriceDisplay = document.getElementById('calculated-price-display');
                    if (calcPriceDisplay) {
                        calculatedPrice = parseFloat(calcPriceDisplay.textContent) || 0;
                        console.log("Using price from display element:", calculatedPrice);
                    }
                }
                
                // Update the unit price input
                if (unitPriceInput) {
                    unitPriceInput.value = calculatedPrice.toFixed(2);
                    console.log("Updated unit price input to:", calculatedPrice.toFixed(2));
                    
                    // Also update the display if it exists
                    if (unitPriceDisplay) {
                        unitPriceDisplay.textContent = calculatedPrice.toFixed(2);
                    }
                    
                    // Update the total price
                    updateTotalPrice();
                }
            });
        }
        
        // Setup preset buttons
        setupPresetButtons();
    }
    
    function fetchPaperOptions() {
        fetch('/api/paper-options')
            .then(response => response.json())
            .then(data => {
                paperOptionsData = data;
                console.log("Paper options loaded:", data.length);
                console.log("Paper options data:", paperOptionsData);
                updateCalculations();
            })
            .catch(error => {
                console.error("Error fetching paper options:", error);
            });
    }
    
    function fetchPrintPricing() {
        fetch('/api/print-pricing')
            .then(response => response.json())
            .then(data => {
                printPricingData = data;
                console.log("Print pricing loaded:", data.length);
                updateCalculations();
            })
            .catch(error => {
                console.error("Error fetching print pricing:", error);
            });
    }
    
    function fetchFinishingCategories() {
        // Get the container for finishing options
        const finishingCategoriesContainer = document.getElementById('finishing-categories');
        if (!finishingCategoriesContainer) {
            console.error("Finishing categories container not found in the DOM");
            // Try to inspect the DOM to find where it should be
            console.log("DOM Structure for debugging:");
            console.log(document.body.innerHTML);
            return;
        }
        
        console.log("Fetching finishing categories from API...");
        finishingCategoriesContainer.innerHTML = '<div class="text-muted small mb-2">Loading finishing options... <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span></div>';
        
        // Debug DOM path
        let element = finishingCategoriesContainer;
        let domPath = [];
        while (element && element !== document.body) {
            domPath.unshift(element.tagName + (element.id ? '#' + element.id : ''));
            element = element.parentElement;
        }
        console.log("Finishing categories container DOM path:", domPath.join(' > '));
        
        // Fetch categories from API with debug headers
        console.log("Making fetch request to /api/finishing-categories");
        
        // Add a timestamp to prevent caching
        const timestamp = new Date().getTime();
        const url = `/api/finishing-categories?_=${timestamp}`;
        
        // Get CSRF token if available
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        const headers = {};
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
            console.log("Using CSRF token:", csrfToken);
        } else {
            console.warn("No CSRF token found in the page");
        }
        
        console.log("About to execute fetch request to:", url);
        
        fetch(url, {
            method: 'GET',
            headers: headers,
            credentials: 'same-origin'
        })
            .then(response => {
                console.log("Finishing categories API response status:", response.status);
                console.log("Finishing categories API response headers:", 
                    Array.from(response.headers.entries()).reduce((obj, [key, val]) => {
                        obj[key] = val;
                        return obj;
                    }, {})
                );
                
                if (!response.ok) {
                    throw new Error(`API returned status ${response.status}`);
                }
                return response.json();
            })
            .then(categories => {
                finishingCategories = categories;
                console.log("Finishing categories loaded successfully:", categories);
                
                if (!categories || categories.length === 0) {
                    console.warn("No categories returned from API");
                    finishingCategoriesContainer.innerHTML = '<div class="alert alert-warning">No finishing options available in the system.</div>';
                    return;
                }
                
                // Clear loading message
                finishingCategoriesContainer.innerHTML = '';
                
                // Create accordion for categories
                const accordion = document.createElement('div');
                accordion.className = 'accordion';
                accordion.id = 'finishingAccordion';
                
                console.log(`Creating UI for ${categories.length} finishing categories`);
                
                // Create a section for each category
                categories.forEach((category, index) => {
                    console.log(`Setting up category UI for: ${category}`);
                    createCategorySection(accordion, category, index);
                    // Pre-load options for this category
                    fetchFinishingOptionsForCategory(category);
                });
                
                finishingCategoriesContainer.appendChild(accordion);
                console.log("Finished building finishing options UI");
            })
            .catch(error => {
                console.error("Error fetching finishing categories:", error);
                finishingCategoriesContainer.innerHTML = '<div class="alert alert-danger">Failed to load finishing options. Please try again later.</div>';
            });
    }
    
    function createCategorySection(accordion, category, index) {
        // Create accordion item container
        const item = document.createElement('div');
        item.className = 'accordion-item mb-2';
        
        // Create header
        const headerDiv = document.createElement('div');
        headerDiv.className = 'accordion-header';
        headerDiv.id = `heading-${category.replace(/\s+/g, '-').toLowerCase()}`;
        
        // Create checkbox for the category
        const checkboxDiv = document.createElement('div');
        checkboxDiv.className = 'form-check';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'form-check-input category-toggle';
        checkbox.id = `category-${category.replace(/\s+/g, '-').toLowerCase()}`;
        checkbox.dataset.category = category;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = checkbox.id;
        label.textContent = category;
        
        checkboxDiv.appendChild(checkbox);
        checkboxDiv.appendChild(label);
        headerDiv.appendChild(checkboxDiv);
        
        // Create collapsible content area
        const collapseDiv = document.createElement('div');
        collapseDiv.className = 'collapse mt-2';
        collapseDiv.id = `collapse-${category.replace(/\s+/g, '-').toLowerCase()}`;
        
        // Options container (will be populated when category is selected)
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'options-container ps-3';
        optionsContainer.id = `options-${category.replace(/\s+/g, '-').toLowerCase()}`;
        optionsContainer.innerHTML = '<div class="text-muted small">Select this category to view options</div>';
        
        collapseDiv.appendChild(optionsContainer);
        
        // Add to accordion
        item.appendChild(headerDiv);
        item.appendChild(collapseDiv);
        accordion.appendChild(item);
        
        // Add event listener to toggle dropdown and load options
        checkbox.addEventListener('change', function() {
            // Toggle the collapse
            if (this.checked) {
                // Show options
                collapseDiv.classList.add('show');
                // If we haven't loaded the options yet, or need to refresh them, load now
                populateOptionsForCategory(category, optionsContainer);
            } else {
                // Hide options
                collapseDiv.classList.remove('show');
                // Clear any selected options
                const options = document.querySelectorAll(`#${optionsContainer.id} input[type="checkbox"]:checked`);
                options.forEach(option => {
                    option.checked = false;
                });
                // Remove from selected options array
                selectedFinishingOptions = selectedFinishingOptions.filter(opt => opt.category !== category);
                // Update price calculation
                updateCalculations();
            }
        });
    }
    
    function fetchFinishingOptionsForCategory(category) {
        // Fetch options for this category if we haven't already
        if (!finishingOptionsData[category]) {
            console.log(`Fetching finishing options for category: ${category}`);
            
            // Add a timestamp to prevent caching
            const timestamp = new Date().getTime();
            const url = `/api/finishing-options?category=${encodeURIComponent(category)}&_=${timestamp}`;
            
            console.log(`Making request to: ${url}`);
            
            // Get CSRF token if available
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            const headers = {};
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
                console.log(`Using CSRF token for ${category} request:`, csrfToken);
            }
            
            fetch(url, {
                method: 'GET',
                headers: headers,
                credentials: 'same-origin'
            })
                .then(response => {
                    console.log(`Finishing options API response for ${category}:`, response.status);
                    console.log(`Finishing options API response headers for ${category}:`, 
                        Array.from(response.headers.entries()).reduce((obj, [key, val]) => {
                            obj[key] = val;
                            return obj;
                        }, {})
                    );
                    
                    if (!response.ok) {
                        throw new Error(`API returned status ${response.status} for ${category}`);
                    }
                    return response.json();
                })
                .then(options => {
                    finishingOptionsData[category] = options;
                    console.log(`Loaded ${options.length} options for ${category}:`, options);
                    
                    // If an options container is already open for this category, update it
                    const optionsContainer = document.getElementById(`options-${category.replace(/\s+/g, '-').toLowerCase()}`);
                    const categoryCheckbox = document.getElementById(`category-${category.replace(/\s+/g, '-').toLowerCase()}`);
                    
                    if (optionsContainer && categoryCheckbox && categoryCheckbox.checked) {
                        populateOptionsForCategory(category, optionsContainer);
                    }
                })
                .catch(error => {
                    console.error(`Error fetching options for ${category}:`, error);
                    // Create an empty array for this category so we don't keep trying to fetch
                    finishingOptionsData[category] = [];
                });
        }
    }
    
    function populateOptionsForCategory(category, container) {
        // Check if we have options data for this category
        if (finishingOptionsData[category] && finishingOptionsData[category].length > 0) {
            const options = finishingOptionsData[category];
            container.innerHTML = ''; // Clear container
            
            // Create a dropdown for the options
            const selectGroup = document.createElement('div');
            selectGroup.className = 'mb-3';
            
            const selectLabel = document.createElement('label');
            selectLabel.className = 'form-label';
            selectLabel.textContent = `${category} Options`;
            selectGroup.appendChild(selectLabel);
            
            const select = document.createElement('select');
            select.className = 'form-select finishing-option-select';
            select.dataset.category = category;
            
            // Add options
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = `Select ${category} option...`;
            select.appendChild(defaultOption);
            
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.id;
                optElement.textContent = option.name;
                optElement.dataset.basePrice = option.base_price || 0;
                optElement.dataset.pricePerPiece = option.price_per_piece || 0;
                optElement.dataset.pricePerSqft = option.price_per_sqft || 0;
                optElement.dataset.minimumPrice = option.minimum_price || 0;
                select.appendChild(optElement);
            });
            
            selectGroup.appendChild(select);
            container.appendChild(selectGroup);
            
            // Event listener for option selection
            select.addEventListener('change', function() {
                const selectedOption = this.options[this.selectedIndex];
                const optionId = this.value;
                
                // Remove previous option for this category
                selectedFinishingOptions = selectedFinishingOptions.filter(opt => opt.category !== category);
                
                // Add the new selection if an option was selected
                if (optionId) {
                    const option = options.find(o => o.id == optionId);
                    if (option) {
                        selectedFinishingOptions.push({
                            id: option.id,
                            name: option.name,
                            category: category,
                            basePrice: option.base_price || 0,
                            pricePerPiece: option.price_per_piece || 0,
                            pricePerSqft: option.price_per_sqft || 0,
                            minimumPrice: option.minimum_price || 0
                        });
                    }
                }
                
                // Update price calculations
                updateCalculations();
            });
        } else {
            // If we don't have data yet, show loading
            container.innerHTML = '<div class="text-muted small">Loading options...</div>';
            
            // Try to fetch the options
            fetchFinishingOptionsForCategory(category);
            
            // Set a timeout to check again in 500ms
            setTimeout(() => {
                populateOptionsForCategory(category, container);
            }, 500);
        }
    }
    
    function setupPresetButtons() {
        // B&W Copies preset
        if (presetBWCopiesBtn) {
            presetBWCopiesBtn.addEventListener('click', function() {
                setupPreset('B&W Copies', 100, 'Letter', 'Bond', '20#', 'White', 'B/W', 'Single', 1, 0.10);
            });
        }
        
        // Color Copies preset
        if (presetColorCopiesBtn) {
            presetColorCopiesBtn.addEventListener('click', function() {
                setupPreset('Color Copies', 100, 'Letter', 'Bond', '20#', 'White', 'Color', 'Single', 1, 0.59);
            });
        }
        
        // Business Cards preset
        if (presetBusinessCardsBtn) {
            presetBusinessCardsBtn.addEventListener('click', function() {
                setupPreset('Business Cards', 100, 'Business Card', 'Cardstock', '100#', 'White', 'Color', 'Double', 1, 0.25);
            });
        }
        
        // Flyers preset
        if (presetFlyersBtn) {
            presetFlyersBtn.addEventListener('click', function() {
                setupPreset('Color Flyers', 100, 'Letter', 'Gloss', '80#', 'White', 'Color', 'Single', 1, 0.45);
            });
        }
    }
    
    function setupPreset(name, quantity, paperSize, paperType, paperWeight, paperColor, printType, sides, nUp, unitPrice) {
        // Set basic fields
        if (nameInput) nameInput.value = name;
        if (quantityInput) {
            quantityInput.value = quantity;
            if (quantityDisplay) quantityDisplay.textContent = quantity;
        }
        
        // Set paper options
        if (paperSizeSelect) paperSizeSelect.value = paperSize;
        if (paperTypeSelect) paperTypeSelect.value = paperType;
        if (paperWeightSelect) paperWeightSelect.value = paperWeight;
        if (paperColorSelect) paperColorSelect.value = paperColor;
        
        // Set print options
        if (printTypeBW && printTypeColor) {
            printTypeBW.checked = (printType === 'B/W');
            printTypeColor.checked = (printType === 'Color');
        }
        
        if (sidesSingle && sidesDouble) {
            sidesSingle.checked = (sides === 'Single');
            sidesDouble.checked = (sides === 'Double');
        }
        
        if (nUpSelect) nUpSelect.value = nUp;
        
        // Clear finishing options - legacy checkboxes
        finishingOptions.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Clear dynamic finishing options
        const categoryCheckboxes = document.querySelectorAll('.category-toggle');
        categoryCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            // Collapse any open dropdowns
            const categoryId = checkbox.dataset.category.replace(/\s+/g, '-').toLowerCase();
            const collapseDiv = document.getElementById(`collapse-${categoryId}`);
            if (collapseDiv) {
                collapseDiv.classList.remove('show');
            }
        });
        
        // Clear selected options array
        selectedFinishingOptions = [];
        
        // Set price
        if (unitPriceInput) {
            unitPriceInput.value = unitPrice.toFixed(2);
            if (unitPriceDisplay) unitPriceDisplay.textContent = unitPrice.toFixed(2);
        }
        
        // Update calculations
        updateCalculations();
    }
    
    // Make updateCalculations accessible globally for the finishing options script
    function updateCalculations() {
        console.log("Running updateCalculations in simple_quote_calculator.js");
        
        // Get current form values
        const paperSize = paperSizeSelect ? paperSizeSelect.value : '';
        const paperType = paperTypeSelect ? paperTypeSelect.value : '';
        const paperWeight = paperWeightSelect ? paperWeightSelect.value : '';
        const paperColor = paperColorSelect ? paperColorSelect.value : '';
        const printType = printTypeBW && printTypeBW.checked ? 'B/W' : 'Color';
        const sides = sidesSingle && sidesSingle.checked ? 'Single' : 'Double';
        const nUp = nUpSelect ? parseInt(nUpSelect.value) || 1 : 1;
        const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
        
        // Look up paper option in database
        const paperOption = findPaperOption(paperSize, paperType, paperWeight, paperColor);
        console.log("Finding paper option:", paperSize, paperType, paperWeight, paperColor);
        console.log("Found paper option:", paperOption);
        
        // Look up print pricing in database
        const printPrice = findPrintPrice(printType, paperType);
        console.log("Finding print price for:", printType, paperType);
        console.log("Found print price:", printPrice);
        
        // Calculate costs
        let basePrice = 0;
        let paperCost = calculatePaperCost(paperOption, sides);
        let printingCost = calculatePrintingCost(printPrice, sides, nUp);
        let finishingCost = calculateFinishingCost();
        
        // Calculate unit price based on costs with standard markup
        const calculatedPrice = (paperCost + printingCost + finishingCost) * 2.5; // 150% markup
        
        // Calculate total costs for display
        const totalPaperCost = paperCost * quantity;
        const totalPrintingCost = printingCost * quantity;
        const totalFinishingCost = finishingCost * quantity;
        
        // Update display elements
        if (basePriceDisplay) basePriceDisplay.textContent = basePrice.toFixed(2);
        if (paperCostDisplay) paperCostDisplay.textContent = totalPaperCost.toFixed(2);
        if (printingCostDisplay) printingCostDisplay.textContent = totalPrintingCost.toFixed(2);
        if (finishingCostDisplay) finishingCostDisplay.textContent = totalFinishingCost.toFixed(2);
        
        // Update calculated price field and button data
        if (calculatedPriceField) {
            calculatedPriceField.value = calculatedPrice.toFixed(2);
            console.log("Updated calculated price to:", calculatedPrice.toFixed(2));
            
            // Also update calculated-price-display if it exists
            const calcPriceDisplay = document.getElementById('calculated-price-display');
            if (calcPriceDisplay) {
                calcPriceDisplay.textContent = calculatedPrice.toFixed(2);
            }
            
            // Update button data attribute with price AND print settings
            const useCalcPriceBtn = document.getElementById('use_calculated_price');
            if (useCalcPriceBtn) {
                useCalcPriceBtn.setAttribute('data-price', calculatedPrice.toFixed(2));
                useCalcPriceBtn.setAttribute('data-print-type', printType);
                useCalcPriceBtn.setAttribute('data-sides', sides);
                useCalcPriceBtn.setAttribute('data-n-up', nUp);
                console.log("Updated button data with print type:", printType, "sides:", sides);
            }
            
            // Also update the hidden field if it exists
            const calculatedPriceHidden = document.getElementById('calculated_price_hidden');
            if (calculatedPriceHidden) {
                calculatedPriceHidden.value = calculatedPrice.toFixed(2);
            }
        }
        
        // Update the total price based on the actual unit price entered
        updateTotalPrice();
    }
    
    function findPaperOption(size, type, weight, color) {
        if (!paperOptionsData.length) return null;
        
        // First try to find an exact match
        let option = paperOptionsData.find(p => 
            p.size === size && 
            (p.type === type || p.category === type) && 
            p.weight === weight && 
            p.color === color
        );
        
        // If not found, try with just size, type and weight
        if (!option) {
            option = paperOptionsData.find(p => 
                p.size === size && 
                (p.type === type || p.category === type) && 
                p.weight === weight
            );
        }
        
        // If still not found, try with just size and type
        if (!option) {
            option = paperOptionsData.find(p => 
                p.size === size && 
                (p.type === type || p.category === type)
            );
        }
        
        return option;
    }
    
    function findPrintPrice(printType, paperType) {
        if (!printPricingData.length) return null;
        
        // Try to find an exact match for print type and paper type
        let price = printPricingData.find(p => 
            p.color === printType && 
            p.paper_type === paperType
        );
        
        // If not found, try just by print type
        if (!price) {
            price = printPricingData.find(p => p.color === printType);
        }
        
        return price;
    }
    
    function calculatePaperCost(paperOption, sides) {
        if (!paperOption) return 0.05; // Default paper cost if no option found
        
        let cost = 0;
        
        // If paper has sheet pricing
        if (paperOption.cost_per_sheet > 0) {
            cost = paperOption.cost_per_sheet;
        } 
        // If paper has sqft pricing and dimensions
        else if (paperOption.cost_per_sqft > 0 && paperOption.width > 0 && paperOption.height > 0) {
            // Convert to square feet and calculate
            const sqft = (paperOption.width * paperOption.height) / 144; // 144 sq inches per sq ft
            cost = paperOption.cost_per_sqft * sqft;
        }
        // Use default retail price
        else if (paperOption.price_per_sheet > 0) {
            cost = paperOption.price_per_sheet * 0.4; // 40% of retail for cost estimate
        }
        // Default minimal cost if nothing else available
        else {
            cost = 0.05;
        }
        
        // Double-sided uses two sheets
        if (sides === 'Double') {
            // For duplex, we don't double the cost, just add 80% more
            cost = cost * 1.8;
        }
        
        return cost;
    }
    
    function calculatePrintingCost(printPrice, sides, nUp) {
        // Default costs if no pricing found
        let baseCost = 0;
        let perPageCost = printPrice && printPrice.color === 'B/W' ? 0.03 : 0.25;
        
        // If we found a price in the database, use that
        if (printPrice) {
            baseCost = printPrice.base_price || 0;
            perPageCost = printPrice.per_page_price || perPageCost;
            
            // If duplex is indicated in the print price
            if (printPrice.duplex && sides === 'Double') {
                // Use the duplex price directly
                return baseCost + perPageCost;
            }
        }
        
        // Adjust for sides
        if (sides === 'Double') {
            perPageCost = perPageCost * 1.8; // 80% more for double-sided
        }
        
        // Adjust for n-up
        if (nUp > 1) {
            // N-up is more complex, so there's a slight upcharge per impression
            // but divided by the number of pages being printed
            perPageCost = (perPageCost * (1 + (nUp * 0.1))) / nUp;
        }
        
        return baseCost + perPageCost;
    }
    
    function calculateFinishingCost() {
        // Use window.selectedFinishingOptions if available, otherwise fall back to local array
        const optionsToUse = window.selectedFinishingOptions || selectedFinishingOptions || [];
        
        // If no finishing options selected, return 0
        if (!optionsToUse || optionsToUse.length === 0) {
            return 0;
        }
        
        console.log("Calculating finishing cost using options:", optionsToUse);
        
        // Get current quantity
        const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
        
        // Calculate cost for each selected finishing option
        let totalFinishingCost = 0;
        
        optionsToUse.forEach(option => {
            // First, apply base price
            let optionCost = option.basePrice || 0;
            
            // Then add per-piece cost if applicable
            if (option.pricePerPiece && option.pricePerPiece > 0) {
                optionCost += option.pricePerPiece * quantity;
            }
            
            // Ensure minimum price is met
            if (option.minimumPrice && optionCost < option.minimumPrice) {
                optionCost = option.minimumPrice;
            }
            
            totalFinishingCost += optionCost;
        });
        
        // Return cost per unit
        return totalFinishingCost / quantity;
    }
    
    function updateTotalPrice() {
        const quantity = quantityInput ? parseInt(quantityInput.value) || 1 : 1;
        const unitPrice = unitPriceInput ? parseFloat(unitPriceInput.value) || 0 : 0;
        const total = quantity * unitPrice;
        
        if (totalPriceDisplay) {
            totalPriceDisplay.textContent = total.toFixed(2);
        }
    }
});