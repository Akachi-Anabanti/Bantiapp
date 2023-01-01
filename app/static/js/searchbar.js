function w3_open() {
  document.getElementById("SearchBar").style.width = "25%";
  document.getElementById("SearchBar").style.marginLeft = "15%";
  document.getElementById("SearchBar").classList.add("w3-animate-left");
  document.getElementById("SearchBar").style.display = "block";
}
function w3_close() {
  document.getElementById("SearchBar").style.display = "none";
}

// Get the input field
var input = document.getElementById("example-search-input");
input.addEventListener("keypress", function (event) {
  // If the user presses the "Enter" key on the keyboard
  if (event.key === "Enter" && input.value !== "") {
    // Cancel the default action, if needed
    event.preventDefault();

    $(function () {
      $.ajax(`/search?q=${input.value}&s=l`).done(function (data) {
        document.getElementById("search-results").innerHTML = data;
      });
    });
  }
});
