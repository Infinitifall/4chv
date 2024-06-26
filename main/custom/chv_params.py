all_stylesheets = {
    "dark": "dark.css",
    "light": "light.css",
    "forest": "forest.css",
    "candy": "candy.css"

    # custom stylesheets can be put in html/resources/stylesheets/ and added here
}
selected_style = "dark"  # default style
selected_stylesheet = all_stylesheets[selected_style]


# average time in seconds in-between downloading threads
download_wait_time = 2

# average time in seconds in-between rebuilding all board html pages
view_wait_time = 400

# maximum number of threads shown in a board's html page
view_max_threads_per_board = 300

# maximum number of threads stored in a database per board
# we want this to be large since most threads are low quality, especially during high traffic
db_max_threads_per_board = 5000

# update version when you update css, js, images to bypass browser cache
# you dont need to touch this unless you are a 4chv dev
version_number = "60"


if __name__ == '__main__':
    pass
