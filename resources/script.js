function get_post_from_no(post_no) {
    return document.getElementById(post_no).parentElement.parentElement;
}


function get_post_no_from_post(post) {
    return post.getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
}


function is_post_a_thread(post) {
    return post.parentElement.parentElement.classList.contains("thread-parent");
}


function get_thread_from_post(post) {
    return post.parentElement.parentElement;
}


function get_file_from_post(post) {
    let post_file = post.getElementsByClassName("post-file")[0];
    if (!post_file) {
        return null;
    }
    return post_file.children[0];
}


function get_post_no_from_thread(thread) {
    return thread.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
}


function get_child_post_no(post_no) {
    let curr_post = get_post_from_no(post_no);
    let next_post_parent_r = curr_post.parentElement.getElementsByClassName("post-parent-r");
    if (next_post_parent_r.length == 0) {
        return null;
    }
    next_post = next_post_parent_r[0].getElementsByClassName("post-parent")[0];
    return get_post_no_from_post(next_post);
}


function get_parent_post_no(post_no) {
    let curr_post = get_post_from_no(post_no);
    let grandparent_post = curr_post.parentElement.parentElement;
    if (grandparent_post.classList.contains("thread-parent")) {
        return;
    }
    let parent_post = grandparent_post.getElementsByClassName("post-parent")[0];
    return get_post_no_from_post(parent_post);
}


function get_next_post_no(post_no, previous) {
    let current_post = get_post_from_no(post_no);
    let current_post_parent_r = current_post.parentElement;
    let next_post_parent_r = null;
    if (previous) {
        let prev_sibling = current_post_parent_r.previousSibling;
        if (!prev_sibling.classList.contains("post-parent")) {
            next_post_parent_r = prev_sibling;
        }
    } else {
        next_post_parent_r = current_post_parent_r.nextSibling;
    }
    if (!next_post_parent_r) {
        return null;
    }
    let next_post = next_post_parent_r.getElementsByClassName("post-parent")[0];
    return get_post_no_from_post(next_post);
}


function get_next_thread_no(post_no, previous) {
    let current_post = get_post_from_no(post_no);
    let current_thread = get_thread_from_post(current_post);
    let next_thread = null;
    if (previous) {
        next_thread = current_thread.previousSibling;
    } else {
        next_thread = current_thread.nextSibling;
    }
    if (!next_thread) {
        return null;
    }
    return get_post_no_from_thread(next_thread);
}


function add_to_history(post_no) {
    // avoid duplication
    let urlFragment = window.location.href.split("#")[1] || {};
    if (urlFragment === post_no) {
        return;
    }

    // update window hash with post id. This forces browser to scroll
    // to the element with that id so we do it before custom scrolling
    // window.location.hash = post_no.toString();
    history.pushState({}, "", "#" + post_no.toString());
}


function post_scroll_to(post_no) {
    // scroll into view of the post or thread
    let scroll_post = get_post_from_no(post_no);
    if (is_post_a_thread(scroll_post)) {
        // scroll to top of thread
        let scroll_thread = get_thread_from_post(scroll_post);
        scroll_thread.scrollIntoView({
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


function post_collapse(post_no) {
    let original_post = get_post_from_no(post_no);

    // depending on whether its the OP, collapse the thread or just the post
    if (is_post_a_thread(original_post)) {
        let original_thread = get_thread_from_post(original_post);
        original_thread.classList.add("collapsed-thread-parent");

    } else {
        original_post.classList.add("collapsed");
        original_post.parentElement.classList.add("collapsed-parent");
    }
}


function post_expand(post_no) {
    let original_post = get_post_from_no(post_no);

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
                (post.children[i].classList.contains("post-parent")) &&
                (post.children[i].classList.contains("collapsed"))
            ) {
                post.children[i].classList.remove("collapsed");
            }
        }
        if (post.classList.contains("collapsed-thread-parent")) {
            post.classList.remove("collapsed-thread-parent");
        }
        post = post.parentElement;
    }
}


function post_toggle_collapse(post_no) {
    let original_post = get_post_from_no(post_no);
    let return_value = -1;

    if (original_post.classList.contains("collapsed") || get_thread_from_post(original_post).classList.contains("collapsed-thread-parent")) {
        post_expand(post_no);
        return_value = 1;
    } else {
        post_collapse(post_no);
        return_value = 0;
    }
    return return_value;
}


function add_all_collapse_event_listeners() {
    let thread_collapsibles = document.getElementsByClassName("thread-collapsible-anchor");
    for (let i = 0; i < thread_collapsibles.length; i++) {
        thread_collapsibles[i].addEventListener("click", function() {
            let post_no = this.parentNode.parentNode.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_no);
            post_colorize_deterministic(post_no);
            add_to_history(post_no);
            post_scroll_to(post_no);
        });
    }

    let post_collapsibles = document.getElementsByClassName("post-collapsible-anchor");
    for (let i = 0; i < post_collapsibles.length; i++) {
        post_collapsibles[i].addEventListener("click", function() {
            let post_no = this.parentNode.parentNode.getElementsByClassName("post-no")[0].id;
            post_toggle_collapse(post_no);
        });
    }
}


