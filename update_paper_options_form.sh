#!/bin/bash

# Update the create.html form to include roll paper specific fields
cat > roll_paper_fields_create.html << 'ROLLFIELDS'
            <div class="roll-specific-fields mb-3" style="display: none;">
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Roll Paper Specific Details</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1">
                                <label class="form-check-label" for="is_roll">
                                    This is roll media
                                </label>
                            </div>
                            <div class="form-text">Check this if this paper comes on a roll</div>
                        </div>
                        <div class="mb-3">
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>
                            <input type="number" name="roll_length" id="roll_length" class="form-control" 
                                   step="0.1" min="0" placeholder="e.g., 150">
                            <div class="form-text">The total length of the roll in feet</div>
                        </div>
                    </div>
                </div>
            </div>
ROLLFIELDS

# Update the edit.html form to include roll paper specific fields
cat > roll_paper_fields_edit.html << 'ROLLFIELDS'
            <div class="roll-specific-fields mb-3" {% if paper_option.size != 'Roll' %}style="display: none;"{% endif %}>
                <div class="card">
                    <div class="card-header bg-light">
                        <h5 class="mb-0">Roll Paper Specific Details</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1" 
                                       {% if paper_option.is_roll %}checked{% endif %}>
                                <label class="form-check-label" for="is_roll">
                                    This is roll media
                                </label>
                            </div>
                            <div class="form-text">Check this if this paper comes on a roll</div>
                        </div>
                        <div class="mb-3">
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>
                            <input type="number" name="roll_length" id="roll_length" class="form-control" 
                                   step="0.1" min="0" value="{{ paper_option.roll_length or '' }}" placeholder="e.g., 150">
                            <div class="form-text">The total length of the roll in feet</div>
                        </div>
                    </div>
                </div>
            </div>
ROLLFIELDS

# Insert the fields into create.html
sed -i '/pricing_method/a\
\
            <!-- Roll Paper Specific Fields -->\
            <div class="roll-specific-fields mb-3" style="display: none;">\
                <div class="card">\
                    <div class="card-header bg-light">\
                        <h5 class="mb-0">Roll Paper Specific Details</h5>\
                    </div>\
                    <div class="card-body">\
                        <div class="mb-3">\
                            <div class="form-check">\
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1">\
                                <label class="form-check-label" for="is_roll">\
                                    This is roll media\
                                </label>\
                            </div>\
                            <div class="form-text">Check this if this paper comes on a roll</div>\
                        </div>\
                        <div class="mb-3">\
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>\
                            <input type="number" name="roll_length" id="roll_length" class="form-control" \
                                   step="0.1" min="0" placeholder="e.g., 150">\
                            <div class="form-text">The total length of the roll in feet</div>\
                        </div>\
                    </div>\
                </div>\
            </div>' templates/paper_options/create.html

# Insert the fields into edit.html
sed -i '/pricing_method/a\
\
            <!-- Roll Paper Specific Fields -->\
            <div class="roll-specific-fields mb-3" {% if paper_option.size != "Roll" %}style="display: none;"{% endif %}>\
                <div class="card">\
                    <div class="card-header bg-light">\
                        <h5 class="mb-0">Roll Paper Specific Details</h5>\
                    </div>\
                    <div class="card-body">\
                        <div class="mb-3">\
                            <div class="form-check">\
                                <input class="form-check-input" type="checkbox" id="is_roll" name="is_roll" value="1" \
                                       {% if paper_option.is_roll %}checked{% endif %}>\
                                <label class="form-check-label" for="is_roll">\
                                    This is roll media\
                                </label>\
                            </div>\
                            <div class="form-text">Check this if this paper comes on a roll</div>\
                        </div>\
                        <div class="mb-3">\
                            <label for="roll_length" class="form-label">Roll Length (feet)</label>\
                            <input type="number" name="roll_length" id="roll_length" class="form-control" \
                                   step="0.1" min="0" value="{{ paper_option.roll_length or \'\' }}" placeholder="e.g., 150">\
                            <div class="form-text">The total length of the roll in feet</div>\
                        </div>\
                    </div>\
                </div>\
            </div>' templates/paper_options/edit.html

# Add JavaScript to show/hide roll fields based on size selection
cat > js_create.txt << 'JSCREATE'
document.addEventListener('DOMContentLoaded', function() {
    const pricingMethodSelect = document.getElementById('pricing_method');
    const perSheetPricing = document.querySelector('.per-sheet-pricing');
    const sqftPricing = document.querySelector('.sqft-pricing');
    const sizeSelect = document.getElementById('size');
    const rollFields = document.querySelector('.roll-specific-fields');
    
    // Function to update pricing fields visibility
    const updatePricingFields = function() {
        if (pricingMethodSelect.value === 'sqft') {
            perSheetPricing.style.display = 'none';
            sqftPricing.style.display = 'flex';
        } else {
            perSheetPricing.style.display = 'flex';
            sqftPricing.style.display = 'none';
        }
    };
    
    // Function to update roll fields visibility
    const updateRollFields = function() {
        if (sizeSelect.value === 'Roll') {
            rollFields.style.display = 'block';
            // For roll paper, default to sqft pricing
            pricingMethodSelect.value = 'sqft';
            updatePricingFields();
        } else {
            rollFields.style.display = 'none';
        }
    };
    
    // Set initial state
    updatePricingFields();
    updateRollFields();
    
    // Add event listeners
    pricingMethodSelect.addEventListener('change', updatePricingFields);
    sizeSelect.addEventListener('change', updateRollFields);
});
JSCREATE

