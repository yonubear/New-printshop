/**
 * Quote Item Price Calculator
 * Handles automatic calculations for quote items based on selected options
 * Implements a workflow that:
 * 1. First selects a finished size
 * 2. Shows paper options that are that size or larger
 * 3. Allows choosing weight based on standard options and database
 * 4. Filters paper type options
 * 5. Enables n-up options when finished size is smaller than paper size
 * 6. Calculates price based on paper size and color using print pricing database
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("Quote item calculator beginning initialization");
    
    // Check if we are on the quote item form page by looking for any of our form elements
    const regularForm = document.getElementById('regular-print-form');
    const bookletForm = document.getElementById('booklet-form');
    const notepadForm = document.getElementById('notepad-form');
    
    console.log("Found forms:", 
        regularForm ? "regular-print-form ✓" : "regular-print-form ✗", 
        bookletForm ? "booklet-form ✓" : "booklet-form ✗", 
        notepadForm ? "notepad-form ✓" : "notepad-form ✗");
    
    if (!regularForm && !bookletForm && !notepadForm) {
        console.log("Not on quote item form page");
        return;
    }
    
    console.log("Quote item calculator initialized");
    
    // Form elements
    const productTypeSelect = document.getElementById('product_type');
    const quantityInput = document.getElementById('quantity');
    const unitPriceInput = document.getElementById('unit_price');
    const totalPriceDisplay = document.getElementById('total_price_display');
    const calculatedPriceDisplay = document.getElementById('calculated_price');
    
    // Paper option selectors
    const paperSizeSelect = document.getElementById('paper_size');
    const paperTypeSelect = document.getElementById('paper_type');
    const paperWeightSelect = document.getElementById('paper_weight');
    const printTypeSelect = document.getElementById('print_type');
    const paperColorSelect = document.getElementById('paper_color');
    const nUpSelect = document.getElementById('n_up');
    
    // Booklet specific fields
    const pagesInput = document.getElementById('booklet_pages');
    const selfCoverCheckbox = document.getElementById('self_cover');
    const bindingSelect = document.getElementById('binding');
    const coverTypeSelect = document.getElementById('booklet_cover_type');
    const coverWeightSelect = document.getElementById('booklet_cover_weight');
    
    // Notepad specific fields
    const sheetsInput = document.getElementById('notepad_sheets');
    const backingCheckbox = document.getElementById('backing');
    const partsInput = document.getElementById('notepad_parts');
    
    // Define standard finished sizes with dimensions (in inches)
    const standardSizes = {
        'Letter': { width: 8.5, height: 11 },
        'Legal': { width: 8.5, height: 14 },
        'Tabloid': { width: 11, height: 17 },
        'Half Letter': { width: 5.5, height: 8.5 },
        'Quarter Letter': { width: 4.25, height: 5.5 },
        'A4': { width: 8.27, height: 11.69 },
        'A5': { width: 5.83, height: 8.27 },
        'A3': { width: 11.69, height: 16.54 },
        'Business Card': { width: 3.5, height: 2 },
        'Postcard': { width: 4, height: 6 },
        'Roll': { width: 24, height: 36 } // Example roll size
    };
    
    // Standard paper weights by type
    const standardWeights = {
        'Bond': ['16#', '20#', '24#', '28#', '32#'],
        'Text': ['60#', '70#', '80#', '100#'],
        'Cover': ['65#', '80#', '100#', '120#'],
        'Cardstock': ['80#', '100#', '110#', '130#'],
        'NCR': ['20#'],
        'Gloss': ['80#', '100#', '120#'],
        'Matte': ['80#', '100#', '120#']
    };
    
    // Finishing options
    const finishingOptions = document.querySelectorAll('input[name="finishing_options"]');
    
    // Store paper options data
    let paperOptionsData = [];
    let printPricingData = [];
    
    // Fetch paper options data and populate dropdowns
    function fetchPaperOptionData() {
        console.log('Fetching paper options data from API...');
        
        // Check for CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        fetch('/api/paper-options', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'same-origin'
        })
            .then(response => {
                console.log('Paper options API response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                paperOptionsData = data;
                console.log('Paper options loaded successfully:', data.length, data);
                
                // Populate paper type dropdowns
                populatePaperTypeDropdowns(data);
                
                // Set up change event listeners for paper type selectors
                setupPaperTypeChangeListeners();
                
                // Initial population of dependent dropdowns
                if (paperTypeSelect && paperTypeSelect.value) {
                    updatePaperWeightOptions(paperTypeSelect.value, paperWeightSelect);
                    updatePaperColorOptions(paperTypeSelect.value, paperColorSelect);
                }
                
                if (coverTypeSelect && coverTypeSelect.value) {
                    updatePaperWeightOptions(coverTypeSelect.value, coverWeightSelect);
                }
                
                calculatePrice();
            })
            .catch(error => console.error('Error loading paper options:', error));
    }
    
    // Fetch print pricing data
    function fetchPrintPricingData() {
        console.log('Fetching print pricing data from API...');
        
        // Check for CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        fetch('/api/print-pricing', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken || ''
            },
            credentials: 'same-origin'
        })
            .then(response => {
                console.log('Print pricing API response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                printPricingData = data;
                console.log('Print pricing loaded successfully:', data.length, data);
                calculatePrice();
            })
            .catch(error => console.error('Error loading print pricing:', error));
    }
    
    // Populate paper type dropdowns with unique values from the API
    function populatePaperTypeDropdowns(paperOptions) {
        // Log full paper options to debug
        console.log('Paper options data:', paperOptions);
        
        // Get unique paper types (categories)
        const uniqueTypes = [...new Set(paperOptions.map(option => option.type || option.category).filter(Boolean))];
        
        console.log('Unique paper types:', uniqueTypes);
        
        // Populate regular print form dropdown
        if (paperTypeSelect) {
            // Save current value if any
            const currentValue = paperTypeSelect.value;
            
            // Clear dropdown except for the first option
            while (paperTypeSelect.options.length > 1) {
                paperTypeSelect.remove(1);
            }
            
            // Add new options
            uniqueTypes.forEach(type => {
                if (type) { // Skip null or undefined values
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    paperTypeSelect.appendChild(option);
                }
            });
            
            // Restore selected value if it still exists
            if (currentValue && uniqueTypes.includes(currentValue)) {
                paperTypeSelect.value = currentValue;
            }
        }
        
        // Populate booklet cover type dropdown
        if (coverTypeSelect) {
            // Save current value if any
            const currentValue = coverTypeSelect.value;
            
            // Clear dropdown except for the first option
            while (coverTypeSelect.options.length > 1) {
                coverTypeSelect.remove(1);
            }
            
            // Add self-cover option first
            const selfCoverOption = document.createElement('option');
            selfCoverOption.value = 'None';
            selfCoverOption.textContent = 'Same as Inside (Self Cover)';
            coverTypeSelect.appendChild(selfCoverOption);
            
            // Add other options
            uniqueTypes.forEach(type => {
                // Skip Bond for covers as it's not typically used
                if (type !== 'Bond') {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    coverTypeSelect.appendChild(option);
                }
            });
            
            // Restore selected value if it still exists
            if (currentValue && (currentValue === 'None' || uniqueTypes.includes(currentValue))) {
                coverTypeSelect.value = currentValue;
            }
        }
        
        // Populate notepad paper type dropdown in a similar way
        // (implementation would be similar to above)
    }
    
    // Update paper weight options based on selected paper type
    function updatePaperWeightOptions(paperType, weightDropdown) {
        if (!weightDropdown) return;
        
        console.log('Updating paper weight options for type:', paperType);
        
        // Get all weights for the selected paper type - try both type and category fields
        const weights = paperOptionsData
            .filter(option => (option.type === paperType || option.category === paperType))
            .map(option => option.weight)
            .filter(weight => weight); // Remove empty values
        
        console.log('Available weights for selected type:', weights);
        
        // Get unique weights
        const uniqueWeights = [...new Set(weights)];
        
        // Save current value if any
        const currentValue = weightDropdown.value;
        
        // Clear dropdown except for the first option
        while (weightDropdown.options.length > 1) {
            weightDropdown.remove(1);
        }
        
        // Add new options
        uniqueWeights.forEach(weight => {
            const option = document.createElement('option');
            option.value = weight;
            option.textContent = weight;
            weightDropdown.appendChild(option);
        });
        
        // Restore selected value if it still exists
        if (currentValue && uniqueWeights.includes(currentValue)) {
            weightDropdown.value = currentValue;
        }
    }
    
    // Update paper color options based on selected paper type
    function updatePaperColorOptions(paperType, colorDropdown) {
        if (!colorDropdown) return;
        
        console.log('Updating paper color options for type:', paperType);
        
        // Get all colors for the selected paper type - try both type and category fields
        const colors = paperOptionsData
            .filter(option => (option.type === paperType || option.category === paperType))
            .map(option => option.color)
            .filter(color => color); // Remove empty values
        
        // Get unique colors
        const uniqueColors = [...new Set(colors)];
        
        // Save current value if any
        const currentValue = colorDropdown.value;
        
        // Clear dropdown except for the first option
        while (colorDropdown.options.length > 1) {
            colorDropdown.remove(1);
        }
        
        // Add new options
        uniqueColors.forEach(color => {
            const option = document.createElement('option');
            option.value = color;
            option.textContent = color;
            colorDropdown.appendChild(option);
        });
        
        // Restore selected value if it still exists
        if (currentValue && uniqueColors.includes(currentValue)) {
            colorDropdown.value = currentValue;
        }
    }
    
    // Setup change event listeners for paper size selectors
    function setupPaperSizeChangeListeners() {
        // For regular print form
        if (paperSizeSelect) {
            paperSizeSelect.addEventListener('change', function() {
                // When finished size changes, update available paper types
                filterPaperTypesBySize(this.value, paperTypeSelect);
                // Calculate which n-up options should be available based on size
                updateNUpOptions(this.value, nUpSelect);
                calculatePrice();
            });
        }
        
        // For booklet form
        if (document.getElementById('booklet_size')) {
            document.getElementById('booklet_size').addEventListener('change', function() {
                // Filter paper types appropriate for booklet of this size
                filterPaperTypesBySize(this.value, document.getElementById('booklet_paper_type'));
                calculatePrice();
            });
        }
        
        // For notepad form
        if (document.getElementById('notepad_size')) {
            document.getElementById('notepad_size').addEventListener('change', function() {
                // Filter paper types appropriate for notepad of this size
                filterPaperTypesBySize(this.value, document.getElementById('notepad_type'));
                calculatePrice();
            });
        }
    }
    
    // Filter paper types based on finished size (show only papers that are this size or larger)
    function filterPaperTypesBySize(finishedSize, typeDropdown) {
        if (!finishedSize || !typeDropdown || !standardSizes[finishedSize]) return;
        
        console.log('Filtering paper types by finished size:', finishedSize);
        
        // Get dimensions of the finished size
        const finishedDimensions = standardSizes[finishedSize];
        
        // Get paper types that are this size or larger
        let compatiblePaperTypes = new Set();
        
        paperOptionsData.forEach(option => {
            let paperType = option.type || option.category;
            if (!paperType) return;
            
            // For specific sized papers, check dimensions
            if (option.size && option.size !== 'Roll' && option.size !== 'Custom') {
                // If this paper option has a standard size, check if it can accommodate the finished size
                if (standardSizes[option.size]) {
                    const paperDimensions = standardSizes[option.size];
                    // Paper can fit finished size if both dimensions are at least as large
                    // (or if rotated, width becomes height and vice versa)
                    if ((paperDimensions.width >= finishedDimensions.width && 
                         paperDimensions.height >= finishedDimensions.height) ||
                        (paperDimensions.width >= finishedDimensions.height && 
                         paperDimensions.height >= finishedDimensions.width)) {
                        compatiblePaperTypes.add(paperType);
                    }
                }
            } 
            // Roll paper can always accommodate any size
            else if (option.size === 'Roll' || option.is_roll) {
                compatiblePaperTypes.add(paperType);
            }
            // For papers with explicit width/height in the database
            else if (option.width && option.height) {
                if ((option.width >= finishedDimensions.width && 
                     option.height >= finishedDimensions.height) ||
                    (option.width >= finishedDimensions.height && 
                     option.height >= finishedDimensions.width)) {
                    compatiblePaperTypes.add(paperType);
                }
            }
            // If no size info is available, include it by default
            else {
                compatiblePaperTypes.add(paperType);
            }
        });
        
        // Convert to array and update dropdown
        const compatibleTypes = Array.from(compatiblePaperTypes);
        console.log('Compatible paper types for this size:', compatibleTypes);
        
        // Save current value if any
        const currentValue = typeDropdown.value;
        
        // Clear dropdown except for the first option
        while (typeDropdown.options.length > 1) {
            typeDropdown.remove(1);
        }
        
        // Add new options
        compatibleTypes.forEach(type => {
            if (type) { // Skip null or undefined values
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeDropdown.appendChild(option);
            }
        });
        
        // Restore selected value if it still exists
        if (currentValue && compatibleTypes.includes(currentValue)) {
            typeDropdown.value = currentValue;
        }
    }
    
    // Update N-up options based on selected finished size and paper size
    function updateNUpOptions(finishedSize, nUpDropdown) {
        if (!finishedSize || !nUpDropdown || !standardSizes[finishedSize]) return;
        
        console.log('Updating N-up options for size:', finishedSize);
        
        // Get dimensions of the finished size
        const finishedDimensions = standardSizes[finishedSize];
        
        // Initially disable all n-up options except 1-up
        // Save current value
        const currentValue = nUpDropdown.value;
        
        // Clear dropdown except for the first option (1-up)
        while (nUpDropdown.options.length > 1) {
            nUpDropdown.remove(1);
        }
        
        // Get the selected paper size and dimensions
        const paperSizeValue = paperSizeSelect.value;
        if (!paperSizeValue || !standardSizes[paperSizeValue]) {
            // If no paper size is selected or it's custom, just enable 1-up
            return;
        }
        
        const paperDimensions = standardSizes[paperSizeValue];
        
        // Calculate how many finished pieces can fit on the paper
        // (considering both orientations)
        const fitHorizontal = Math.floor(paperDimensions.width / finishedDimensions.width);
        const fitVertical = Math.floor(paperDimensions.height / finishedDimensions.height);
        const maxHorizontalVertical = fitHorizontal * fitVertical;
        
        const fitHorizontalRotated = Math.floor(paperDimensions.width / finishedDimensions.height);
        const fitVerticalRotated = Math.floor(paperDimensions.height / finishedDimensions.width);
        const maxRotated = fitHorizontalRotated * fitVerticalRotated;
        
        const maxFit = Math.max(maxHorizontalVertical, maxRotated);
        
        // Standard n-up options
        const nUpOptions = [1, 2, 4, 8, 9, 16];
        
        // Add appropriate n-up options
        nUpOptions.forEach(option => {
            if (option <= maxFit) {
                const nUpOption = document.createElement('option');
                nUpOption.value = option;
                nUpOption.textContent = `${option}-up`;
                nUpDropdown.appendChild(nUpOption);
            }
        });
        
        // Restore selected value if it still exists and is valid
        if (currentValue && parseInt(currentValue) <= maxFit) {
            nUpDropdown.value = currentValue;
        } else {
            // Default to 1-up if previous selection is no longer valid
            nUpDropdown.value = '1';
        }
    }
    
    // Setup change event listeners for paper type selectors
    function setupPaperTypeChangeListeners() {
        // For regular print form
        if (paperTypeSelect) {
            paperTypeSelect.addEventListener('change', function() {
                updatePaperWeightOptions(this.value, paperWeightSelect);
                updatePaperColorOptions(this.value, paperColorSelect);
                calculatePrice();
            });
        }
        
        // For booklet form
        if (coverTypeSelect) {
            coverTypeSelect.addEventListener('change', function() {
                if (this.value !== 'None') {
                    updatePaperWeightOptions(this.value, coverWeightSelect);
                }
                calculatePrice();
            });
        }
        
        // For notepad form (similar to regular print form)
        // (implementation would be similar to above)
    }
    
    // Initialize data
    console.log("Initializing data fetching");
    fetchPaperOptionData();
    fetchPrintPricingData();
    
    // Set up the listeners for paper size changes
    setupPaperSizeChangeListeners();
    
    // Add event listeners to form elements
    addEventListeners();
    function addEventListeners() {
        // Set up the "Use Calculated Price" button
        const useCalculatedPriceBtn = document.getElementById('use_calculated_price');
        if (useCalculatedPriceBtn) {
            console.log('Found Use Calculated Price button, setting up listener');
            useCalculatedPriceBtn.addEventListener('click', function() {
                const unitPrice = document.getElementById('unit_price');
                const unitPriceDisplay = document.getElementById('unit_price_display');
                
                // Get the calculated price
                const calculatedPrice = parseFloat(this.getAttribute('data-price')) || 0;
                console.log('Use Calculated Price clicked with price:', calculatedPrice);
                
                // Update unit price input and display
                if (unitPrice) unitPrice.value = calculatedPrice.toFixed(2);
                if (unitPriceDisplay) unitPriceDisplay.textContent = calculatedPrice.toFixed(2);
                
                // Update total price if needed
                const totalPriceDisplay = document.getElementById('total_price_display');
                const quantity = parseInt(document.getElementById('quantity')?.value || 1);
                if (totalPriceDisplay) {
                    totalPriceDisplay.textContent = (calculatedPrice * quantity).toFixed(2);
                }
            });
        }

        // Regular print form fields
        if (regularForm) {
            const regularFormElements = [
                document.getElementById('paper_size'),
                document.getElementById('paper_type'),
                document.getElementById('paper_weight'),
                document.getElementById('print_type'),
                document.getElementById('paper_color'),
                document.getElementById('n_up'),
                document.getElementById('quantity')
            ];
            
            regularFormElements.forEach(element => {
                if (element) {
                    element.addEventListener('change', calculatePrice);
                    element.addEventListener('input', calculatePrice);
                }
            });
        }
        
        // Booklet form fields
        if (bookletForm) {
            const bookletFormElements = [
                document.getElementById('booklet_size'),
                document.getElementById('booklet_pages'),
                document.getElementById('booklet_quantity'),
                document.getElementById('booklet_cover_type'),
                document.getElementById('booklet_cover_weight'),
                document.getElementById('binding')
            ];
            
            bookletFormElements.forEach(element => {
                if (element) {
                    element.addEventListener('change', calculatePrice);
                    element.addEventListener('input', calculatePrice);
                }
            });
        }
        
        // Notepad form fields
        if (notepadForm) {
            const notepadFormElements = [
                document.getElementById('notepad_size'),
                document.getElementById('notepad_type'),
                document.getElementById('notepad_weight'),
                document.getElementById('notepad_sheets'),
                document.getElementById('notepad_quantity'),
                document.getElementById('notepad_parts')
            ];
            
            notepadFormElements.forEach(element => {
                if (element) {
                    element.addEventListener('change', calculatePrice);
                    element.addEventListener('input', calculatePrice);
                }
            });
        }
        
        // Add event listeners to finishing options
        finishingOptions.forEach(option => {
            if (option) {
                option.addEventListener('change', calculatePrice);
            }
        });
        
        // Initial calculation
        calculatePrice();
        
        // We already set up the "Use Calculated Price" button at the beginning of this function
    }
    
    // Calculate price based on selected options
    function calculatePrice() {
        const currentProductType = productTypeSelect ? productTypeSelect.value : 'regular';
        let quantity = 1;
        try {
            quantity = parseInt(quantityInput ? quantityInput.value : 1);
            if (isNaN(quantity) || quantity < 1) quantity = 1;
        } catch (e) {
            console.log('Error parsing quantity:', e);
            quantity = 1;
        }
        
        let nUp = 1;
        try {
            nUp = parseInt(nUpSelect ? nUpSelect.value : 1);
            if (isNaN(nUp) || nUp < 1) nUp = 1;
        } catch (e) {
            console.log('Error parsing n-up value:', e);
            nUp = 1;
        }
        
        console.log('Calculating price for product type:', currentProductType);
        console.log('Quantity:', quantity, 'N-up:', nUp);
        
        let unitPrice = 0.50; // Default unit price to ensure a non-zero value 
        let totalPrice = 0;
        
        // Get selected paper options
        const paperSize = paperSizeSelect ? paperSizeSelect.value : '';
        const paperType = paperTypeSelect ? paperTypeSelect.value : '';
        const paperWeight = paperWeightSelect ? paperWeightSelect.value : '';
        
        console.log('Selected paper options:', paperSize, paperType, paperWeight);
        
        // Get print type from radio buttons
        let printType = 'B/W'; // Default to B/W
        const printTypeBW = document.getElementById('print_type_bw');
        const printTypeColor = document.getElementById('print_type_color');
        
        // If we can't get the elements directly, try getting by name
        if (!printTypeBW || !printTypeColor) {
            console.log('Could not find print type radio buttons by ID, trying by name');
            const printTypeRadios = document.querySelectorAll('input[name="print_type"]');
            let foundChecked = false;
            printTypeRadios.forEach(radio => {
                if (radio.checked) {
                    printType = radio.value;
                    foundChecked = true;
                    console.log('Found checked print type by name:', printType);
                }
            });
            
            if (!foundChecked) {
                console.log('No print type radio button was checked, defaulting to B/W');
                // Try to check the B/W radio if it exists
                printTypeRadios.forEach(radio => {
                    if (radio.value === 'B/W') {
                        radio.checked = true;
                        printType = 'B/W';
                    }
                });
            }
        } else {
            if (printTypeBW && printTypeBW.checked) {
                printType = 'B/W';
                console.log('Found checked print type B/W by ID');
            } else if (printTypeColor && printTypeColor.checked) {
                printType = 'Color';
                console.log('Found checked print type Color by ID');
            } else {
                // Default to B/W if nothing is checked and check the radio
                printType = 'B/W';
                if (printTypeBW) printTypeBW.checked = true;
                console.log('No print type checked, defaulting to B/W and checking the radio');
            }
        }
        
        const paperColor = paperColorSelect ? paperColorSelect.value : '';
        
        // Find matching paper option
        const selectedPaper = findPaperOption(paperSize, paperType, paperWeight);
        console.log('Selected paper:', selectedPaper, 'Inputs:', paperSize, paperType, paperWeight);
        
        // Find matching print pricing
        const printPrice = findPrintPrice(printType, paperType);
        console.log('Selected print price:', printPrice, 'Inputs:', printType, paperType);
        
        // Calculate based on product type
        if (currentProductType === 'regular') {
            // Calculate regular print price
            unitPrice = calculateRegularPrintPrice(selectedPaper, printPrice, nUp);
        } else if (currentProductType === 'booklet') {
            // Calculate booklet price
            const pages = parseInt(pagesInput ? pagesInput.value : 4);
            const selfCover = selfCoverCheckbox ? selfCoverCheckbox.checked : false;
            const binding = bindingSelect ? bindingSelect.value : 'Saddle Stitch';
            
            unitPrice = calculateBookletPrice(
                selectedPaper, printPrice, pages, selfCover, binding, 
                coverTypeSelect ? coverTypeSelect.value : '',
                coverWeightSelect ? coverWeightSelect.value : ''
            );
        } else if (currentProductType === 'notepad') {
            // Calculate notepad price
            const sheets = parseInt(sheetsInput ? sheetsInput.value : 50);
            const backing = backingCheckbox ? backingCheckbox.checked : false;
            const parts = parseInt(partsInput ? partsInput.value : 1);
            
            unitPrice = calculateNotepadPrice(selectedPaper, printPrice, sheets, backing, parts);
        }
        
        // Calculate finishing costs
        const finishingCost = calculateFinishingCost(quantity);
        
        // Calculate total price
        totalPrice = (unitPrice * quantity) + finishingCost;
        
        // Update display fields
        if (unitPriceInput) unitPriceInput.value = unitPrice.toFixed(2);
        if (totalPriceDisplay) totalPriceDisplay.textContent = totalPrice.toFixed(2);
        if (calculatedPriceDisplay) {
            // Update both textContent for display elements and value for input elements
            if (calculatedPriceDisplay.tagName === 'INPUT') {
                calculatedPriceDisplay.value = totalPrice.toFixed(2);
            } else {
                calculatedPriceDisplay.textContent = totalPrice.toFixed(2);
            }
        }
        
        // Update the "Use Calculated Price" button's data attributes
        const useCalculatedPriceBtn = document.getElementById('use_calculated_price');
        if (useCalculatedPriceBtn) {
            useCalculatedPriceBtn.setAttribute('data-price', unitPrice.toFixed(2));
            useCalculatedPriceBtn.setAttribute('data-print-type', printType || 'B/W');
            // Check if sides are double or single
            let isDouble = false;
            const sidesDoubleElement = document.getElementById('sides_double');
            
            if (sidesDoubleElement) {
                isDouble = sidesDoubleElement.checked;
                console.log('Found sides_double by ID, checked:', isDouble);
            } else {
                // Try getting by name if ID doesn't work
                const sidesRadios = document.querySelectorAll('input[name="sides"]');
                sidesRadios.forEach(radio => {
                    if (radio.checked && radio.value === 'Double') {
                        isDouble = true;
                        console.log('Found sides by name, Double checked:', isDouble);
                    }
                });
            }
            
            useCalculatedPriceBtn.setAttribute('data-sides', isDouble ? 'Double' : 'Single');
            useCalculatedPriceBtn.setAttribute('data-n-up', nUp);
            console.log("Updated Use Calculated Price button with price:", unitPrice.toFixed(2),
                "print type:", printType || 'B/W',
                "sides:", isDouble ? 'Double' : 'Single',
                "n-up:", nUp);
            
            // Make sure the hidden calculated price field is updated too
            const calculatedPriceHidden = document.getElementById('calculated_price_hidden');
            if (calculatedPriceHidden) {
                calculatedPriceHidden.value = unitPrice.toFixed(2);
            }
        }
        
        // Update more display fields if they exist (for price display card)
        const calculatedUnitPriceDisplay = document.getElementById('calculated_unit_price');
        if (calculatedUnitPriceDisplay) calculatedUnitPriceDisplay.textContent = unitPrice.toFixed(2);
        
        // Update booklet display if we're in booklet mode
        const bookletCalculatedUnitPrice = document.getElementById('booklet_calculated_unit_price');
        const bookletCalculatedPrice = document.getElementById('booklet_calculated_price');
        if (currentProductType === 'booklet') {
            if (bookletCalculatedUnitPrice) bookletCalculatedUnitPrice.textContent = unitPrice.toFixed(2);
            if (bookletCalculatedPrice) bookletCalculatedPrice.textContent = totalPrice.toFixed(2);
        }
        
        // Update notepad display if we're in notepad mode
        const notepadCalculatedUnitPrice = document.getElementById('notepad_calculated_unit_price');
        const notepadCalculatedPrice = document.getElementById('notepad_calculated_price');
        if (currentProductType === 'notepad') {
            if (notepadCalculatedUnitPrice) notepadCalculatedUnitPrice.textContent = unitPrice.toFixed(2);
            if (notepadCalculatedPrice) notepadCalculatedPrice.textContent = totalPrice.toFixed(2);
        }
        
        return totalPrice;
    }
    
    // Find paper option data
    function findPaperOption(size, type, weight) {
        if (!paperOptionsData.length) return null;
        
        console.log('Finding paper option:', size, type, weight);
        
        return paperOptionsData.find(option => 
            option.size === size && 
            (option.category === type || option.type === type) && 
            option.weight === weight
        ) || null;
    }
    
    // Find print pricing data
    function findPrintPrice(color, paperType) {
        if (!printPricingData.length) return null;
        
        console.log('Finding print price for:', color, paperType);
        console.log('Available print pricing data:', printPricingData);
        
        // Debug the actual structure of the data we're getting
        if (printPricingData.length > 0) {
            console.log('Sample print pricing item structure:', Object.keys(printPricingData[0]));
        }
        
        // Try to find with paper_category first
        let match = printPricingData.find(price => 
            price.color === color && 
            (price.paper_category === paperType || price.paper_type === paperType)
        );
        
        // If not found, try with just color
        if (!match) {
            console.log('No exact paper type match, trying just color match');
            match = printPricingData.find(price => 
                price.color === color
            );
        }
        
        // If still not found, use any pricing data available
        if (!match && printPricingData.length > 0) {
            console.log('No color match either, using first available pricing');
            match = printPricingData[0];
        }
        
        console.log('Found print price:', match);
        return match || null;
    }
    
    // Calculate price for regular print jobs
    function calculateRegularPrintPrice(paperOption, printPrice, nUp) {
        // Start with a minimum base price to avoid zero pricing
        let price = 0.25;
        
        console.log('Calculating price with paper option:', paperOption);
        console.log('Print price data:', printPrice);
        
        // Base calculations on available data
        if (paperOption) {
            try {
                // Use appropriate pricing based on pricing method
                if (paperOption.pricing_method === 'sqft' && paperOption.price_per_sqft) {
                    // For square footage pricing, calculate area and multiply by price per sqft
                    const width = parseFloat(paperOption.width) || 8.5;
                    const height = parseFloat(paperOption.height) || 11;
                    console.log('Using sqft pricing with dimensions:', width, 'x', height);
                    const sqft = (width * height) / 144; // Convert square inches to square feet
                    const sqftPrice = parseFloat(paperOption.price_per_sqft) || 1.0;
                    price += sqftPrice * sqft;
                    console.log('Paper cost (sqft):', sqftPrice * sqft);
                } else {
                    // Default to price per sheet
                    const sheetPrice = parseFloat(paperOption.price_per_sheet) || 0.10;
                    price += sheetPrice;
                    console.log('Paper cost (per sheet):', sheetPrice);
                }
            } catch (e) {
                console.error('Error calculating paper price:', e);
                // Use default price if calculation fails
                price += 0.10;
            }
        } else {
            console.log('No paper option found, using default price');
            price += 0.10; // Default basic paper cost
        }
        
        if (printPrice) {
            try {
                // Add base setup charge
                const basePrice = parseFloat(printPrice.base_price) || 0.10;
                price += basePrice;
                console.log('Adding base price:', basePrice);
                
                // Use appropriate pricing based on pricing method
                if (printPrice.pricing_method === 'sqft' && printPrice.price_per_sqft) {
                    // For square footage pricing
                    const paperWidth = paperOption ? (parseFloat(paperOption.width) || 8.5) : 8.5; // Default to letter size
                    const paperHeight = paperOption ? (parseFloat(paperOption.height) || 11) : 11;
                    console.log('Using sqft print pricing with dimensions:', paperWidth, 'x', paperHeight);
                    const sqft = (paperWidth * paperHeight) / 144; // Convert square inches to square feet
                    const sqftPrice = parseFloat(printPrice.price_per_sqft) || 0.20;
                    price += sqftPrice * sqft;
                    console.log('Print cost (sqft):', sqftPrice * sqft);
                } else {
                    // Default to price per side
                    // Add per-page price (adjusted for duplex if applicable)
                    // First, check if we have per_page_price (API format) otherwise try price_per_side (DB field)
                    let perPagePrice = 0;
                    if (printPrice.per_page_price !== undefined) {
                        perPagePrice = parseFloat(printPrice.per_page_price) || 0.15;
                    } else if (printPrice.price_per_side !== undefined) {
                        perPagePrice = parseFloat(printPrice.price_per_side) || 0.15;
                    } else {
                        perPagePrice = 0.15; // Default reasonable price
                    }
                    console.log('Using per-page price:', perPagePrice);
                    
                    // Check if sides_double element exists and is checked
                    const sidesDoubleElement = document.getElementById('sides_double');
                    let isDouble = false;
                    
                    if (sidesDoubleElement && sidesDoubleElement.checked) {
                        isDouble = true;
                    } else {
                        // Try getting by name if ID doesn't work
                        const sidesRadios = document.querySelectorAll('input[name="sides"]');
                        sidesRadios.forEach(radio => {
                            if (radio.checked && radio.value === 'Double') {
                                isDouble = true;
                            }
                        });
                    }
                    
                    console.log('Double-sided printing:', isDouble);
                    
                    if (isDouble) {
                        price += perPagePrice * 2; // Both sides
                        console.log('Print cost (double-sided):', perPagePrice * 2);
                    } else {
                        price += perPagePrice;
                        console.log('Print cost (single-sided):', perPagePrice);
                    }
                }
            } catch (e) {
                console.error('Error calculating print price:', e);
                // Use default price if calculation fails
                price += 0.25; // Default print cost
            }
        } else {
            console.log('No print price data found, using default print cost');
            price += 0.25; // Default basic print cost
        }
        
        // Adjust for n-up printing (reduces material costs)
        if (nUp > 1 && price > 0) {
            // Scale the material cost portion down by the n-up factor
            // We don't reduce labor portion (assume 50% of price is labor)
            const materialPortion = price * 0.5;
            const laborPortion = price * 0.5;
            price = laborPortion + (materialPortion / nUp);
        }
        
        // Apply minimum price
        return Math.max(price, 0.25);
    }
    
    // Calculate price for booklet jobs
    function calculateBookletPrice(paperOption, printPrice, pages, selfCover, binding, coverType, coverWeight) {
        let price = 0;
        
        console.log('Calculating booklet price with paper option:', paperOption);
        console.log('Print price data:', printPrice);
        console.log('Pages:', pages, 'Self cover:', selfCover, 'Binding:', binding, 'Cover type:', coverType, 'Cover weight:', coverWeight);
        
        // Calculate interior pages cost
        const sheetsNeeded = Math.ceil(pages / 4); // 4 pages per sheet in a booklet
        console.log('Sheets needed for booklet:', sheetsNeeded);
        
        if (paperOption && sheetsNeeded) {
            // Use appropriate pricing based on pricing method
            if (paperOption.pricing_method === 'sqft' && paperOption.price_per_sqft) {
                // For square footage pricing, calculate area and multiply by price per sqft
                const width = paperOption.width || 0;
                const height = paperOption.height || 0;
                console.log('Using sqft pricing with dimensions:', width, 'x', height);
                const sqft = (width * height) / 144; // Convert square inches to square feet
                price += (paperOption.price_per_sqft * sqft) * sheetsNeeded;
                console.log('Interior paper cost (sqft):', (paperOption.price_per_sqft * sqft) * sheetsNeeded);
            } else {
                // Default to price per sheet
                price += (paperOption.price_per_sheet || 0) * sheetsNeeded;
                console.log('Interior paper cost (per sheet):', (paperOption.price_per_sheet || 0) * sheetsNeeded);
            }
        } else {
            console.log('No paper option found or no sheets needed, using default price');
            price += 0.05 * Math.max(1, sheetsNeeded); // Default basic paper cost per sheet
        }
        
        if (printPrice) {
            // Add base price once
            price += printPrice.base_price || 0;
            console.log('Adding base price:', printPrice.base_price || 0);
            
            // Add per-page price for all pages (always duplex for booklets)
            // First, check if we have per_page_price (API format) otherwise try price_per_side (DB field)
            const perPagePrice = printPrice.per_page_price || printPrice.price_per_side || 0;
            
            if (perPagePrice > 0) {
                price += perPagePrice * pages;
                console.log('Interior print cost:', perPagePrice * pages);
            } else {
                console.log('No per-page price found in print price data');
                // Apply a default printing cost as fallback
                price += 0.10 * pages; // Basic per-page print cost
            }
        } else {
            console.log('No print price data found, using default print cost');
            price += 0.10 * pages; // Default basic print cost per page
        }
        
        // Add cover costs if not self-cover
        if (!selfCover) {
            // Find cover paper option
            const coverPaperOption = paperOptionsData.find(option => 
                (option.category === coverType || option.type === coverType) && 
                option.weight === coverWeight
            );
            
            if (coverPaperOption) {
                // Calculate cover paper cost with appropriate pricing method
                if (coverPaperOption.pricing_method === 'sqft' && coverPaperOption.price_per_sqft) {
                    const width = coverPaperOption.width || 0;
                    const height = coverPaperOption.height || 0;
                    const sqft = (width * height) / 144; // Convert square inches to square feet
                    price += coverPaperOption.price_per_sqft * sqft;
                } else {
                    price += coverPaperOption.price_per_sheet || 0;
                }
                
                // Assume cover is printed in color
                // Try to find print price with both paper_category and paper_type
                let coverPrintPrice = printPricingData.find(price => 
                    price.color === 'Color' && 
                    price.paper_category === coverType
                );
                
                // Fallback to paper_type if needed
                if (!coverPrintPrice) {
                    coverPrintPrice = printPricingData.find(price => 
                        price.color === 'Color' && 
                        price.paper_type === coverType
                    );
                }
                
                if (coverPrintPrice) {
                    price += coverPrintPrice.base_price || 0;
                    
                    // Cover printing - use appropriate pricing method
                    if (coverPrintPrice.pricing_method === 'sqft' && coverPrintPrice.price_per_sqft) {
                        // For square footage pricing
                        const paperWidth = coverPaperOption ? (coverPaperOption.width || 0) : 0;
                        const paperHeight = coverPaperOption ? (coverPaperOption.height || 0) : 0;
                        const sqft = (paperWidth * paperHeight) / 144; // Convert square inches to square feet
                        price += coverPrintPrice.price_per_sqft * sqft;
                    } else if (coverPrintPrice.per_page_price) {
                        // Default to per-page pricing (both sides)
                        price += coverPrintPrice.per_page_price * 2;
                    }
                }
            }
        }
        
        // Add binding cost
        if (binding === 'Saddle Stitch') {
            price += 1.50; // Base cost for saddle stitching
            // Add per-signature cost for thicker booklets
            const signatures = Math.ceil(sheetsNeeded / 5);
            if (signatures > 1) {
                price += (signatures - 1) * 0.50;
            }
        } else if (binding === 'Coil') {
            price += 2.50;
            // Thicker books need more expensive coils
            if (pages > 60) {
                price += Math.ceil((pages - 60) / 30) * 0.75;
            }
        } else if (binding === 'Perfect Bound') {
            price += 5.00; // Base cost for perfect binding
            // Add per-signature cost for thicker books
            price += (sheetsNeeded * 0.10);
        }
        
        // Apply minimum price
        return Math.max(price, 1.00);
    }
    
    // Calculate price for notepad jobs
    function calculateNotepadPrice(paperOption, printPrice, sheets, backing, parts) {
        let price = 0;
        
        console.log('Calculating notepad price with paper option:', paperOption);
        console.log('Print price data:', printPrice);
        console.log('Sheets:', sheets, 'Backing:', backing, 'Parts:', parts);
        
        // Calculate paper cost
        if (paperOption && sheets) {
            // Use appropriate pricing based on pricing method
            if (paperOption.pricing_method === 'sqft' && paperOption.price_per_sqft) {
                // For square footage pricing, calculate area and multiply by price per sqft
                const width = paperOption.width || 0;
                const height = paperOption.height || 0;
                console.log('Using sqft pricing with dimensions:', width, 'x', height);
                const sqft = (width * height) / 144; // Convert square inches to square feet
                price += (paperOption.price_per_sqft * sqft) * sheets;
                console.log('Paper cost (sqft):', (paperOption.price_per_sqft * sqft) * sheets);
            } else {
                // Default to price per sheet
                price += (paperOption.price_per_sheet || 0) * sheets;
                console.log('Paper cost (per sheet):', (paperOption.price_per_sheet || 0) * sheets);
            }
        } else {
            console.log('No paper option found or no sheets specified, using default price');
            price += 0.05 * Math.max(1, sheets || 50); // Default basic paper cost
        }
        
        if (printPrice) {
            // Add base price once
            price += printPrice.base_price || 0;
            console.log('Adding base price:', printPrice.base_price || 0);
            
            // For notepads, we only print one side
            // First, check if we have per_page_price (API format) otherwise try price_per_side (DB field)
            const perPagePrice = printPrice.per_page_price || printPrice.price_per_side || 0;
            
            if (printPrice.pricing_method === 'sqft' && printPrice.price_per_sqft) {
                // For square footage pricing
                const paperWidth = paperOption ? (paperOption.width || 0) : 8.5; // Default to letter size
                const paperHeight = paperOption ? (paperOption.height || 0) : 11;
                console.log('Using sqft print pricing with dimensions:', paperWidth, 'x', paperHeight);
                const sqft = (paperWidth * paperHeight) / 144; // Convert square inches to square feet
                price += printPrice.price_per_sqft * sqft * sheets;
                console.log('Print cost (sqft):', printPrice.price_per_sqft * sqft * sheets);
            } else if (perPagePrice > 0) {
                // Default to per-page pricing for one side
                price += perPagePrice * sheets;
                console.log('Print cost (per page):', perPagePrice * sheets);
            } else {
                console.log('No printing cost found in data, using default');
                price += 0.10 * sheets; // Default cost
            }
        } else {
            console.log('No print price data found, using default print cost');
            price += 0.10 * Math.max(1, sheets || 50); // Default basic print cost for one side
        }
        
        // Multiply by number of parts for NCR paper
        if (parts > 1 && paperOption && (paperOption.category === 'NCR' || paperOption.type === 'NCR')) {
            price *= parts;
            // Add interleaving cost
            price += (parts - 1) * 0.01 * sheets;
        }
        
        // Add backing board cost
        if (backing) {
            price += 0.25; // Cost of chipboard backing
        }
        
        // Add padding compound cost
        price += 0.50; // Base cost for padding
        if (sheets > 50) {
            // More padding compound needed for thicker pads
            price += Math.ceil((sheets - 50) / 50) * 0.25;
        }
        
        // Apply minimum price
        return Math.max(price, 1.50);
    }
    
    // Calculate finishing costs
    function calculateFinishingCost(quantity) {
        let finishingCost = 0;
        
        // Get selected finishing options
        const selectedOptions = Array.from(finishingOptions)
            .filter(option => option.checked)
            .map(option => option.value);
        
        // Calculate cost for each selected option
        selectedOptions.forEach(optionName => {
            // This would need to fetch finishing option data from the server
            // For now, use some default values
            switch(optionName) {
                case 'Cutting':
                    finishingCost += 1.00 + (quantity * 0.01);
                    break;
                case 'Folding':
                    finishingCost += 0.75 + (quantity * 0.02);
                    break;
                case 'Drilling':
                    finishingCost += 1.50 + (quantity * 0.01);
                    break;
                case 'Stapling':
                    finishingCost += 0.50 + (quantity * 0.02);
                    break;
                case 'Laminating':
                    finishingCost += 0.75 + (quantity * 0.20);
                    break;
                default:
                    // Unknown finishing option
                    finishingCost += 1.00;
            }
        });
        
        return finishingCost;
    }
    
    // Add all event listeners
    function addEventListeners() {
        console.log('Setting up event listeners for calculator...');
        
        // Setup paper size change listeners
        setupPaperSizeChangeListeners();
        
        // Add change listeners to form elements
        if (quantityInput) {
            console.log('Adding listener to quantity input');
            quantityInput.addEventListener('change', calculatePrice);
            quantityInput.addEventListener('input', calculatePrice);
        }
        
        if (paperSizeSelect) {
            console.log('Adding listener to paper size select');
            paperSizeSelect.addEventListener('change', function() {
                // Update paper types based on selected size
                filterPaperTypesBySize(paperSizeSelect.value, paperTypeSelect);
                calculatePrice();
            });
        }
        
        if (paperTypeSelect) {
            console.log('Adding listener to paper type select');
            paperTypeSelect.addEventListener('change', function() {
                // Update weights and colors when paper type changes
                if (paperWeightSelect) updatePaperWeightOptions(this.value, paperWeightSelect);
                if (paperColorSelect) updatePaperColorOptions(this.value, paperColorSelect);
                calculatePrice();
            });
        }
        
        if (paperWeightSelect) {
            console.log('Adding listener to paper weight select');
            paperWeightSelect.addEventListener('change', calculatePrice);
        }
        
        if (paperColorSelect) {
            console.log('Adding listener to paper color select');
            paperColorSelect.addEventListener('change', calculatePrice);
        }
        
        if (nUpSelect) {
            console.log('Adding listener to n-up select');
            nUpSelect.addEventListener('change', calculatePrice);
        }
        
        // Add listeners to print type radio buttons
        const printTypeRadios = document.querySelectorAll('input[name="print_type"]');
        printTypeRadios.forEach(radio => {
            console.log('Adding listener to print type radio:', radio.value);
            radio.addEventListener('change', calculatePrice);
        });
        
        // Add listeners to sides radio buttons
        const sidesRadios = document.querySelectorAll('input[name="sides"]');
        sidesRadios.forEach(radio => {
            console.log('Adding listener to sides radio:', radio.value);
            radio.addEventListener('change', calculatePrice);
        });
        
        // Add listeners to finishing option checkboxes
        if (finishingOptions) {
            finishingOptions.forEach(option => {
                console.log('Adding listener to finishing option:', option.value);
                option.addEventListener('change', calculatePrice);
            });
        }
        
        // Add listener to calculate button if it exists
        const calculateButton = document.getElementById('calculate_price');
        if (calculateButton) {
            console.log('Adding listener to calculate button');
            calculateButton.addEventListener('click', function(e) {
                e.preventDefault();
                calculatePrice();
            });
        }
        
        // Add listeners to notepad-specific fields
        if (sheetsInput) sheetsInput.addEventListener('change', calculatePrice);
        if (backingCheckbox) backingCheckbox.addEventListener('change', calculatePrice);
        if (partsInput) partsInput.addEventListener('change', calculatePrice);
        
        // Add listeners to booklet-specific fields
        if (pagesInput) pagesInput.addEventListener('change', calculatePrice);
        if (selfCoverCheckbox) selfCoverCheckbox.addEventListener('change', calculatePrice);
        if (bindingSelect) bindingSelect.addEventListener('change', calculatePrice);
        if (coverTypeSelect) coverTypeSelect.addEventListener('change', calculatePrice);
        if (coverWeightSelect) coverWeightSelect.addEventListener('change', calculatePrice);
        
        console.log('All event listeners set up successfully');
    }
    
    // Initialize event listeners after a short delay to ensure DOM is fully loaded
    setTimeout(function() {
        console.log("Setting up calculator with delay...");
        
        // Make sure to fetch data right away
        fetchPaperOptionData();
        fetchPrintPricingData();
        
        // Setup event listeners
        addEventListeners();
        
        // Initialize global var for finishing options
        window.selectedFinishingOptions = [];
        
        // Force an initial calculation
        setTimeout(function() {
            console.log("Forcing initial price calculation");
            calculatePrice();
        }, 1000);
        
        console.log("Quote calculator initialization complete");
    }, 500);
});