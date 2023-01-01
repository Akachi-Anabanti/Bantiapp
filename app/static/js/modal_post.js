function setModalPost(post_id) {
  $(`#comment-button-${post_id}`).click(function () {
    const modal = document.getElementById(`modalComment-${post_id}`);
    const PostAuthor = document.getElementById(`PostAuthor-${post_id}`);
    const PostBody = document.getElementById(`PostBody-${post_id}`);
    const PostTime = document.getElementById(`PostTime-${post_id}`);
    const PostImage = document.getElementById(`PostImage-${post_id}`);
    const PostTimeLong = document.getElementById(`PostTimeLong-${post_id}`);
    const PostURL = document.getElementById(`PostUrl-${post_id}`);
    const modalPostAuthor = document.getElementById(
      `modalPostAuthor-${post_id}`
    );
    const _modalPostAuthor = document.getElementById(
      `_modalPostAuthor-${post_id}`
    );
    const modalPostBody = document.getElementById(`modalPostBody-${post_id}`);
    const modalPostTime = document.getElementById(`modalPostTime-${post_id}`);
    const modalPostImage = document.getElementById(`modalPostImage-${post_id}`);
    const modalPostTimeLong = document.getElementById(
      `modalPostTimeLong-${post_id}`
    );
    const ModalCommentForm = document.getElementById(
      `ModalCommentForm-${post_id}`
    );
    modalPostAuthor.innerHTML = PostAuthor.innerHTML;

    modalPostAuthor.href = PostAuthor.href;
    _modalPostAuthor.innerHTML = PostAuthor.innerHTML;
    _modalPostAuthor.href = PostAuthor.href;

    modalPostBody.innerHTML = PostBody.innerHTML;
    modalPostTime.innerHTML = PostTime.innerHTML;
    modalPostImage.src = PostImage.src;
    modalPostTimeLong.innerHTML = PostTimeLong.innerHTML;
    ModalCommentForm.action = PostURL.href;

    modal.style.display = "block";
  });
}