# Add JavaScript to show/hide roll fields based on size selection
cat > js_edit.txt << 'JSEDIT'
document.addEventListener('DOMContentLoaded', function() {
    const pricingMethodSelect = document.getElementById('pricing_method');
    const perSheetPricing = document.querySelector('.per-sheet-pricing');
    const sqftPricing = document.querySelector('.sqft-pricing');
    const sizeSelect = document.getElementById('size');
    const rollFields = document.querySelector('.roll-specific-fields');
    
    // Function to update pricing fields visibility
    const updatePricingFields = function() {
        if (pricingMethodSelect.value === 'sqft') {
            perSheetPricing.style.display = 'none';
            sqftPricing.style.display = 'flex';
        } else {
            perSheetPricing.style.display = 'flex';
            sqftPricing.style.display = 'none';
        }
    };
    
    // Function to update roll fields visibility
    const updateRollFields = function() {
        if (sizeSelect.value === 'Roll') {
            rollFields.style.display = 'block';
            // For roll paper, default to sqft pricing
            pricingMethodSelect.value = 'sqft';
            updatePricingFields();
        } else {
            rollFields.style.display = 'none';
        }
    };
    
    // Set initial state
    updatePricingFields();
    
    // Add event listeners
    pricingMethodSelect.addEventListener('change', updatePricingFields);
    sizeSelect.addEventListener('change', updateRollFields);
});
JSEDIT

# Replace the JavaScript in create.html
sed -i '/DOMContentLoaded/,/}/c\
<script>\
document.addEventListener(\"DOMContentLoaded\", function() {\
    const pricingMethodSelect = document.getElementById(\"pricing_method\");\
    const perSheetPricing = document.querySelector(\".per-sheet-pricing\");\
    const sqftPricing = document.querySelector(\".sqft-pricing\");\
    const sizeSelect = document.getElementById(\"size\");\
    const rollFields = document.querySelector(\".roll-specific-fields\");\
    \
    // Function to update pricing fields visibility\
    const updatePricingFields = function() {\
        if (pricingMethodSelect.value === \"sqft\") {\
            perSheetPricing.style.display = \"none\";\
            sqftPricing.style.display = \"flex\";\
        } else {\
            perSheetPricing.style.display = \"flex\";\
            sqftPricing.style.display = \"none\";\
        }\
    };\
    \
    // Function to update roll fields visibility\
    const updateRollFields = function() {\
        if (sizeSelect.value === \"Roll\") {\
            rollFields.style.display = \"block\";\
            // For roll paper, default to sqft pricing\
            pricingMethodSelect.value = \"sqft\";\
            updatePricingFields();\
        } else {\
            rollFields.style.display = \"none\";\
        }\
    };\
    \
    // Set initial state\
    updatePricingFields();\
    updateRollFields();\
    \
    // Add event listeners\
    pricingMethodSelect.addEventListener(\"change\", updatePricingFields);\
    sizeSelect.addEventListener(\"change\", updateRollFields);\
});\
</script>' templates/paper_options/create.html

# Replace the JavaScript in edit.html
sed -i '/DOMContentLoaded/,/}/c\
<script>\
document.addEventListener(\"DOMContentLoaded\", function() {\
    const pricingMethodSelect = document.getElementById(\"pricing_method\");\
    const perSheetPricing = document.querySelector(\".per-sheet-pricing\");\
    const sqftPricing = document.querySelector(\".sqft-pricing\");\
    const sizeSelect = document.getElementById(\"size\");\
    const rollFields = document.querySelector(\".roll-specific-fields\");\
    \
    // Function to update pricing fields visibility\
    const updatePricingFields = function() {\
        if (pricingMethodSelect.value === \"sqft\") {\
            perSheetPricing.style.display = \"none\";\
            sqftPricing.style.display = \"flex\";\
        } else {\
            perSheetPricing.style.display = \"flex\";\
            sqftPricing.style.display = \"none\";\
        }\
    };\
    \
    // Function to update roll fields visibility\
    const updateRollFields = function() {\
        if (sizeSelect.value === \"Roll\") {\
            rollFields.style.display = \"block\";\
            // For roll paper, default to sqft pricing\
            pricingMethodSelect.value = \"sqft\";\
            updatePricingFields();\
        } else {\
            rollFields.style.display = \"none\";\
        }\
    };\
    \
    // Set initial state\
    updatePricingFields();\
    \
    // Add event listeners\
    pricingMethodSelect.addEventListener(\"change\", updatePricingFields);\
    sizeSelect.addEventListener(\"change\", updateRollFields);\
});\
</script>' templates/paper_options/edit.html

