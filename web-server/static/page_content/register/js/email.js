var emailInput = document.getElementById("email");
var validEmail = document.getElementById("validemail");
var byuEmail = document.getElementById("byuemail");

// When the user clicks on the password field, show the message box
emailInput.onfocus = function() {
    document.getElementById("emessage").style.display = "block";
}

// When the user clicks outside of the password field, hide the message box
emailInput.onblur = function() {
    document.getElementById("emessage").style.display = "none";
}

// When the user starts to type something inside the password field
emailInput.onkeyup = function() {
  // Test if email matches regex
  if (emailInput.value.match(/^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/)) {
      validEmail.classList.remove("invalid");
      validEmail.classList.add("valid");
  } else {
      validEmail.classList.remove("valid");
      validEmail.classList.add("invalid");
  }

  // Define the regex pattern
  var byuRegex = /@(?:[a-zA-Z0-9-]+\.)?byu\.edu$/;
  if (byuRegex.test(emailInput.value)) {
    byuEmail.classList.remove("invalid");
    byuEmail.classList.add("valid");
  } else {
    byuEmail.classList.remove("valid");
    byuEmail.classList.add("invalid");
  }


}