$(function () {
  let since = 0.0;
  setInterval(function () {
    $.ajax(`http://127.0.0.1:4000/notifications?since=${since}`).done(function (
      notifications
    ) {
      for (let i = 0; i < notifications.length; i++) {
        switch (notifications[i].name) {
          case "unread_message_count":
            set_message_count(notifications[i].data);
            break;
          case "task_progress":
            set_task_progess(
              notifications[i].data.task_id,
              notifications[i].data.progress
            );
            break;
        }
        since = notifications[i].timestamp;
      }
    });
  }, 10000);
});
