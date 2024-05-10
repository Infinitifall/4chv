all_stylesheets = {
    "default": "style.css",
    # Add custom stylesheet filenames below. Custom stylesheets go in html/resources/stylesheets/
}
selected_stylesheet = all_stylesheets["default"]


# average time in seconds in-between downloading threads
download_wait_time = 2

# average time in seconds in-between rebuilding all board html pages
view_wait_time = 400

# maximum number of threads shown in a board's html page
view_max_threads_per_board = 300

# maximum number of threads stored in a database per board
# we want this to be large since most threads are low quality, especially during high traffic
db_max_threads_per_board = 5000



if __name__ == '__main__':
    pass