function unix_timestamp_to_time_ago(unix_timestamp) {
    let curr_time = new Date();
    let post_time = new Date(unix_timestamp * 1000);
    let post_time_ago = (curr_time.getTime() - post_time.getTime()) / 1000;

    if (post_time_ago < 0) {
        return "Error! Negative time!";
    }

    let time_delta_days = Math.floor(post_time_ago / (60*60*24));
    let time_delta_hours = Math.floor(post_time_ago / (60*60)) % (24);
    let time_delta_minutes = Math.floor(post_time_ago / (60)) % (60);
    let time_delta_seconds = Math.floor(post_time_ago) % (60);

    return_time = "";
    if (time_delta_days == 0) {
        if (time_delta_hours == 0) {
            if (time_delta_minutes == 0) {
                return_time = time_delta_seconds.toString() + "s ago";
            } else {
                return_time = time_delta_minutes.toString() + "m ago";
            }
        } else {
            return_time = time_delta_hours.toString() + "h " + time_delta_minutes.toString() + "m ago";
        }
    } else {
        return_time = time_delta_days.toString() + "d " + time_delta_hours.toString() + "h ago";
    }
    return return_time;
}


function convert_all_elements_to_time_ago() {
    let all_elements = document.querySelectorAll(".board-time,.thread-time,.post-time");
    for (let i = 0; i < all_elements.length; i++) {
        let time_element_curr = all_elements[i];
        let time_element_time = time_element_curr.innerHTML;
        time_element_time = unix_timestamp_to_time_ago(time_element_time);
        time_element_curr.innerHTML = time_element_time;
    }
}


function generate_random_string(length, allowed_chars) {
    let return_value = "";
    for (let i = 0; i < length; i++) {
        let random_index = Math.floor(Math.random() * allowed_chars.length);
        return_value += allowed_chars[random_index];
    }
    return return_value;
}


function post_colorize_random(post_no) {
    let original_post = document.getElementById(post_no).parentElement.parentElement;
    let color_hex = "#" + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef") + generate_random_string(1, "12") + generate_random_string(1, "0123456789abcdef");
    original_post.style.background = color_hex;
}


function get_post_color_deterministic(post_no) {
    let random_choice1 = Math.abs(Math.sin(post_no)).toString(16).substring(2 + 1);
    let random_choice2 = Math.abs(Math.sin(post_no)).toString(2).substring(2 + 1);
    let random_choice_2_sub = "";
    for (let i = 0; i < random_choice2.length; i++) { if (random_choice2.charAt(i) == 0) { random_choice_2_sub += "2"; } else { random_choice_2_sub += "2"; }}
    let color_hex = "#" + random_choice_2_sub.slice(0,1) + random_choice1.slice(0,1) + random_choice_2_sub.slice(1,2) + random_choice1.slice(1,2) + random_choice_2_sub.slice(2,3) + random_choice1.slice(2,3);
    return color_hex;
}


function post_colorize_deterministic(post_no) {
    let original_post = document.getElementById(post_no).parentElement.parentElement;
    original_post.style.background = get_post_color_deterministic(post_no);
    original_post.style.border = "1px solid #fff";
    setTimeout(function() {
        original_post.style.border = "1px dashed #666";
    }, 500);
}


function element_colorize_deterministic(element, post_no) {
    element.style.background = get_post_color_deterministic(post_no);
    element.style.border = "1px solid #444";
}


function button_press_highlight(original_div) {
    original_div.style.background = "#577989";
    setTimeout(function() {
        original_div.style.background = null;
    }, 500);
}


function strip_post_no_start_chars(rid) {
    // get rid of certain starting substrings
    while (rid.startsWith("#")) { rid = rid.substring(1); }
    while (rid.startsWith("&gt;")) { rid = rid.substring(4); }
    return rid;
}


function keypress_parent() {
    let post_no = null;
    let post_parent_no = null;
    if(window.location.hash) {
        post_no = Number(window.location.hash.substring(1));
        post_parent_no = get_parent_post_no(post_no);
    }
    if (!post_parent_no) {
        if (!post_no) {
            return;
        }
        post_parent_no = post_no;
    }

    post_expand(post_parent_no);
    post_colorize_deterministic(post_parent_no);
    add_to_history(post_parent_no);
    post_scroll_to(post_parent_no);
}


