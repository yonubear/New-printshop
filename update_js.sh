#!/bin/bash

# Replace the JavaScript in create.html
sed -i '/pricingMethodSelect.addEventListener/i\
    const sizeSelect = document.getElementById("size");\
    const rollFields = document.querySelector(".roll-specific-fields");\
    \
    // Function to update roll fields visibility\
    const updateRollFields = function() {\
        if (sizeSelect.value === "Roll") {\
            rollFields.style.display = "block";\
            // For roll paper, default to sqft pricing\
            pricingMethodSelect.value = "sqft";\
            updatePricingFields();\
        } else {\
            rollFields.style.display = "none";\
        }\
    };\
    \
    // Init roll fields\
    updateRollFields();\
    \
    // Add roll fields event listener\
    sizeSelect.addEventListener("change", updateRollFields);' templates/paper_options/create.html

# Replace the JavaScript in edit.html
sed -i '/pricingMethodSelect.addEventListener/i\
    const sizeSelect = document.getElementById("size");\
    const rollFields = document.querySelector(".roll-specific-fields");\
    \
    // Function to update roll fields visibility\
    const updateRollFields = function() {\
        if (sizeSelect.value === "Roll") {\
            rollFields.style.display = "block";\
            // For roll paper, default to sqft pricing\
            pricingMethodSelect.value = "sqft";\
            updatePricingFields();\
        } else {\
            rollFields.style.display = "none";\
        }\
    };\
    \
    // Add roll fields event listener\
    sizeSelect.addEventListener("change", updateRollFields);' templates/paper_options/edit.html
