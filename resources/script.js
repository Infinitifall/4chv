function post_scroll_to(post_id) {
        // update window hash with post id. This forces browser to scroll
        // to the element with that id so we do it before custom scrolling
        // window.location.hash = post_id.toString();
        history.pushState({}, '', '#' + post_id.toString());

        // scroll into view of the post or thread
        let scroll_post = document.getElementById(post_id).parentElement.parentElement;
        if (scroll_post.parentElement.parentElement.classList.contains("thread-parent")) {
            // scroll to top of thread
            scroll_post = scroll_post.parentElement.parentElement;
            scroll_post.scrollIntoView();
        } else {
            // scroll to middle of post unless it is too long
            if (scroll_post.clientHeight > window.screen.height) {
                scroll_post.scrollIntoView();
            } else {
                scroll_post.scrollIntoView({
                    block: 'center'
                });
            }
        }
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


function custom_format_datetime_ago(unix_timestamp) {
    let curr_time = new Date();
    let post_time = new Date(unix_timestamp * 1000);
    let post_time_ago = (curr_time.getTime() - post_time.getTime()) / 1000;

    if (post_time_ago < 0) {
        return '';
    }

    let time_delta_days = Math.floor(post_time_ago / (60*60*24));
    let time_delta_hours = Math.floor(post_time_ago / (60*60)) % (24);
    let time_delta_minutes = Math.floor(post_time_ago / (60)) % (60);

    return_time = ''
    if (time_delta_days == 0) {
        if (time_delta_hours == 0) {
            return_time = time_delta_minutes.toString() + 'm ago';
        } else {
            return_time = time_delta_hours.toString() + 'h ' + time_delta_minutes.toString() + 'm ago';
        }
    } else {
        return_time = time_delta_days.toString() + 'd ' + time_delta_hours.toString() + 'h ago';
    }

    return return_time;
}


function post_colorize_random(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;
    let color_hex = "#" + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef");
    original_post.style.background = color_hex;
}


function get_post_color_determinstic(post_id) {
    let random_choice1 = Math.abs(Math.sin(post_id)).toString(16).substring(2 + 1);
    let random_choice2 = Math.abs(Math.sin(post_id)).toString(2).substring(2 + 1);
    let random_choice_2_sub = ""
    for (let i = 0; i < random_choice2.length; i++) { if (random_choice2.charAt(i) == 0) { random_choice_2_sub += "2"; } else { random_choice_2_sub += "2"; }}
    let color_hex = "#" + random_choice_2_sub.slice(0,1) + random_choice1.slice(0,1) + random_choice_2_sub.slice(1,2) + random_choice1.slice(1,2) + random_choice_2_sub.slice(2,3) + random_choice1.slice(2,3);
    return color_hex;
}


function post_colorize_deterministic(post_id) {
    let original_post = document.getElementById(post_id).parentElement.parentElement;
    original_post.style.background = get_post_color_determinstic(post_id);
    original_post.style.border = "1px solid #666";
}


function element_colorize_deterministic(element, post_id) {
    element.style.background = get_post_color_determinstic(post_id);
    element.style.border = "1px solid #444";
}


function event_function_1(self) {
    let reply_id = self.innerHTML;
    while (reply_id.startsWith("#")) { reply_id = reply_id.substring(1); }
    while (reply_id.startsWith("&gt;")) { reply_id = reply_id.substring(4); }
    post_uncollapse(reply_id);
    element_colorize_deterministic(self, reply_id);
    post_colorize_deterministic(reply_id);
    post_scroll_to(reply_id);
}


function event_function_2(self) {
    let reply_id = self.innerHTML;
    while (reply_id.startsWith("#")) { reply_id = reply_id.substring(1); }
    while (reply_id.startsWith("&gt;")) { reply_id = reply_id.substring(4); }
    post_uncollapse(reply_id);
    element_colorize_deterministic(self, reply_id);
    post_colorize_deterministic(reply_id);
    post_scroll_to(reply_id);
}


function event_function_3(self) {
    let thread_element = self.parentNode.parentNode;
    let thread_post_parents = thread_element.querySelectorAll(".post-parent")

    for (let j = 0; j < thread_post_parents.length; j++) {
        let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
        post_uncollapse(post_id);
    }
}


function event_function_4(self) {
    let thread_files_dump = self.parentNode.parentNode.getElementsByClassName("thread-files-dump")[0];
    let thread_files_dump_children = thread_files_dump.children;

    // clear thread_files_dump of all links first
    let thread_files_dump_children_length_curr = thread_files_dump_children.length;
    for (let j = 0; j < thread_files_dump_children_length_curr; j++) {
        thread_files_dump_children[0].remove();
    }

    let thread_element = self.parentNode.parentNode;
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
}


function event_function_5(self) {
    let thread_files_dump = self.parentNode.parentNode.getElementsByClassName("thread-files-dump")[0];
    let thread_files_dump_children = thread_files_dump.children;

    let thread_element = self.parentNode.parentNode;
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
}


window.onload = function() {
    // convert unix timestamps to time ago

    let thread_post_times = document.querySelectorAll(".thread-time,.post-time");
    for (let i = 0; i < thread_post_times.length; i++) {
        let time_element_curr = thread_post_times[i];
        let time_element_time = time_element_curr.innerHTML;
        time_element_time = custom_format_datetime_ago(time_element_time);
        time_element_curr.innerHTML = time_element_time;
    }

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
            event_function_1(this);
        });
    }

    let post_as = document.querySelectorAll(".post-a,.post-no");
    for (let i = 0; i < post_as.length; i++) {
        post_as[i].addEventListener("click", function() {
            event_function_2(this);
        });
    }

    let thread_maximize_replies = document.getElementsByClassName("thread-maximize-replies");
    for (let i = 0; i < thread_maximize_replies.length; i++) {
        thread_maximize_replies[i].addEventListener("click", function() {
            event_function_3(this);
        });
    }

    let thread_reset = document.getElementsByClassName("thread-reset");
    for (let i = 0; i < thread_reset.length; i++) {
        thread_reset[i].addEventListener("click", function() {
            event_function_4(this);
        });
    }

    let thread_files_all = document.getElementsByClassName("thread-files-all");
    for (let i = 0; i < thread_files_all.length; i++) {
        thread_files_all[i].addEventListener("click", function() {
            event_function_5(this);
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

