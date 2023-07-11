var posts = document.getElementsByClassName("post-collapsible-anchor");
for (let i = 0; i < posts.length; i++) {
  posts[i].addEventListener("click", function() {
    this.parentNode.parentNode.classList.toggle("collapsed");
    this.parentNode.parentNode.parentNode.classList.toggle("collapsed-parent");
  });
}

var posts = document.getElementsByClassName("thread-collapsible-anchor");
for (let i = 0; i < posts.length; i++) {
  posts[i].addEventListener("click", function() {
    this.parentNode.classList.toggle("collapsed-thread");
    this.parentNode.parentNode.classList.toggle("collapsed-thread-parent");
  });
}
