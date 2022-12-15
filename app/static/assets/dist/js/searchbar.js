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

// input.addEventListener("change", stateHandle);

// // function to delete all child elements on change
// function stateHandle() {
//   searchbar = document.getElementById("SearchBar");
//   if (input.value === "") {
//     var child = searchbar.lastElementChild;
//     while (child) {
//       searchbar.removeChild(child);
//       child = searchbar.lastElementChild;
//     }
//   }
// }
// Execute a function when the user presses a key on the keyboard
input.addEventListener("keypress", function (event) {
  // If the user presses the "Enter" key on the keyboard
  if (event.key === "Enter" && input.value !== "") {
    // Cancel the default action, if needed
    event.preventDefault();
    // Trigger the button element with a click
    // document.getElementById("myBtn").click();
    var searchbar = document.getElementById("SearchBar");
    var child = searchbar.firstElementChild;
    while (child.nextElementSibling) {
      searchbar.removeChild(child.nextElementSibling);
      child = searchbar.firstElementChild;
    }

    $.ajax({
      type: "get",
      url: `http://127.0.0.1:4000/search?q=${input.value}`,
      success: function (resp) {
        let data = Object(resp);

        for (let i = 0; i < data.length; i++) {
          const node1 = document.createElement("div");
          node1.classList.add(
            "w3-container",
            "w3-card",
            "w3-round",
            "w3-margin"
          );
          node1.style.transform = "rotate(0)";
          node1.style.position = "relative";
          node1.innerHTML = `<a class="stretched-link" href="${data[i].postUrl}"></a><img class="w3-circle w3-margin-top w3-left w3-margin-right" src="${data[i].imgUrl}" alt="Avatar" style="width:30px"/> <p class="w3-margin-top" style="z-index:1000; position:relative"><a href="${data[i].userUrl}">${data[i].username}</a></p><hr class="w3-clear"/><p class="w3-container">${data[i].body}</p>`;
          // const textnode = document.createTextNode(data[i].username);
          // node.appendChild(textnode);
          searchbar.appendChild(node1);
        }
      },
    });
  }
});
