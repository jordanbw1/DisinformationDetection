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