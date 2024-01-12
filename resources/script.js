function add_to_history(post_id) {

    // avoid duplication
    let urlFragment = window.location.href.split('#')[1] || {};
    if (urlFragment === post_id) {
        return;
    }

    // update window hash with post id. This forces browser to scroll
    // to the element with that id so we do it before custom scrolling

    // window.location.hash = post_id.toString();
    history.pushState({}, '', '#' + post_id.toString());
}


function post_scroll_to(post_id) {
    // scroll into view of the post or thread
    let scroll_post = document.getElementById(post_id).parentElement.parentElement;
    if (scroll_post.parentElement.parentElement.classList.contains("thread-parent")) {
        // scroll to top of thread
        scroll_post = scroll_post.parentElement.parentElement;
        scroll_post.scrollIntoView({
            behavior:"smooth",
        });
    } else {
        // scroll to middle of post unless it is too long
        if (scroll_post.clientHeight > window.screen.height) {
            scroll_post.scrollIntoView({
                "behavior":"smooth",
            });
        } else {
            scroll_post.scrollIntoView({
                block: "center",
                behavior:"smooth",
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
        return 'Error! Negative time!';
    }

    let time_delta_days = Math.floor(post_time_ago / (60*60*24));
    let time_delta_hours = Math.floor(post_time_ago / (60*60)) % (24);
    let time_delta_minutes = Math.floor(post_time_ago / (60)) % (60);
    let time_delta_seconds = Math.floor(post_time_ago) % (60);

    return_time = ''
    if (time_delta_days == 0) {
        if (time_delta_hours == 0) {
            if (time_delta_minutes == 0) {
                return_time = time_delta_seconds.toString() + 's ago';
            } else {
                return_time = time_delta_minutes.toString() + 'm ago';
            }
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


function strip_post_id_start_chars(rid) {
    // get rid of certain starting substrings
    while (rid.startsWith("#")) { rid = rid.substring(1); }
    while (rid.startsWith("&gt;")) { rid = rid.substring(4); }
    return rid;
}


function event_reply_text(self) {
    let post_id = self.parentElement.parentElement.getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_id = self.innerHTML;
    reply_id = strip_post_id_start_chars(reply_id);

    // uncollapse, colorize and colorize, add to history and scroll
    post_uncollapse(reply_id);
    element_colorize_deterministic(self, reply_id);
    post_colorize_deterministic(reply_id);
    add_to_history(post_id);
    // post_scroll_to(post_id);
    add_to_history(reply_id);
    post_scroll_to(reply_id);
}


function event_file_dump_a(self) {
    let post_id = self.parentElement.parentElement.parentElement.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_id = self.innerHTML;
    reply_id = strip_post_id_start_chars(reply_id);

    // uncollapse, colorize and colorize, add to history and scroll
    post_uncollapse(reply_id);
    element_colorize_deterministic(self, reply_id);
    post_colorize_deterministic(reply_id);
    add_to_history(post_id);
    // post_scroll_to(post_id);
    add_to_history(reply_id);
    post_scroll_to(reply_id);
}


function event_post_a(self) {
    let post_id = self.parentElement.parentElement.parentElement.getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_id = self.innerHTML;
    reply_id = strip_post_id_start_chars(reply_id);

    // uncollapse, colorize and colorize, add to history and scroll
    post_uncollapse(reply_id);
    element_colorize_deterministic(self, reply_id);
    post_colorize_deterministic(reply_id);
    add_to_history(post_id);
    // post_scroll_to(post_id);
    add_to_history(reply_id);
    post_scroll_to(reply_id);
}


function event_post_no(self) {
    let post_id = self.id;
    post_id = strip_post_id_start_chars(post_id);

    // uncollapse, colorize and colorize, add to history and scroll
    post_uncollapse(post_id);
    element_colorize_deterministic(self, post_id);
    post_colorize_deterministic(post_id);
    add_to_history(post_id);
    post_scroll_to(post_id);
}


function event_thread_maximize_replies(self) {
    let thread_element = self.parentNode.parentNode;
    let thread_post_parents = thread_element.querySelectorAll(".post-parent")

    for (let j = 0; j < thread_post_parents.length; j++) {
        let post_id = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
        post_uncollapse(post_id);
    }
}


function event_thread_reset(self) {
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


function event_thread_files_all(self) {
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
        let post_file = thread_post_parents[j].getElementsByClassName("post-file")[0];
        let post_no = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
        if (post_file) {
            post_file = post_file.children[0];
            let div_curr = document.createElement("div");
            let div_curr_child = document.createElement("div");
            let a_curr = document.createElement("a");

            a_curr.innerHTML = post_file.innerHTML;
            a_curr.href = post_file.href;
            a_curr.rel = "noreferrer";
            a_curr.target = "_blank";

            div_curr_child.innerHTML = ">>" + post_no.toString();
            div_curr_child.classList.add("file-dump-a");
            // manipulating innerHTML destroys and recreates everything in div, removing event listeners
            div_curr_child.addEventListener("click", function() {
                event_file_dump_a(this);
            })
            
            div_curr.appendChild(div_curr_child);
            div_curr.appendChild(a_curr);
            thread_files_dump.appendChild(div_curr);

            file_count += 1;
        }
    }
}


function addEventListenerToClass(class_name, execute_function) {
    let all_elements = document.getElementsByClassName(class_name);
    for (let i = 0; i < all_elements.length; i++) {
        all_elements[i].addEventListener("click", function() {
            execute_function(this);
        });
    }
}


function onpageload_popstate() {
    // uncollapse, colorize, scroll to the post in the url hash
    if(window.location.hash) {
    let post_id = Number(window.location.hash.substring(1));
    post_uncollapse(post_id);
    post_colorize_deterministic(post_id);
    setTimeout(function() {
        post_scroll_to(post_id);
        }, 500);  // for some reason it doesn't work well without a timeout
    }
}


window.addEventListener('popstate', function() {
    // make back button work perfectly, scroll to prev post regardless of divs uncollapsing
    onpageload_popstate();
});


window.onload = function() {
    // convert unix timestamps to time ago
    let thread_post_times = document.querySelectorAll(".board-time,.thread-time,.post-time");
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
            let post_id = this.parentNode.parentNode.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_id);
            add_to_history(post_id);
            post_scroll_to(post_id);
        });
    }

    let post_collapsibles = document.getElementsByClassName("post-collapsible-anchor");
    for (let i = 0; i < post_collapsibles.length; i++) {
        post_collapsibles[i].addEventListener("click", function() {
            let post_id = this.parentNode.parentNode.getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_id);
        });
    }

    addEventListenerToClass("reply-text",       event_reply_text);
    addEventListenerToClass("post-a",           event_post_a);
    addEventListenerToClass("post-no",          event_post_no);
    addEventListenerToClass("thread-maximize-replies",  event_thread_maximize_replies);
    addEventListenerToClass("thread-reset",             event_thread_reset);
    addEventListenerToClass("thread-files-all",         event_thread_files_all);

    // scroll to the #fragment
    onpageload_popstate();
}