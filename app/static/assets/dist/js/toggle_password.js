function togglePasswordShow() {
  var x = document.getElementById("registration-password");
  if (x.type === "password") {
    x.type = "text";
  } else {
    x.type = "password";
  }
}

//CAPSLOCK DETECTION
// Get the input field
var input = document.getElementById("registration-password");
if (input) {
  // Get the warning text
  var text = document.getElementById("capslock-text");

  // When the user presses any key on the keyboard, run the function

  input.addEventListener("keyup", function (event) {
    // If "caps lock" is pressed, display the warning text
    if (event.getModifierState("CapsLock")) {
      text.style.display = "block";
    } else {
      text.style.display = "none";
    }
  });
}