function keypress_child() {
    let post_no = null;
    let post_child_no = null;
    if(window.location.hash) {
        post_no = Number(window.location.hash.substring(1));
        post_child_no = get_child_post_no(post_no);
    }
    if (!post_child_no) {
        if (!post_no) {
            return;
        }
        post_child_no = post_no;
    }

    post_expand(post_child_no);
    post_colorize_deterministic(post_child_no);
    add_to_history(post_child_no);
    post_scroll_to(post_child_no);
}


function keypress_next(previous) {
    let post_no = null;
    let next_post_no = null;
    if(window.location.hash) {
        post_no = Number(window.location.hash.substring(1));
        let post = get_post_from_no(post_no);
        if (is_post_a_thread(post)) {
            next_post_no = get_next_thread_no(post_no, previous);
        } else {
            next_post_no = get_next_post_no(post_no, previous);
        }
    } else {
        if (previous) {
            // pick the last thread in the page
            thread_parents = document.getElementsByClassName("thread-parent");
            if (thread_parents.length != 0) {
                next_post_no = get_post_no_from_thread(thread_parents[thread_parents.length - 1]);
            }
        } else {
            // pick the first thread in the page
            thread_parents = document.getElementsByClassName("thread-parent");
            if (thread_parents.length != 0) {
                next_post_no = get_post_no_from_thread(thread_parents[0]);
            }
        }
    }
    if (!next_post_no) {
        if (!post_no) {
            return;
        }
        next_post_no = post_no;
    }

    post_expand(next_post_no);
    post_colorize_deterministic(next_post_no);
    add_to_history(next_post_no);
    post_scroll_to(next_post_no);
}


function keypress_file_open() {
    let post_file = null;
    if(window.location.hash) {
        let post_no = Number(window.location.hash.substring(1));
        let post = get_post_from_no(post_no);
        post_file = get_file_from_post(post);
    }
    if (!post_file) {
        return;
    }
    // triggers browser popup block unfortunately
    window.open(post_file.href, "_blank", "noreferrer");
}


function keypress_toggle_collapse() {
    let post_no = null;
    if(window.location.hash) {
        post_no = Number(window.location.hash.substring(1));
    }
    if (!post_no) {
        return;
    }

    post_toggle_collapse(post_no);
    post_colorize_deterministic(post_no);
    post_scroll_to(post_no);
}


function keypress_go_forward() {
    history.forward();
}


function keypress_go_back() {
    let post_no = null;
    if(window.location.hash) {
        post_no = Number(window.location.hash.substring(1));
    }
    if (!post_no) {
        // don't go back if it takes you away from 4chv
        return;
    }
    history.back();
}


function event_reply_text(self) {
    let post_no = self.parentElement.parentElement.getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_no = self.innerHTML;
    reply_no = strip_post_no_start_chars(reply_no);

    // uncollapse, colorize and colorize, add to history and scroll
    post_expand(reply_no);
    element_colorize_deterministic(self, reply_no);
    post_colorize_deterministic(reply_no);
    add_to_history(post_no);
    // post_scroll_to(post_no);
    add_to_history(reply_no);
    post_scroll_to(reply_no);
}


function event_file_dump_a(self) {
    let post_no = self.parentElement.parentElement.parentElement.getElementsByClassName("post-parent-r")[0].getElementsByClassName("post-parent")[0].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_no = self.innerHTML;
    reply_no = strip_post_no_start_chars(reply_no);

    // uncollapse, colorize and colorize, add to history and scroll
    post_expand(reply_no);
    element_colorize_deterministic(self, reply_no);
    post_colorize_deterministic(reply_no);
    add_to_history(post_no);
    // post_scroll_to(post_no);
    add_to_history(reply_no);
    post_scroll_to(reply_no);
}


function event_post_a(self) {
    let post_no = self.parentElement.parentElement.parentElement.getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
    let reply_no = self.innerHTML;
    reply_no = strip_post_no_start_chars(reply_no);

    // uncollapse, colorize and colorize, add to history and scroll
    post_expand(reply_no);
    element_colorize_deterministic(self, reply_no);
    post_colorize_deterministic(reply_no);
    add_to_history(post_no);
    // post_scroll_to(post_no);
    add_to_history(reply_no);
    post_scroll_to(reply_no);
}


