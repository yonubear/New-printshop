// First create the quote, then we will redirect to edit page to add items
const mainForm = document.querySelector('form[action="{{ url_for(\'quotes_create\') }}"]');

// Add a hidden field to ensure the customer_id is passed correctly
const customerIdValue = document.getElementById("customer_id").value;
console.log("Using customer ID:", customerIdValue); // Debug output

// Create a hidden field if it doesn't exist
let hiddenField = mainForm.querySelector('input[name="customer_id_hidden"]');
if (!hiddenField) {
    hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = 'customer_id_hidden';
    mainForm.appendChild(hiddenField);
}
hiddenField.value = customerIdValue;

// Submit the main form
mainForm.submit();
return false;
