const form = document.querySelector("#post-form");

form.onsubmit = (e) => {
  e.preventDefault();
  fetch("/post", {
    method: "POST",
    body: new FormData(form),
  }).then((r) => {
    form.reset();
  });
};

//

function delePost(id) {
  fetch(`/post/${id}`, {
    method: "DELETE",
  });
}

//apends new post tot he list of blog posts on the page

function appendTolist(data) {
  const html = `
    <div class="card" id="${data.id}">
        <header class="card-header">
            <p class="card-header-title">${data.title}</p>
        </header>
        <div class="card-content">
            <div class="card-content">
                <p>${data.content}</p>
            </div>
        
        </div>
        <footer class="card-footer">
            <a href="#" onclick="deactivatePost('${data.id}')" class="card-footer-item">Deactivate</a>
            <a href="#" onlclick="deletePost('${data.id}')" class="card-footer-item">Delete</a>
        </footer>
    </div>
    `;
  let list = document.querySelector("#post-list");
  list.innerHTML += html;
}
