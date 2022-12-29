function menuPopover(username) {
  elem = document.getElementById("userMenu");
  html = `<div class="w3-container">
                <div>
                </div>
                <hr class="w3-clear" />
                <div>
                <a href="/auth/logout" style="text-decoration=none;">Logout out of ${username}</a>
                </div>
            </div> `;

  elem
    .popover({
      trigger: "manual",
      html: true,
      animation: false,
      container: elem,
      content: html,
    })
    .popover("show");
}
$("#userMenu").click();
