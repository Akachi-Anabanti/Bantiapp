function set_message_count(n) {
  $("#message_count").text(n);
  $("#message_count").css("display", n ? "inline-block" : "none");
}
