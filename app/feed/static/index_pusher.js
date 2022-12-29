const pusher = new Pusher("d844ca1a998cb88283fb", {
  cluster: "eu",
  encrypted: true, //optional
});

const channel = pusher.subscribe("blog");

channel.bind("post-added", (data) => {
  appendTolist(data);
});

channel.bind("post-deleted", (data) => {
  const post = document.querySelector(`#${data.id}`);
  post.parentNode.removeChild(post);
});

channel.bind("post-deactivated", (data) => {
  const post = document.querySelector(`#${data.id}`);
  post.classList.add("deactivated");
});
