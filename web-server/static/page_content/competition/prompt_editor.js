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

// Disable submit button after form is submitted
function disableSubmitButton() {
    document.querySelector('.submit').disabled = true;
}

// Call disableSubmitButton function when the form is submitted
document.querySelector('form').addEventListener('submit', disableSubmitButton);
