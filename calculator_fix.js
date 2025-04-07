// Simple price calculator for quote items
document.addEventListener("DOMContentLoaded", function() {
    console.log("Price calculator loaded");
    
    // Get the calculate price button
    const calculatePriceBtn = document.getElementById("calculate_price_btn");
    if (calculatePriceBtn) {
        console.log("Calculate price button found");
        
        calculatePriceBtn.addEventListener("click", function() {
            console.log("Calculate price button clicked");
            
            // Get the quantity
            const quantity = parseInt(document.getElementById("quantity").value) || 100;
            console.log("Quantity:", quantity);
            
            // Simple calculation based on quantity with discounts
            let basePrice = 0.15; // Base price per item
            
            // Apply quantity discounts
            if (quantity >= 500) basePrice = 0.10;
            if (quantity >= 1000) basePrice = 0.08;
            
            const unitPrice = basePrice;
            const totalPrice = unitPrice * quantity;
            
            // Update all price fields
            updateAllPriceFields(unitPrice, totalPrice);
            
            // Show confirmation
            alert("Price calculated! Unit price: $" + unitPrice.toFixed(2) + ", Total: $" + totalPrice.toFixed(2));
        });
    }
    
    // Default price button
    const defaultPriceBtn = document.getElementById("use_default_price");
    if (defaultPriceBtn) {
        console.log("Default price button found");
        
        defaultPriceBtn.addEventListener("click", function() {
            console.log("Default price button clicked");
            
            // Set default price ($1.00)
            const defaultPrice = 1.00;
            const quantity = parseInt(document.getElementById("quantity").value) || 100;
            const totalPrice = defaultPrice * quantity;
            
            // Update all price fields
            updateAllPriceFields(defaultPrice, totalPrice);
            
            // Show confirmation
            alert("Default price of $1.00 has been applied. Total: $" + totalPrice.toFixed(2));
        });
    }
    
    // Function to update all price-related fields
    function updateAllPriceFields(unitPrice, totalPrice) {
        console.log("Updating price fields - unit:", unitPrice, "total:", totalPrice);
        
        // Update unit price input (form field)
        const unitPriceInput = document.getElementById("unit_price");
        if (unitPriceInput) {
            unitPriceInput.value = unitPrice.toFixed(2);
        }
        
        // Update display elements
        const unitPriceDisplay = document.getElementById("unit_price_display");
        const totalPriceDisplay = document.getElementById("total_price_display");
        
        if (unitPriceDisplay) unitPriceDisplay.textContent = unitPrice.toFixed(2);
        if (totalPriceDisplay) totalPriceDisplay.textContent = totalPrice.toFixed(2);
        
        // Update calculated price (if exists)
        const calculatedPrice = document.getElementById("calculated_price");
        if (calculatedPrice) {
            calculatedPrice.value = unitPrice.toFixed(2);
        }
        
        // Update hidden field (if exists)
        const calculatedPriceHidden = document.getElementById("calculated_price_hidden");
        if (calculatedPriceHidden) {
            calculatedPriceHidden.value = unitPrice.toFixed(2);
        }
        
        console.log("Price fields updated successfully");
    }
});
