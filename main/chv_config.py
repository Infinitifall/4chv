##############################
# config for active boards
##############################

boards_active = [
#   ["3",       '3DCG'],
#   ["a",      'Anime & Manga'],
#   ["adv",    'Advice'],
#   ["an",     'Animals & Nature'],
#   ["b",      'Random'],
#   ["bant",   'International/Random'],
#   ["biz",    'Business & Finance'],
#   ["c",      'Anime/Cute'],
#   ["cgl",    'Cosplay & EGL'],
#   ["ck",     'Food & Cooking'],
#   ["cm",     'Cute/Male'],
#   ["co",     'Comics & Cartoons'],
#   ["diy",    'Do-It-Yourself'],
#   ["fa",     'Fashion'],
#   ["fit",    'Fitness'],
   ["g",      'Technology'],
#   ["gd",     'Graphic Design'],
#   ["i",      'Oekaki'],
#   ["ic",     'Artwork/Critique'],
   ["his",    'History & Humanities'],
#   ["int",    'International'],
#   ["jp",     'Otaku Culture'],
#   ["k",      'Weapons'],
   ["lit",    'Literature'],
#   ["lgbt",   'LGBT'],
#   ["m",      'Mecha'],
#   ["mlp",    'Pony'],
   ["mu",     'Music'],
#   ["news",   'Current News'],
#   ["n",      'Transportation'],
#   ["o",      'Auto'],
#   ["out",    'Outdoors'],
#   ["p",      'Photography'],
#   ["po",     'Papercraft & Origami'],
#   ["pol",    'Politically Incorrect'],
#   ["pw",     'Professional Wrestling'],
#   ["qst",    'Quests'],
#   ["r9k",    'ROBOT9001'],
#   ["s4s",    'Shit 4chan Says'],
   ["sci",    'Science & Math'],
#   ["soc",    'Cams & Meetups'],
#   ["sp",     'Sports'],
#   ["tg",     'Traditional Games'],
#   ["toy",    'Toys'],
#   ["trash"   'Off-topic'],
#   ["trv",    'Travel'],
   ["tv",     'Television & Film'],
#   ["v",      'Video Games'],
#   ["vg",     'Video Game Generals'],
#   ["vm",     'Video Games/Multiplayer'],
#   ["vmg",    'Video Games/Mobile'],
#   ["vip",    'Very Important Posts'],
#   ["vp",     'Pokémon'],
#   ["vr",     'Retro Games'],
#   ["vrpg",   'Video Games/RPG'],
#   ["vst",    'Video Games/Strategy'],
#   ["vt",     'Virtual YouTubers'],
#   ["w",      'Anime/Wallpapers'],
#   ["wg",     'Wallpapers/General'],
#   ["wsg",    'Worksafe GIF'],
#   ["wsr",    'Worksafe Requests'],
   ["x",      'Paranormal'],
#   ["xs",      'Extreme Sports']
]


##############################
# config for css
##############################

all_stylesheets = {
    "dark": "dark.css",
    "light": "light.css",
    "forest": "forest.css",
    "candy": "candy.css"

    # custom stylesheets can be put in html/resources/stylesheets/ and added here
}
selected_style = "dark"  # default style
selected_stylesheet = all_stylesheets[selected_style]


##############################
# config for download
##############################

# average time in seconds in-between downloading threads
# default: 2
download_wait_time = 2

# view_wait_time_internal is time in seconds to wait in-between building board html pages
# view_wait_time is average time in seconds in-between building all board html pages
# default: 5, 400
view_wait_time_internal = 5
view_wait_time = 400

# maximum number of threads shown in a board's html page
# default: 300
view_max_threads_per_board = 300


# minimum number of replies to a thread before it is downloaded
# unfortunately we need this to prevent being completely washed over by low quality spam
# default: 5
minimum_replies_before_download = 5

# maximum number of threads stored in a database per board
# we want this to be large since most threads are low quality, especially during high traffic
# default: 1000
db_max_threads_per_board = 1000


##############################
# config for view
##############################

# maximum number of times a post is shown
# a value of 1 means no repeats
# default: 1
post_occurrences_max = 1

# factors that affect whether a post is toggled open or close by default
# post_nesting is how deep in the replies a post is nested
# open if post_points > (toggle_min + toggle_factor * post_nesting)
# default: 10, 2
toggle_min = 10
toggle_factor = 2

# factors that affect how threads are penalized for being old
# time_delta_hours is the time delta since a thread was created
# thread_points_timed = thread_points * (decay_delta + max(0, decay_limit_hours - time_delta_hours) / decay_limit_hours) ** decay_power
# points are no longer deducted after (decay_limit_hours) hours
# default: 24 * 4, 0.15, 2
decay_limit_hours = 24 * 4
decay_delta = 0.15
decay_power = 2


##############################
# config for dev
##############################

# update version when you update css, js, images to bypass browser cache
# you dont need to touch this unless you are a 4chv dev
# default: 60
version_number = "61"

# start message printed in console
pretty_ugly_start_message = f'''
--------------------------------------------------
                       4CHV

                   version: {version_number}

        A viewer for a more civilized age        

--------------------------------------------------
Leave this running in the background whenever and
however long you like.

While running, it will
1. Download new threads every few seconds
2. Update board html files every few minutes

Open the board html files in your web browser :)

--------------------------------------------------
'''


if __name__ == '__main__':
    pass
