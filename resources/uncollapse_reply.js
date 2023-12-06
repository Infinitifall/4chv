function uncollapse_reply(post_id) {
    if (isNaN(post_id)) { return; }
    let original_post = document.getElementById(post_id).parentElement.parentElement;

    if (original_post.classList.contains("collapsed")) {
        original_post.classList.remove("collapsed");
    }

    // go up through the parents and uncollapse them all
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

    // update window hash with post id
    // remember, this forces browser to scroll to element with that id
    // so we do it before custom scrolling
    window.location.hash = post_id.toString();

    // scroll into view of the post or thread
    let scroll_post = original_post;
    if (scroll_post.parentElement.parentElement.classList.contains("thread-parent")) {
        scroll_post = scroll_post.parentElement.parentElement;
    }
    scroll_post.scrollIntoView();
    
}


function uncollapse_reply_wrapper(element) {
    uncollapse_reply(element.parentElement.id);
}


// uncollapse and (hopefully) force scroll to the desired post
window.onload = function() {
    if(window.location.hash) {
        let post_id = Number(window.location.hash.substring(1));
        uncollapse_reply(post_id);
    }
};
  