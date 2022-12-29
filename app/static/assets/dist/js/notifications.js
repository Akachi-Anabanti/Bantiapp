$(function () {
  let since = 0.0;
  setInterval(function () {
    $.ajax(`/notifications?since=${since}`).done((notifications) => {
      for (let i = 0; i < notifications.length; i++) {
        switch (notifications[i].name) {
          case "unread_message_count":
            set_message_indicator(notifications[i].data);
            break;
          case "task_progress":
            set_task_progess(
              notifications[i].data.task_id,
              notifications[i].data.progress
            );
            break;
          case "user_followed":
            // window.alert(notifications[i].data);
            set_bell_indicator(notifications[i].data);
            set_bell_indicator_small(notifications[i].data);

            break;
          case "post_liked":
            set_bell_indicator(notifications[i].data);
            set_bell_indicator_small(notifications[i].data);
            break;
        }
        since = notifications[i].timestamp;
      }
    });
  }, 10000);
});

$(function () {
  setInterval(function () {
    //USERS TO FOLLOW LOADER
    $.ajax("/user/users-recommended").done(function (data) {
      if (data.length === 0) {
      } else {
        document.getElementById("people-know").style.display = "block";
        document.getElementById("recommended-users").innerHTML = data;
      }
    });

    //Activity suggestion API
    $.ajax("https://www.boredapi.com/api/activity").done(function (data) {
      //Returns the json format
      // {
      //   "activity":"Find a charity and donate to it",
      //   "type":"charity",
      //   "participants":1,
      //   "price":0.4,
      //   "link":"",
      //   "key":"1488053",
      //   "accessibility":0.1
      // }
      document.getElementById("recommended-activity-type").innerHTML =
        data.type;
      document.getElementById("recommended-activity").innerHTML = data.activity;
      document.getElementById("recommended-activities-div").style.display =
        "block";
    });
  }, 50000);
});
