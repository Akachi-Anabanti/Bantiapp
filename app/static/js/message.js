function set_message_count(n) {
  //USED FOR THE MESSAGE COUNT
  $("#message_count").text(n);
  $("#message_count").css("display", n ? "inline-block" : "none");
}

function set_message_indicator(n) {
  el = document.getElementById("message_badge");
  if (n) {
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}

function set_notification_count(n) {
  //USED FOR THE NOFTIFACTION COUNT
  $("#notification_count").text();
  $("#notification_count").css("display", n ? "inline-block" : "none");
}
function set_bell_indicator(n) {
  //USED TO SET THE BELL COLOR
  let el = document.getElementById("notification_badge");
  if (n) {
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}
function set_bell_indicator_small(n) {
  //USED TO SET THE BELL COLOR
  let el = document.getElementById("notification_badge_small");
  if (n) {
    el.style.display = "block";
  } else {
    el.style.display = "none";
  }
}
//Notification
function notification_close() {
  document.getElementById("notification-card").style.display = "none";
  document.getElementById("notification-button").style.pointerEvents = "auto";
  document.getElementById("notification-button").style.cursor = "pointer";
  const notification = document.getElementById("notification-card");
  notification.innerHTML = "";
}

function display_notification() {
  $.ajax({
    url: "/notification_list?s=l",
    type: "GET",
    success: function (resp) {
      const data = new Object(resp);
      const notify = document.getElementById("notification-card");
      notify.style.width = "25%";
      notify.style.marginLeft = "15%";
      notify.classList.add("w3-animate-left");
      notify.style.display = "block";

      document.getElementById("notification-content").innerHTML = resp;
      notify.getElementById("notification-button").style.pointerEvents = "none";
      notify.getElementById("notification-button").style.cursor = "default";
    },
  });
}
