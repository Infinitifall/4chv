all_stylesheets = {
    "dark": "dark.css",
    "light": "light.css"

    # custom stylesheets can be put in html/resources/stylesheets/ and added here
}
selected_stylesheet = all_stylesheets["dark"]


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