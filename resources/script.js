function post_scroll_to(post_id) {
        // update window hash with post id. This forces browser to scroll 
        // to the element with that id so we do it before custom scrolling
        // window.location.hash = post_id.toString();
        history.pushState({}, '', '#' + post_id.toString())

        // scroll into view of the post or thread
        let scroll_post = document.getElementById(post_id).parentElement.parentElement;
        if (scroll_post.parentElement.parentElement.classList.contains("thread-parent")) {
            scroll_post = scroll_post.parentElement.parentElement;
        }
        scroll_post.scrollIntoView();
}


function post_collapse(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;

    // depending on whether its the OP, collapse the thread or just the post
    if (original_post.parentElement.parentElement.classList.contains("thread-parent")) {
        original_post.parentElement.parentElement.classList.add("collapsed-thread-parent");

    } else {
        original_post.classList.add("collapsed");
        original_post.parentElement.classList.add("collapsed-parent");
    }
}


function post_uncollapse(post_id) {
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
}


function post_toggle_collapse(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;
    let return_value = -1;

    if (original_post.classList.contains("collapsed") || original_post.parentElement.parentElement.classList.contains("collapsed-thread-parent")) {
        post_uncollapse(post_id);
        return_value = 1;
    } else {
        post_collapse(post_id);
        return_value = 0;
    }
    return return_value;
}


function generate_random_string(length, allowed_chars) {
    let return_value = '';
    for (let i = 0; i < length; i++) {
        let random_index = Math.floor(Math.random() * allowed_chars.length);
        return_value += allowed_chars[random_index];
    }
    return return_value;
}


function post_colorize_random(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;
    let color_hex = "#" + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef");
    original_post.style.background = color_hex;
}


window.onload = function() {
    // add all the event listeners

    let thread_collapsibles = document.getElementsByClassName("thread-collapsible-anchor");
    for (let i = 0; i < thread_collapsibles.length; i++) {
        thread_collapsibles[i].addEventListener("click", function() {
            let post_id_curr = this.parentNode.parentNode.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_id_curr);
            post_scroll_to(post_id_curr);
        });
    }

    let post_collapsibles = document.getElementsByClassName("post-collapsible-anchor");
    for (let i = 0; i < post_collapsibles.length; i++) {
        post_collapsibles[i].addEventListener("click", function() {
            let post_id_curr = this.parentNode.parentNode.getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_id_curr);
        });
    }

    let reply_posts = document.getElementsByClassName("reply-text");
    for (let i = 0; i < reply_posts.length; i++) {
        reply_posts[i].addEventListener("click", function() {
            let reply_id = this.innerHTML;
            if (reply_id.startsWith("&gt;")) {
                reply_id = reply_id.substring(4);
            }
            post_uncollapse(reply_id);
            post_colorize_random(reply_id);
            post_scroll_to(reply_id);
        });
    }

    let post_as = document.getElementsByClassName("post-a");
    for (let i = 0; i < post_as.length; i++) {
        post_as[i].addEventListener("click", function() {
            let reply_id = this.innerHTML;
            if (reply_id.charAt(0) == "#") {
                reply_id = reply_id.substring(1);
            }
            post_uncollapse(reply_id);
            post_colorize_random(reply_id);
            post_scroll_to(reply_id);
        });
    }    

    let thread_uncollapse_all = document.getElementsByClassName("thread-uncollapse-all");
    for (let i = 0; i < thread_uncollapse_all.length; i++) {
        thread_uncollapse_all[i].addEventListener("click", function() {
            let thread_element = this.parentNode;
            let thread_post_parents = thread_element.querySelectorAll(".post-parent")

            for (let j = 0; j < thread_post_parents.length; j++) {
                let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
                post_uncollapse(post_id);
            }
        });
    }   
}

window.onpageshow = function() {
    // uncollapse, colorize, scroll to the post in the url hash
    if(window.location.hash) {
        let post_id = Number(window.location.hash.substring(1));
        post_uncollapse(post_id);
        post_colorize_random(post_id);
        post_scroll_to(post_id);
    }
};
  