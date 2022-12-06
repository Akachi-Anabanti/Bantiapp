$(function () {
  let since = 0.0;
  setInterval(function () {
    $.ajax(`http://127.0.0.1:4000/notifications?since=${since}`).done(function (
      notifications
    ) {
      for (let i = 0; i < notifications.length; i++) {
        if (notifications[i].name == "unread_message_count") {
          set_message_count(notifications[i].data);
        }
        since = notifications[i].timestamp;
      }
    });
  }, 10000);
});
