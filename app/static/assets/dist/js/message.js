function set_message_count(n) {
  $("#message_count").text(n);
  $("#message_count").css("visibility", n ? "visible" : "hidden");
}
