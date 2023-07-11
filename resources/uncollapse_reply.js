function uncollapse_reply(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;

    if (original_post.classList.contains("collapsed")) {
        original_post.classList.remove("collapsed");
    }

    let post = original_post.parentElement;

    while(
        post.classList.contains("post-parent-r") || 
        post.classList.contains("thread-parent")
    ) {

        if (post.classList.contains("collapsed-parent")) {
            post.classList.remove("collapsed-parent");
        }

        for (let i = 0; i < post.children.length; i++) {
            if (
                (post.children[i].classList.contains('post-parent')) && 
                (post.children[i].classList.contains('collapsed'))
            ) {
                post.children[i].classList.remove('collapsed');
            }
        }

        if (post.classList.contains("collapsed-thread-parent")) {
            post.classList.remove("collapsed-thread-parent");
        }

        post = post.parentElement;
    }

    original_post.scrollIntoView();
    window.location.hash = post_id.toString();
}


function uncollapse_reply_wrapper(element) {
    uncollapse_reply(element.parentElement.id);
}


if(window.location.hash) {
    let post_id = Number(window.location.hash.substring(1));
    uncollapse_reply(post_id);
}
  