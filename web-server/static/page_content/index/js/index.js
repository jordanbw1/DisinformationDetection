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

    // Prepare the additional text to append to the prompt
    var additionalText = promptText + "\nYour answer will have 4 sections separated by a ';'.\n";
    additionalText += "Section 1 - a one number response of either '1' if it is factual or '0' if it is disinformation.\n";
    additionalText += "Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct.\n";
    additionalText += "Section 3 - a level from 1-12 on how truthful the twitter post is.\n";
    additionalText += "Section 4 - An explanation of why the post is fact or fake and why you gave the confidence level you did.\n";
    additionalText += "Here is the twitter post:";

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