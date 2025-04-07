/**
 * Interactive Print Preview
 * 
 * This script provides an interactive print job preview with real-time
 * material cost estimation. It visualizes different paper sizes, printing options,
 * and calculates pricing based on current material costs.
 */

$(document).ready(function() {
    // Check if we're on the preview page
    if (!document.getElementById('paper_preview_container')) {
        return; // Not on the print preview page
    }
    
    // Initialize elements
    const paperSizeSelect = document.getElementById('paper_size');
    const paperCategorySelect = document.getElementById('paper_category');
    const paperWeightSelect = document.getElementById('paper_weight');
    const paperOptionSelect = document.getElementById('paper_option');
    const colorTypeSelect = document.getElementById('color_type');
    const sidesSelect = document.getElementById('sides');
    const quantityInput = document.getElementById('quantity');
    const customSizeInputs = document.querySelector('.custom-size-inputs');
    const customWidthInput = document.getElementById('custom_width');
    const customHeightInput = document.getElementById('custom_height');
    const showBackSideToggle = document.getElementById('showBackSide');
    const updatePreviewBtn = document.getElementById('update_preview_btn');
    const finishingOptionsContainer = document.getElementById('finishing_options_container');
    const previewLoading = document.getElementById('previewLoading');
    
    // Custom size handling
    paperSizeSelect.addEventListener('change', function() {
        if (this.value === 'Custom') {
            customSizeInputs.style.display = 'block';
        } else {
            customSizeInputs.style.display = 'none';
        }
        updateFormState();
    });
    
    // Update paper options when size, category, or weight changes
    [paperSizeSelect, paperCategorySelect, paperWeightSelect].forEach(select => {
        select.addEventListener('change', function() {
            updatePaperOptions();
            updateFormState();
        });
    });
    
    // Toggle back side visibility
    showBackSideToggle.addEventListener('change', function() {
        const backSide = document.querySelector('.back-side');
        if (backSide) {
            backSide.style.display = this.checked ? 'block' : 'none';
        }
    });
    
    // Update button state
    function updateFormState() {
        const isValid = paperOptionSelect.value && colorTypeSelect.value;
        updatePreviewBtn.disabled = !isValid;
        
        if (paperOptionSelect.value) {
            loadFinishingOptions();
        }
    }
    
    // Handle option changes
    [paperOptionSelect, colorTypeSelect, sidesSelect, quantityInput].forEach(element => {
        element.addEventListener('change', updateFormState);
    });
    
    // Update preview button click handler
    updatePreviewBtn.addEventListener('click', function() {
        generatePreview();
        calculateCost();
    });
    
    // Load paper options based on selected criteria
    function updatePaperOptions() {
        const size = paperSizeSelect.value;
        const category = paperCategorySelect.value;
        const weight = paperWeightSelect.value;
        
        if (!size || !category || !weight) {
            paperOptionSelect.innerHTML = '<option value="">Select paper size, type, and weight first</option>';
            paperOptionSelect.disabled = true;
            return;
        }
        
        // Fetch paper options that match the criteria
        fetch(`/api/paper-options?size=${encodeURIComponent(size)}&weight=${encodeURIComponent(weight)}`)
            .then(response => response.json())
            .then(data => {
                paperOptionSelect.innerHTML = '<option value="">Select paper</option>';
                
                // Filter by category (client-side since we already have the data)
                const filteredOptions = data.filter(paper => paper.category === category);
                
                if (filteredOptions.length === 0) {
                    paperOptionSelect.innerHTML = '<option value="">No matching paper options found</option>';
                    paperOptionSelect.disabled = true;
                } else {
                    filteredOptions.forEach(paper => {
                        const option = document.createElement('option');
                        option.value = paper.id;
                        option.textContent = `${paper.name} - $${paper.price_per_sheet.toFixed(2)}/sheet`;
                        option.setAttribute('data-cost', paper.cost_per_sheet || 0);
                        paperOptionSelect.appendChild(option);
                    });
                    paperOptionSelect.disabled = false;
                }
                
                updateFormState();
            })
            .catch(error => {
                console.error('Error fetching paper options:', error);
                paperOptionSelect.innerHTML = '<option value="">Error loading options</option>';
                paperOptionSelect.disabled = true;
            });
    }
    
    // Load finishing options
    function loadFinishingOptions() {
        fetch('/api/finishing-options')
            .then(response => response.json())
            .then(data => {
                // Group options by category
                const categories = {};
                data.forEach(option => {
                    if (!categories[option.category]) {
                        categories[option.category] = [];
                    }
                    categories[option.category].push(option);
                });
                
                // Build the UI
                let html = '';
                for (const category in categories) {
                    html += `<div class="finishing-category mb-3">
                                <h6>${category}</h6>
                                <div class="finishing-options">`;
                    
                    categories[category].forEach(option => {
                        html += `<div class="finishing-option">
                                    <div class="form-check">
                                        <input class="form-check-input finishing-checkbox" type="checkbox" 
                                               id="finishing_${option.id}" value="${option.id}" 
                                               data-name="${option.name}" 
                                               data-base-price="${option.base_price}"
                                               data-price-per-piece="${option.price_per_piece}"
                                               data-min-price="${option.minimum_price}">
                                        <label class="form-check-label" for="finishing_${option.id}">
                                            ${option.name}
                                            <span class="text-muted d-block small">${option.description || ''}</span>
                                            <span class="text-primary small">Starting at $${option.base_price.toFixed(2)}</span>
                                        </label>
                                    </div>
                                </div>`;
                    });
                    
                    html += `</div></div>`;
                }
                
                finishingOptionsContainer.innerHTML = html;
                
                // Add event listeners to the checkboxes
                document.querySelectorAll('.finishing-checkbox').forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        if (updatePreviewBtn.disabled === false) {
                            // Auto-update when changing options if preview is already active
                            generatePreview();
                            calculateCost();
                        }
                    });
                });
            })
            .catch(error => {
                console.error('Error loading finishing options:', error);
                finishingOptionsContainer.innerHTML = '<div class="alert alert-danger">Error loading finishing options</div>';
            });
    }
    
    // Generate the paper preview
    function generatePreview() {
        const previewContainer = document.getElementById('paper_preview_container');
        const paperSize = paperSizeSelect.value;
        const colorType = colorTypeSelect.value;
        const sides = sidesSelect.value;
        
        previewLoading.style.display = 'flex';
        
        // Clear any existing preview
        previewContainer.innerHTML = '';
        
        // Create the base paper element with appropriate size class
        let sizeClass = 'custom';
        if (paperSize === 'Letter') sizeClass = 'letter';
        else if (paperSize === 'Legal') sizeClass = 'legal';
        else if (paperSize === 'Tabloid') sizeClass = 'tabloid';
        
        let paperElement = document.createElement('div');
        paperElement.className = `paper-preview ${sizeClass}`;
        
        // Set dimensions for custom size
        if (paperSize === 'Custom') {
            const width = parseFloat(customWidthInput.value);
            const height = parseFloat(customHeightInput.value);
            if (!isNaN(width) && !isNaN(height)) {
                // Convert inches to pixels with a scale factor
                paperElement.style.width = (width * 25) + 'px';
                paperElement.style.height = (height * 25) + 'px';
            }
        }
        
        // Create front side content
        const frontContent = document.createElement('div');
        frontContent.className = `paper-content ${colorType === 'Full Color' ? 'color' : 'bw'}`;
        frontContent.innerHTML = `<div class="placeholder-content">
            <strong>${paperSize}</strong><br>
            ${colorType}<br>
            Front Side
        </div>`;
        paperElement.appendChild(frontContent);
        
        // Create back side content if double-sided
        if (sides === 'Double-sided') {
            const backContent = document.createElement('div');
            backContent.className = `paper-content back-side ${colorType === 'Full Color' ? 'color' : 'bw'}`;
            backContent.innerHTML = `<div class="placeholder-content">
                <strong>${paperSize}</strong><br>
                ${colorType}<br>
                Back Side
            </div>`;
            paperElement.appendChild(backContent);
        }
        
        // Add the finished paper to the preview container
        previewContainer.appendChild(paperElement);
        
        // Show the back side if the toggle is checked
        if (showBackSideToggle.checked) {
            const backSide = document.querySelector('.back-side');
            if (backSide) {
                backSide.style.display = 'block';
            }
        }
        
        // Show materials
        document.getElementById('materials_card').style.display = 'block';
        const materialsList = document.getElementById('materials_list');
        materialsList.innerHTML = '';
        
        // Add paper as a material
        const selectedPaperOption = paperOptionSelect.options[paperOptionSelect.selectedIndex];
        const paperName = selectedPaperOption.textContent.split(' - ')[0];
        
        const paperLi = document.createElement('li');
        paperLi.className = 'list-group-item d-flex justify-content-between align-items-center';
        paperLi.innerHTML = `
            <div>
                <i class="bi bi-file-earmark me-2"></i>
                <strong>${paperName}</strong>
                <span class="badge bg-light text-dark ms-2">${paperSize}</span>
            </div>
            <span class="badge bg-primary rounded-pill">1 sheet</span>
        `;
        materialsList.appendChild(paperLi);
        
        // Add ink as a material
        const inkLi = document.createElement('li');
        inkLi.className = 'list-group-item d-flex justify-content-between align-items-center';
        inkLi.innerHTML = `
            <div>
                <i class="bi bi-droplet-half me-2"></i>
                <strong>${colorType} Ink</strong>
                <span class="badge bg-light text-dark ms-2">${sides}</span>
            </div>
            <span class="badge bg-primary rounded-pill">${sides === 'Double-sided' ? '2' : '1'} sides</span>
        `;
        materialsList.appendChild(inkLi);
        
        // Add finishing options as materials
        document.querySelectorAll('.finishing-checkbox:checked').forEach(checkbox => {
            const finishingLi = document.createElement('li');
            finishingLi.className = 'list-group-item d-flex justify-content-between align-items-center';
            finishingLi.innerHTML = `
                <div>
                    <i class="bi bi-tools me-2"></i>
                    <strong>${checkbox.getAttribute('data-name')}</strong>
                </div>
                <span class="badge bg-primary rounded-pill">1 unit</span>
            `;
            materialsList.appendChild(finishingLi);
        });
        
        previewLoading.style.display = 'none';
    }
    
    // Calculate cost
    function calculateCost() {
        const paperOptionId = paperOptionSelect.value;
        const colorType = colorTypeSelect.value;
        const sides = sidesSelect.value;
        const quantity = parseInt(quantityInput.value);
        
        // Get selected finishing options
        const selectedFinishingOptions = [];
        document.querySelectorAll('.finishing-checkbox:checked').forEach(checkbox => {
            selectedFinishingOptions.push(parseInt(checkbox.value));
        });
        
        // Show loading state
        previewLoading.style.display = 'flex';
        document.getElementById('cost_placeholder').style.display = 'none';
        document.getElementById('cost_breakdown').style.display = 'none';
        
        // Prepare data for API call
        const costData = {
            paper_id: paperOptionId,
            color_type: colorType,
            sides: sides,
            quantity: quantity,
            finishing_ids: selectedFinishingOptions
        };
        
        // Call the API
        fetch('/api/preview/cost-estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify(costData)
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading, show results
            previewLoading.style.display = 'none';
            document.getElementById('cost_breakdown').style.display = 'block';
            
            // Update price information
            document.getElementById('total_price').textContent = data.prices.total_price.toFixed(2);
            document.getElementById('unit_price').textContent = data.prices.unit_with_finishing.toFixed(2);
            document.getElementById('qty_display').textContent = data.quantity;
            
            // Update cost breakdown
            document.getElementById('paper_cost').textContent = data.paper.price_per_sheet.toFixed(2);
            
            const printingCost = data.printing.price_per_side * data.printing.num_sides;
            document.getElementById('printing_cost').textContent = printingCost.toFixed(2);
            
            // Update finishing costs if any
            if (data.finishing.total_cost > 0) {
                document.getElementById('finishing_cost_item').style.display = 'block';
                document.getElementById('finishing_cost').textContent = data.finishing.total_cost.toFixed(2);
                
                // Show finishing breakdown
                document.getElementById('finishing_breakdown').style.display = 'block';
                const finishingDetails = document.getElementById('finishing_details');
                finishingDetails.innerHTML = '';
                
                data.finishing.breakdown.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'finishing-detail';
                    div.innerHTML = `
                        <span class="small">${item.name}</span>
                        <span class="small text-end">$${item.price.toFixed(2)}</span>
                    `;
                    finishingDetails.appendChild(div);
                });
            } else {
                document.getElementById('finishing_cost_item').style.display = 'none';
                document.getElementById('finishing_breakdown').style.display = 'none';
            }
            
            // Update profit information
            document.getElementById('total_cost').textContent = data.costs.total_cost.toFixed(2);
            document.getElementById('estimated_profit').textContent = data.costs.estimated_profit.toFixed(2);
            document.getElementById('profit_margin').textContent = data.costs.profit_margin.toFixed(1);
        })
        .catch(error => {
            console.error('Error calculating cost:', error);
            previewLoading.style.display = 'none';
            document.getElementById('cost_placeholder').style.display = 'block';
            document.getElementById('cost_placeholder').innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error calculating cost. Please try again.
                </div>
            `;
        });
    }
});