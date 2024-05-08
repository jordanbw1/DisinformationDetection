var datasets = JSON.parse(document.getElementById('dataset-data').textContent);

// JavaScript function to auto-resize the textarea
function autoResize(textarea) {
    textarea.style.height = "auto"; // Reset height
    textarea.style.height = textarea.scrollHeight + "px"; // Set new height based on content
}

// Call autoResize function on page load to set initial height
window.addEventListener("load", function() {
    var textarea = document.getElementById("prompt");
    autoResize(textarea);
});

// Function to update AI prompt based on user input
function updateAIPrompt() {
    // Get the text entered by the user in the prompt input box
    var promptText = document.getElementById("prompt").value;
    var instructionsText = document.getElementById("instructions").value;

    // Prepare the additional text to append to the prompt
    var additionalText = promptText + instructionsText;

    // Get the reference to the aiprompt textarea
    var aipromptTextArea = document.getElementById("aiprompt");

    // Write the updated prompt text into the aiprompt textarea
    aipromptTextArea.value = additionalText;
}

// Add event listener to prompt input box to trigger the updateAIPrompt function on input change
document.getElementById("prompt").addEventListener("input", updateAIPrompt);

// Prevnt num-rows from being set out of bounds.
document.addEventListener("DOMContentLoaded", function() {
    // Get the input element for num-rows
    var numRowsInput = document.getElementById("num-rows");

    // Add an event listener for the input event
    numRowsInput.addEventListener("input", function() {
        // Get the current value of the input
        var currentValue = parseInt(numRowsInput.value);

        // Check if the value is less than 0
        if (currentValue < 0) {
            numRowsInput.value = 0; // Set the value to 0
        }
        // Check if the value is greater than 500
        else if (currentValue > 500) {
            numRowsInput.value = 500; // Set the value to 500
        }
    });
});

// Disable submit button after form is submitted
function disableSubmitButton() {
    document.querySelector('.submit').disabled = true;
}

// Call disableSubmitButton function when the form is submitted
document.querySelector('form').addEventListener('submit', disableSubmitButton);

// Function to update the maximum number of rows based on the selected dataset
function updateMaxRows() {
    // Get the selected dataset from the dropdown
    var datasetDropdown = document.getElementById("dataset");
    var selectedDataset = datasetDropdown.value;

    // Get the input element for num-rows
    var numRowsInput = document.getElementById("num-rows");
    var numRowsLabel = document.getElementById("num-rows-label");

    // Update the maximum number of rows based on the selected dataset
    var maxRows = datasets[selectedDataset] || 500; // Default to 500 if dataset not found
    numRowsInput.setAttribute("max", maxRows);

    // Update the label text
    numRowsLabel.textContent = "Number of rows to test (optional, max: " + maxRows + "):";
}

// Add event listener to dataset dropdown to trigger the updateMaxRows function on change
document.getElementById("dataset").addEventListener("change", updateMaxRows);

// Call updateMaxRows function on page load to set initial max rows
window.addEventListener("load", updateMaxRows);