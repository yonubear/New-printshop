// Paper filter functionality for quote/order forms

/**
 * Paper filter and dynamic selection based on size, weight, and type
 */
document.addEventListener('DOMContentLoaded', function() {
    // Elements in the form
    const sizeSelect = document.getElementById('size');
    const paperWeightSelect = document.getElementById('paper_weight');
    const paperTypeSelect = document.getElementById('paper_type');
    
    if (!sizeSelect || !paperWeightSelect || !paperTypeSelect) {
        // Not on a page with these elements
        return;
    }
    
    // Initialize paper filtering
    initPaperFiltering();
    
    // Add event listeners for the size and weight dropdowns
    sizeSelect.addEventListener('change', updatePaperOptions);
    paperWeightSelect.addEventListener('change', updatePaperOptions);
    
    /**
     * Initialize paper filtering
     */
    function initPaperFiltering() {
        // Initial load of paper options (unfiltered)
        updatePaperOptions();
    }
    
    /**
     * Update the paper options dropdown based on selected size and weight
     */
    function updatePaperOptions() {
        const selectedSize = sizeSelect.value;
        const selectedWeight = paperWeightSelect.value;
        
        // Build the API URL with query parameters
        let apiUrl = '/api/paper-options';
        const params = [];
        
        if (selectedSize && selectedSize !== 'Custom') {
            params.push(`size=${encodeURIComponent(selectedSize)}`);
        }
        
        if (selectedWeight) {
            params.push(`weight=${encodeURIComponent(selectedWeight)}`);
        }
        
        if (params.length > 0) {
            apiUrl += '?' + params.join('&');
        }
        
        // Save the current selection
        const currentSelection = paperTypeSelect.value;
        
        // Fetch filtered paper options from the API
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                // Clear the dropdown
                paperTypeSelect.innerHTML = '<option value="">-- Select Paper Type --</option>';
                
                // Add options from the filtered data
                data.forEach(paper => {
                    const option = document.createElement('option');
                    option.value = paper.id;
                    option.textContent = `${paper.name} (${paper.size}, ${paper.weight})`;
                    paperTypeSelect.appendChild(option);
                });
                
                // Try to restore the previous selection if it exists in the new options
                if (currentSelection) {
                    paperTypeSelect.value = currentSelection;
                }
                
                // If no matching option was found and the dropdown has options besides the default
                if (paperTypeSelect.value === '' && paperTypeSelect.options.length > 1) {
                    // Select the first non-default option
                    paperTypeSelect.selectedIndex = 1;
                }
            })
            .catch(error => {
                console.error('Error fetching paper options:', error);
            });
    }
});