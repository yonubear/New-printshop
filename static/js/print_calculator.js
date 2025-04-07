/**
 * Print Calculator - Calculate print job prices based on configured options
 * 
 * This script provides functions to calculate printing prices based on:
 * 1. Paper size
 * 2. Color vs B&W
 * 3. Number of sides
 * 4. Paper cost
 * 5. Booklet pricing (with page count, binding options, and cover options)
 */

$(document).ready(function() {
    // Check if we're on a page with the calculator
    if ($('#calculate-price').length === 0) {
        console.log('Print calculator not needed on this page');
        return; // Exit early if calculator button isn't on this page
    }

    console.log('Initializing print calculator...');
    
    // Elements in the quote form
    const productTypeSelect = $('#product_type');
    const colorTypeSelect = $('#color_type');
    const sidesSelect = $('#sides');
    const paperTypeSelect = $('#paper_type');
    const nUpSelect = $('#n_up');
    const quantityInput = $('#quantity');
    const unitPriceInput = $('#unit_price');
    const totalPriceInput = $('#total_price');
    
    // Booklet elements
    const pageCountInput = $('#page_count');
    const coverPaperSelect = $('#cover_paper_type');
    const bindingTypeSelect = $('#binding_type');
    const coverPrintingSelect = $('#cover_printing');
    const selfCoverCheckbox = $('#self_cover');
    
    // Elements for auto-calculation
    const calcBtn = $('#calculate-price');
    
    // Events
    calcBtn.on('click', function(e) {
        console.log('Calculate button clicked');
        e.preventDefault();
        calculatePrintPrice();
    });
    
    // When these elements change, automatically update the calculation button state
    [colorTypeSelect, sidesSelect, paperTypeSelect, quantityInput, nUpSelect,
     productTypeSelect, pageCountInput, coverPaperSelect, bindingTypeSelect, coverPrintingSelect, selfCoverCheckbox
    ].forEach(element => {
        if (element.length) {
            element.on('change', function() {
                // Enable the calculation button if all required fields are filled
                calcBtn.prop('disabled', !canCalculate());
            });
        }
    });
    
    // Function to check if all required fields for calculation are filled
    function canCalculate() {
        const productType = productTypeSelect.val() || 'print_job';
        
        // Basic requirements for all product types
        const basicRequirements = 
            colorTypeSelect.val() && 
            paperTypeSelect.val() && 
            parseInt(quantityInput.val()) > 0;
            
        if (productType === 'booklet') {
            // For booklets, we need page count and binding type
            return basicRequirements && 
                   parseInt(pageCountInput.val()) >= 4 &&
                   bindingTypeSelect.val();
        } else {
            // For regular print jobs, we need sides
            return basicRequirements && sidesSelect.val();
        }
    }
    
    // Function to fetch price data and calculate
    function calculatePrintPrice() {
        // Get selected values
        const productType = productTypeSelect.val() || 'print_job';
        const colorType = colorTypeSelect.val();
        const sides = sidesSelect.val();
        const paperType = paperTypeSelect.val();
        const quantity = parseInt(quantityInput.val());
        
        // Determine if this is a booklet or regular print job
        if (productType === 'booklet') {
            calculateBookletPrice();
        } else {
            calculateRegularPrintPrice();
        }
    }
    
    // Calculate price for regular print job
    function calculateRegularPrintPrice() {
        // Get selected values
        const colorType = colorTypeSelect.val();
        const sides = sidesSelect.val();
        const paperType = paperTypeSelect.val();
        const quantity = parseInt(quantityInput.val());
        const nUp = parseInt(nUpSelect.val() || '1'); // Default to 1 if not selected
        
        // Determine if this is single or double sided
        const numSides = sides === 'Double-sided' ? 2 : 1;
        
        // Get paper size from paper type (we need to fetch this info)
        $.ajax({
            url: '/api/paper-options',
            method: 'GET',
            data: {
                paper_id: paperType  // Add the paper ID as a parameter
            },
            success: function(paperOptions) {
                // Find the selected paper
                const selectedPaper = paperOptions.find(p => p.id.toString() === paperType.toString());
                
                if (!selectedPaper) {
                    alert('Could not find paper option information. Please try again.');
                    console.error('Paper not found. ID:', paperType, 'Available papers:', paperOptions);
                    return;
                }
                
                // Now get the print pricing for this size and color type
                $.ajax({
                    url: '/api/print-pricing',
                    method: 'GET',
                    data: {
                        paper_size: selectedPaper.size,
                        color_type: colorType
                    },
                    success: function(pricingData) {
                        if (!pricingData || !pricingData.price_per_side) {
                            alert('No pricing configuration found for this combination. Please set up print pricing first.');
                            return;
                        }
                        
                        // Calculate the base price factoring in n-up and the pricing method (per side or per sqft)
                        let paperCost = 0;
                        let effectivePrintCost = 0;
                        
                        // Determine if we're using square footage pricing or per-sheet/per-side pricing
                        const useSquareFootagePricing = (selectedPaper.pricing_method === 'sqft' || pricingData.pricing_method === 'sqft');
                        
                        if (useSquareFootagePricing && selectedPaper.width && selectedPaper.height) {
                            // Calculate square footage of the sheet
                            const sqft = (selectedPaper.width * selectedPaper.height) / 144; // Convert to square feet (12x12=144 sq inches)
                            
                            // Calculate paper cost based on square footage
                            paperCost = selectedPaper.price_per_sqft * sqft;
                            
                            // Calculate print cost based on square footage
                            effectivePrintCost = pricingData.price_per_sqft * sqft * numSides;
                        } else {
                            // Use traditional per-sheet/per-side pricing
                            paperCost = selectedPaper.price_per_sheet;
                            effectivePrintCost = pricingData.price_per_side * numSides;
                        }
                        
                        // Apply n-up discount (reduce print cost based on how many can fit on a sheet)
                        if (nUp > 1) {
                            // Divide the printing cost by the n-up value (with minimum 25% of original cost)
                            // This ensures we're still covering costs while giving appropriate discount
                            effectivePrintCost = Math.max(effectivePrintCost / nUp, effectivePrintCost * 0.25);
                        }
                        
                        const unitPrice = paperCost + effectivePrintCost;
                        const totalPrice = unitPrice * quantity;
                        
                        // Update the form fields
                        unitPriceInput.val(unitPrice.toFixed(2));
                        totalPriceInput.val(totalPrice.toFixed(2));
                        
                        // Optional: show a breakdown
                        const pricingMethod = useSquareFootagePricing ? 'Square Footage Pricing' : 'Per Sheet/Side Pricing';
                        const message = `Price Calculation (${pricingMethod}):\n` +
                                      `- Paper (${selectedPaper.name}): $${paperCost.toFixed(2)}\n` +
                                      `- Printing (${colorType}, ${sides}, ${nUp}-up): $${effectivePrintCost.toFixed(2)}\n` +
                                      `- Total Per Unit: $${unitPrice.toFixed(2)}\n` +
                                      `- Quantity: ${quantity}\n` +
                                      `- Total Price: $${totalPrice.toFixed(2)}`;
                        
                        console.log(message);
                    },
                    error: function() {
                        alert('Failed to fetch pricing data. Please try again.');
                    }
                });
            },
            error: function() {
                alert('Failed to fetch paper options. Please try again.');
            }
        });
    }
    
    // Calculate price for booklet
    function calculateBookletPrice() {
        // Get booklet specific values
        const pageCount = parseInt(pageCountInput.val()) || 4;
        const coverPaperId = coverPaperSelect.val();
        const insidePaperId = paperTypeSelect.val();
        const bindingType = bindingTypeSelect.val();
        const coverPrinting = coverPrintingSelect.val();
        const selfCover = selfCoverCheckbox.prop('checked');
        const quantity = parseInt(quantityInput.val());
        const colorType = colorTypeSelect.val();
        
        // Validate page count - must be multiple of 4
        if (pageCount % 4 !== 0) {
            alert('Booklet page count must be a multiple of 4.');
            return;
        }
        
        // Calculate number of sheets needed
        const insideSheets = pageCount / 4; // 4 pages per sheet (front and back)
        const coverSheets = selfCover ? 0 : 1; // Cover is one sheet, unless using self-cover
        
        // Fetch inside paper details
        $.ajax({
            url: '/api/paper-options',
            method: 'GET',
            data: { paper_id: insidePaperId },
            success: function(paperOptions) {
                const insidePaper = paperOptions.find(p => p.id.toString() === insidePaperId.toString());
                
                if (!insidePaper) {
                    alert('Could not find inside paper option information.');
                    return;
                }
                
                // Get cover paper (if different from inside)
                let coverPaper = insidePaper; // Default to inside paper
                let coverPaperPromise = Promise.resolve();
                
                if (!selfCover && coverPaperId) {
                    coverPaperPromise = new Promise((resolve, reject) => {
                        $.ajax({
                            url: '/api/paper-options',
                            method: 'GET',
                            data: { paper_id: coverPaperId },
                            success: function(paperOptions) {
                                const paper = paperOptions.find(p => p.id.toString() === coverPaperId.toString());
                                if (paper) {
                                    coverPaper = paper;
                                    resolve();
                                } else {
                                    // If not found, still continue with inside paper for cover
                                    resolve();
                                }
                            },
                            error: function() {
                                // On error, still continue with inside paper for cover
                                resolve();
                            }
                        });
                    });
                }
                
                // Get print pricing
                const printPricingPromise = new Promise((resolve, reject) => {
                    $.ajax({
                        url: '/api/print-pricing',
                        method: 'GET',
                        data: {
                            paper_size: insidePaper.size,
                            color_type: colorType
                        },
                        success: function(pricingData) {
                            if (!pricingData || !pricingData.price_per_side) {
                                alert('No pricing configuration found for this combination. Please set up print pricing first.');
                                reject();
                            } else {
                                resolve(pricingData);
                            }
                        },
                        error: function() {
                            alert('Failed to fetch pricing data. Please try again.');
                            reject();
                        }
                    });
                });
                
                // After getting all the paper and pricing data, calculate the total
                Promise.all([coverPaperPromise, printPricingPromise])
                    .then(([_, pricingData]) => {
                        // Determine if we're using square footage pricing or per-sheet/per-side pricing
                        const useInsideSqftPricing = (insidePaper.pricing_method === 'sqft');
                        const useCoverSqftPricing = (!selfCover && coverPaper.pricing_method === 'sqft');
                        const usePrintSqftPricing = (pricingData.pricing_method === 'sqft');
                        
                        // Calculate paper costs
                        let insidePaperCost = 0;
                        let coverPaperCost = 0;
                        
                        if (useInsideSqftPricing && insidePaper.width && insidePaper.height) {
                            // Calculate square footage of the sheet
                            const sqft = (insidePaper.width * insidePaper.height) / 144; // Convert to square feet
                            insidePaperCost = insidePaper.price_per_sqft * sqft * insideSheets;
                        } else {
                            insidePaperCost = insidePaper.price_per_sheet * insideSheets;
                        }
                        
                        if (!selfCover) {
                            if (useCoverSqftPricing && coverPaper.width && coverPaper.height) {
                                // Calculate square footage of the cover sheet
                                const sqft = (coverPaper.width * coverPaper.height) / 144;
                                coverPaperCost = coverPaper.price_per_sqft * sqft * coverSheets;
                            } else {
                                coverPaperCost = coverPaper.price_per_sheet * coverSheets;
                            }
                        }
                        
                        const totalPaperCost = insidePaperCost + coverPaperCost;
                        
                        // Calculate printing costs based on pricing method
                        let insidePrintingCost = 0;
                        
                        if (usePrintSqftPricing && insidePaper.width && insidePaper.height) {
                            // Calculate square footage of each sheet
                            const sqft = (insidePaper.width * insidePaper.height) / 144;
                            insidePrintingCost = pricingData.price_per_sqft * sqft * 2 * insideSheets; // Double-sided
                        } else {
                            insidePrintingCost = pricingData.price_per_side * 2 * insideSheets; // Double-sided
                        }
                        
                        // Calculate cover printing costs based on coverage (4/4, 4/0, etc.)
                        let coverPrintingCost = 0;
                        
                        if (!selfCover) {
                            let baseCoverPrintCost = 0;
                            
                            if (usePrintSqftPricing && coverPaper.width && coverPaper.height) {
                                // Calculate square footage of the cover sheet
                                const sqft = (coverPaper.width * coverPaper.height) / 144;
                                baseCoverPrintCost = pricingData.price_per_sqft * sqft;
                            } else {
                                baseCoverPrintCost = pricingData.price_per_side;
                            }
                            
                            // Apply the appropriate multiplier based on cover printing options
                            if (coverPrinting === '4/4') { // Full color both sides
                                coverPrintingCost = baseCoverPrintCost * 2; 
                            } else if (coverPrinting === '4/0') { // Full color outside only
                                coverPrintingCost = baseCoverPrintCost; 
                            } else if (coverPrinting === '4/1') { // Full color outside, B&W inside
                                // Assume B&W cost is half of color cost for simplicity
                                coverPrintingCost = baseCoverPrintCost * 1.5; 
                            } else { // B&W both sides
                                // Assume B&W cost is half of color cost for simplicity
                                coverPrintingCost = baseCoverPrintCost; 
                            }
                        }
                        
                        // Calculate binding costs based on binding type
                        let bindingCost = 0;
                        switch(bindingType) {
                            case 'saddle_stitch':
                                bindingCost = 1.00; // Basic cost for saddle stitching
                                break;
                            case 'perfect_bound':
                                bindingCost = 3.50; // Higher cost for perfect binding
                                break;
                            case 'coil':
                                bindingCost = 2.50; // Medium cost for coil binding
                                break;
                            case 'wire_o':
                                bindingCost = 2.75; // Medium-high cost for Wire-O binding
                                break;
                            case 'staple':
                                bindingCost = 0.50; // Low cost for stapling
                                break;
                            default:
                                bindingCost = 1.00; // Default binding cost
                        }
                        
                        // Calculate total unit price
                        const totalPrintingCost = insidePrintingCost + coverPrintingCost;
                        const unitPrice = totalPaperCost + totalPrintingCost + bindingCost;
                        const totalPrice = unitPrice * quantity;
                        
                        // Update the form fields
                        unitPriceInput.val(unitPrice.toFixed(2));
                        totalPriceInput.val(totalPrice.toFixed(2));
                        
                        // Optional: show a breakdown with pricing method info
                        const insidePricingMethod = useInsideSqftPricing ? '(sqft pricing)' : '(sheet pricing)';
                        const coverPricingMethod = selfCover ? '' : (useCoverSqftPricing ? '(sqft pricing)' : '(sheet pricing)');
                        const printPricingMethod = usePrintSqftPricing ? '(sqft pricing)' : '(per-side pricing)';
                        
                        const message = `Booklet Price Calculation:\n` +
                                      `- Inside Paper ${insidePricingMethod} (${pageCount} pages): $${insidePaperCost.toFixed(2)}\n` +
                                      `- Cover Paper ${coverPricingMethod}: $${coverPaperCost.toFixed(2)}\n` +
                                      `- Inside Printing ${printPricingMethod}: $${insidePrintingCost.toFixed(2)}\n` +
                                      `- Cover Printing ${printPricingMethod}: $${coverPrintingCost.toFixed(2)}\n` +
                                      `- Binding (${bindingType.replace('_', ' ')}): $${bindingCost.toFixed(2)}\n` +
                                      `- Total Per Unit: $${unitPrice.toFixed(2)}\n` +
                                      `- Quantity: ${quantity}\n` +
                                      `- Total Price: $${totalPrice.toFixed(2)}`;
                        
                        console.log(message);
                    })
                    .catch(error => {
                        console.error('Error calculating booklet price:', error);
                    });
            },
            error: function() {
                alert('Failed to fetch paper options. Please try again.');
            }
        });
    }
});