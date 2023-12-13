function post_scroll_to(post_id) {
        // update window hash with post id. This forces browser to scroll 
        // to the element with that id so we do it before custom scrolling
        // window.location.hash = post_id.toString();
        history.pushState({}, '', '#' + post_id.toString());

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


function get_post_color_determinstic(post_id) {
    let random_choice1 = Math.abs(Math.sin(post_id)).toString(16).substring(2 + 1);
    let random_choice2 = Math.abs(Math.sin(post_id)).toString(2).substring(2 + 1);
    for (let i = 0; i < random_choice2.length; i++) { if (random_choice2.charAt(i) == 0) { random_choice2[i] = 1 } else { random_choice2[i] = 2 }}
    let color_hex = "#" + random_choice2.slice(0,1) + random_choice1.slice(0,1) + random_choice2.slice(1,2) + random_choice1.slice(1,2) + random_choice2.slice(2,3) + random_choice1.slice(2,3);
    return color_hex;
}


function post_colorize_deterministic(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;
    original_post.style.background = get_post_color_determinstic(post_id);
}


function element_colorize_deterministic(element, post_id) {
    element.style.background = get_post_color_determinstic(post_id);
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
            element_colorize_deterministic(this, reply_id);
            post_colorize_deterministic(reply_id);
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
            element_colorize_deterministic(this, reply_id);
            post_colorize_deterministic(reply_id);
            post_scroll_to(reply_id);
        });
    }    

    let thread_maximize_replies = document.getElementsByClassName("thread-maximize-replies");
    for (let i = 0; i < thread_maximize_replies.length; i++) {
        thread_maximize_replies[i].addEventListener("click", function() {
            let thread_element = this.parentNode.parentNode;
            let thread_post_parents = thread_element.querySelectorAll(".post-parent")

            for (let j = 0; j < thread_post_parents.length; j++) {
                let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
                post_uncollapse(post_id);
            }
        });
    }

    let thread_reset = document.getElementsByClassName("thread-reset");
    for (let i = 0; i < thread_reset.length; i++) {
        thread_reset[i].addEventListener("click", function() {
            let thread_files_dump = this.parentNode.getElementsByClassName("thread-files-dump")[0];
            let thread_files_dump_children = thread_files_dump.children;
            
            // clear thread_files_dump of all links first
            let thread_files_dump_children_length_curr = thread_files_dump_children.length;
            for (let j = 0; j < thread_files_dump_children_length_curr; j++) {
                thread_files_dump_children[0].remove();
            }

            let thread_element = this.parentNode.parentNode;
            let thread_post_parents = thread_element.querySelectorAll(".post-parent")

            // first uncollapse the ones not originally collapsed
            for (let j = 0; j < thread_post_parents.length; j++) {
                let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
                if (!thread_post_parents[j].classList.contains("collapsed-originally")) {
                    post_uncollapse(post_id);
                }                
            }

            // then collapse the ones originally collapsed
            for (let j = 0; j < thread_post_parents.length; j++) {
                let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;

                if (thread_post_parents[j].classList.contains("collapsed-originally")) {
                    post_collapse(post_id);
                }                
            }
        });
    }

    let thread_files_all = document.getElementsByClassName("thread-files-all");
    for (let i = 0; i < thread_files_all.length; i++) {
        thread_files_all[i].addEventListener("click", function() {
            let thread_files_dump = this.parentNode.getElementsByClassName("thread-files-dump")[0];
            let thread_files_dump_children = thread_files_dump.children;

            let thread_element = this.parentNode.parentNode;
            let thread_post_parents = thread_element.querySelectorAll(".post-parent");
            
            // clear thread_files_dump of all links first
            let thread_files_dump_children_length_curr = thread_files_dump_children.length;
            for (let j = 0; j < thread_files_dump_children_length_curr; j++) {
                thread_files_dump_children[0].remove();
            }
            
            // dump all file links in thread_files
            let file_count = 0;
            for (let j = 0; j < thread_post_parents.length; j++) {
                let post_file = thread_post_parents[j].getElementsByClassName("post-file")[0].children[0];
                if (post_file.innerHTML) {
                    let div_curr = document.createElement("div");
                    let a_curr = document.createElement("a");
                    a_curr.innerHTML = post_file.innerHTML;
                    a_curr.href = post_file.href;
                    a_curr.rel = "noreferrer";
                    a_curr.target = "_blank";
                    div_curr.innerHTML = (file_count + 1).toString() + ". ";
                    div_curr.appendChild(a_curr);
                    thread_files_dump.appendChild(div_curr);

                    file_count += 1;
                }
            }
        });
    }
}

window.onpageshow = function() {
    // uncollapse, colorize, scroll to the post in the url hash
    if(window.location.hash) {
        let post_id = Number(window.location.hash.substring(1));
        post_uncollapse(post_id);
        post_colorize_deterministic(post_id);
        post_scroll_to(post_id);
    }
};
  