function event_post_no(self) {
    let post_no = self.id;
    post_no = strip_post_no_start_chars(post_no);

    // uncollapse, colorize and colorize, add to history and scroll
    post_expand(post_no);
    element_colorize_deterministic(self, post_no);
    post_colorize_deterministic(post_no);
    add_to_history(post_no);
    post_scroll_to(post_no);
}


function event_thread_maximize_replies(self) {
    let thread_element = self.parentNode.parentNode;
    let thread_post_parents = thread_element.querySelectorAll(".post-parent");

    for (let j = 0; j < thread_post_parents.length; j++) {
        let post_no = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
        post_expand(post_no);
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
    let thread_post_parents = thread_element.querySelectorAll(".post-parent");

    // first uncollapse the ones not originally collapsed
    for (let j = 0; j < thread_post_parents.length; j++) {
        let post_no = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;
        if (!thread_post_parents[j].classList.contains("collapsed-originally")) {
            post_expand(post_no);
        }
    }

    // then collapse the ones originally collapsed
    for (let j = 0; j < thread_post_parents.length; j++) {
        let post_no = thread_post_parents[j].getElementsByClassName("post-details")[0].getElementsByClassName("post-no")[0].id;

        if (thread_post_parents[j].classList.contains("collapsed-originally")) {
            post_collapse(post_no);
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
        let post_file = get_file_from_post(thread_post_parents[j]);
        let post_no = get_post_no_from_post(thread_post_parents[j]);
        if (post_file) {
            let a_curr = document.createElement("a");
            a_curr.innerHTML = post_file.innerHTML;
            a_curr.href = post_file.href;
            a_curr.rel = "noreferrer";
            a_curr.target = "_blank";

            let div_curr_child = document.createElement("div");
            div_curr_child.innerHTML = ">>" + post_no.toString();
            div_curr_child.classList.add("file-dump-a");
            // manipulating innerHTML destroys and recreates everything in div, removing event listeners
            div_curr_child.addEventListener("click", function() {
                event_file_dump_a(this);
            });

            let div_curr = document.createElement("div");
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
        let post_no = Number(window.location.hash.substring(1));
        post_expand(post_no);
        post_colorize_deterministic(post_no);
        setTimeout(function() {
            post_scroll_to(post_no);
            }, 500);  // for some reason it doesn't work well without a timeout
    }
}


window.addEventListener("popstate", function() {
    // make back button work perfectly, scroll to prev post regardless of expanding divs
    onpageload_popstate();
});

function keyboard_shortcuts(e) {
    // don't activate if other keys are pressed
    if (e.ctrlKey || e.altKey) {
        return;
    }

    if (e.key === "n") {
        keypress_next(false);

    } else if (e.key === "N") {
        keypress_next(true);

    } else if (e.key === "c") {
        keypress_child();

    } else if (e.key === "p") {
        keypress_parent();

    } else if (e.key === "i") {
        keypress_file_open();

    } else if (e.key === "t") {
        keypress_toggle_collapse();

    } else if (e.key === "f") {
        keypress_go_forward();

    } else if (e.key === "b") {
        keypress_go_back();

    }
    return;
}

function mobile_controls() {
    addEventListenerToClass("mobile-controls-button-next", function(original_div) { button_press_highlight(original_div); keypress_next(false); });
    addEventListenerToClass("mobile-controls-button-previous", function(original_div) { button_press_highlight(original_div); keypress_next(true); });
    addEventListenerToClass("mobile-controls-button-parent", function(original_div) { button_press_highlight(original_div); keypress_parent(); });
    addEventListenerToClass("mobile-controls-button-child", function(original_div) { button_press_highlight(original_div); keypress_child(); });
    addEventListenerToClass("mobile-controls-button-forward", function(original_div) { button_press_highlight(original_div); keypress_go_forward(); });
    addEventListenerToClass("mobile-controls-button-toggle-collapse", function(original_div) { button_press_highlight(original_div); keypress_toggle_collapse(); });
}

window.onload = function() {
    // convert unix timestamps to time ago
    convert_all_elements_to_time_ago();

    // add all the event listeners
    add_all_collapse_event_listeners();

    addEventListenerToClass("reply-text",       event_reply_text);
    addEventListenerToClass("post-a",           event_post_a);
    addEventListenerToClass("post-no",          event_post_no);
    addEventListenerToClass("thread-maximize-replies",  event_thread_maximize_replies);
    addEventListenerToClass("thread-reset",             event_thread_reset);
    addEventListenerToClass("thread-files-all",         event_thread_files_all);

    // add keypress listeners
    document.addEventListener("keydown", function(e) {
        keyboard_shortcuts(e);
    });

    // add mobile control listeners
    mobile_controls();

    // scroll to the #fragment
    onpageload_popstate();
}