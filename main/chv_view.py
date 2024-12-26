import sys
import pathlib
import re
import time
from datetime import datetime
import html
import sqlite3

# local imports
import chv_config
import chv_database

# filter post text post html escaping
def filter_post(content : str):
    clean_dict = {
        r'(\&gt;)+(\d{5,20})': r'<div class="reply-text">&gt;&gt;\2</div>',  # reply quotes
        r'^(\&gt;.+)': r'<div class="green-text">\1</div>',  # greentext
        r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@;:%_\+.~#?&\/=]*))': r'<a href="\1" rel="noreferrer" target="_blank">\1</a>',  # links
        r'\n': '<br>',  # line breaks
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


# given a list of sentences, returns a list of the same length of their 'complexity scores'
def complexity_score(sentences_array):
    # populate with global count of words
    words_count = dict()
    # populate with words from each sentence
    sentences_words = dict()

    # calculate words_count and sentences_words
    for sentence in sentences_array:
        words = [w.lower() for w in re.findall(r'(?:[^\d\W]|\')+', sentence)]
        sentences_words[sentence] = words
        for word in words:
            if word in words_count:
                words_count[word] += 1
            else:
                words_count[word] = 1

    # populate with complexity of each word
    words_complexity = dict()
    max_word_count = max(words_count.values())
    for word in words_count:
        words_complexity[word] = max_word_count / words_count[word]

    # populate with complexity of each sentence
    sentences_complexity = dict()
    # sentences_complexity - list()
    for sentence in sentences_array:
        sentence_words = sentences_words[sentence]
        sentence_word_count = len(sentence_words)
        sentence_complexity = 0

        # add up the complexity of each word in sentence
        for word in sentence_words:
            sentence_complexity += words_complexity[word]
        # normalize complexity of sentence by its word count powered to (1 - delta)
        if sentence_word_count not in [0, 1]:
            sentence_complexity /= sentence_word_count ** (1 - 2/3)

        sentences_complexity[sentence] = sentence_complexity
        # sentences_complexity.append([sentence, sentence_complexity])

    return sentences_complexity
    # return sorted(sentences_complexity, key=lambda x: -x[1])


# Calculate the cumulative complexity for a post,
# which depends on the complexities of its replies
def calculate_post_cumulative_complexity(board : dict, thread_no : int, post_no : int):
    post_parent_chain = set()
    return calculate_post_cumulative_complexity_r(board, thread_no, post_no, post_parent_chain)

def calculate_post_cumulative_complexity_r(board : dict, thread_no : int, post_no : int, post_parent_chain: set):
    post : dict = board[thread_no]['thread'][post_no]

    # sometimes two posts might reply to each other (sneaky) and cause an infinite function stack
    # this avoids that
    if post_no in post_parent_chain:
        cumulative_post_complexity = 0
        post['cumulative_complexity'] = 0
        post['cumulative_complexity_normalized'] = 0
        return cumulative_post_complexity

    post_parent_chain.add(post_no)

    # base case
    if 'cumulative_complexity' in post:
        return post['cumulative_complexity']

    # recursive case
    cumulative_post_complexity = 0
    norm = 1
    if len(post['succ']) > 0:
        for succ in post['succ']:
            if succ != post_no:
                cumulative_post_complexity += calculate_post_cumulative_complexity_r(board, thread_no, succ, post_parent_chain)
        norm = (len(post['succ'])) ** (1 - 1/3)
    cumulative_post_complexity += post['complexity']

    post_parent_chain.remove(post_no)

    post['cumulative_complexity'] = cumulative_post_complexity
    post['cumulative_complexity_normalized'] = cumulative_post_complexity / norm
    return cumulative_post_complexity


# Calculate the complexity and cumulative complexity for a board and
# append "complexity" and "cumulative_complexity" keys to all posts
def calculate_board_complexity(board : dict):
    all_posts = list()
    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            if 'com' in post:
                all_posts.append(post['com'])

    if len(all_posts) == 0:
        return

    all_posts_complexity_dict = complexity_score(all_posts)
    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            post['complexity'] = 0
            if post['com'] in all_posts_complexity_dict:
                post['complexity'] = all_posts_complexity_dict[post['com']]

    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            calculate_post_cumulative_complexity(board, thread_no, post_no)

    return


# sort a board's posts and threads by cumulative_complexity
def sort_board_cumulative_complexity(board : dict):
    threads_sorted = list()
    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            post['succ'] = sorted(post['succ'], key=lambda x: thread['thread'][x]['cumulative_complexity'], reverse=True)
        op_post_no = min(thread['thread'].keys())
        thread['cumulative_complexity_normalized'] = thread['thread'][op_post_no]['cumulative_complexity_normalized']
        threads_sorted.append(thread_no)

    # decay older threads by decreasing points by a ratio for every hour
    datetime_now = datetime.now().timestamp()
    decay_limit_hours = chv_config.decay_limit_hours
    decay_delta = chv_config.decay_delta
    decay_power = chv_config.decay_power
    for thread_no in board:
        if 'last_modified' not in board[thread_no]:
            board[thread_no]['last_modified'] = 0
        time_delta_hours = (datetime_now - board[thread_no]['last_modified']) // (60 * 60)
        board[thread_no]['cumulative_complexity_normalized_timed'] = board[thread_no]['cumulative_complexity_normalized'] * (decay_delta + max(0, decay_limit_hours - time_delta_hours) / decay_limit_hours) ** decay_power
    threads_sorted = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity_normalized_timed'], reverse=True)
    # threads_sorted2 = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity_normalized'], reverse=True)

    return threads_sorted


# create a list of posts in the order they should be printed
def create_post_list_r(board : dict, thread_no : int, post_no : int, tabbing: int, post_list: list, posts_list_set: set):
    if post_no not in board[thread_no]['thread']:
        # post might have been deleted
        return -2

    post = board[thread_no]['thread'][post_no]

    # track occurrences
    if 'occurrences' not in post:
        post['occurrences'] = 1
    else:
        post['occurrences'] += 1

    if (post['occurrences'] > chv_config.post_occurrences_max):
        return -1

    # logic for whether a post is toggled open or close by default
    # OP (which has tabbing == 0) is always visible
    post_complexity_int = int((post['complexity'] / 100) ** 0.8)
    toggle_min = chv_config.toggle_min
    toggle_factor = chv_config.toggle_factor
    if (post_complexity_int <= toggle_min + toggle_factor * tabbing) and (tabbing > 0):
        post['hidden'] = True

    post_list.append({'post': post, 'tabbing': tabbing})
    if 'no' in post:
        posts_list_set.add(post['no'])

    # recursively call succs
    if 'succ_display' not in post:
        post['succ_display'] = list()
    for succ in post['succ']:
        # only display succ that have been processed already
        if succ in posts_list_set:
            post['succ_display'].append(succ)

        succ_return = create_post_list_r(board, thread_no, succ, tabbing + 1, post_list, posts_list_set)

        # commented out since we are doing the thing above instead
        # don't display succ that are direct descendants
        # if succ_return != 0:
        #     post['succ_display'].append(succ)

    return 0


# print a single post
def print_post(board_name: list, post: dict):
    complexity_int = int((post['complexity'] / 100) ** 0.8)
    # cumulative_complexity_int = int((post['cumulative_complexity'] / 100) ** 0.8)
    # cumulative_complexity_diff_int = int(((post['cumulative_complexity'] - post['complexity']) / 100) ** 0.3)
    # complexity_hashes_int = int((post['complexity'] / 100) ** 0.7)
    complexity_hashes_int = int((max(0, (post['cumulative_complexity_normalized'] - post['complexity'])) / 100) ** 0.3)

    score = ''
    if complexity_int != 1:
        score = f'{complexity_int} points'
    else:
        score = f'{complexity_int} point'

    post_time = post['time']

    post_name_html = ''
    if 'name' in post:
        post_name = html.escape(post['name'])
        post_name_html = f'<div title="Poster\'s name" class="post-name">{post_name}</div>'

    post_id_html = ''
    if 'id' in post:
        post_id = post['id']
        post_id_html = f'<div title="Poster\'s id" class="post-id">{post_id}</div>'

    post_country_name_html = ''
    if 'country_name' in post:
        post_country_name = post['country_name']
        post_country_name_html = f'<div title="Poster\'s country" class="post-country-name">{post_country_name}</div>'

    post_file_html = ''
    post_has_file_html = ''
    if 'file' in post:
        post_file = post['file']
        post_filename = post['filename']
        post_ext = post['ext']

        thumbnail_html = '<img loading="lazy" src="./resources/images/thumbnail_not_found.png"></img>'
        thumbnail_file = pathlib.Path(f'html/thumbs/{board_name[0]}/{post["no"]}.jpg')
        if thumbnail_file.is_file():
            thumbnail_html = f'<img loading="lazy" src="thumbs/{board_name[0]}/{post["no"]}.jpg"></img>'

        post_file_html = f'<div title="Post attachment" class="post-file"><a href="{post_file}" rel="noreferrer" target="_blank">{thumbnail_html}</a></div>'
        post_has_file_html = f'<div title="Post has file" class="post-has-file">{post_ext}</div>'

    post_com = ''
    if 'com' in post and len(post['com']) > 0:
        post_com = post['com']
        post_com = html.escape(post_com)
        post_com = filter_post(post_com)

    post_succ_html = ''
    if 'succ_display' in post and len(post['succ_display']) > 0:
        post_succ_html = 'Other replies: '
        for succ in post['succ_display']:
            post_succ_html += f'<div class="post-a">&gt;&gt;{succ}</div>'

    return f'''
    <div class="post-parent {'collapsed collapsed-originally' if ('hidden' in post) else ''}">
        <div class="post-details">
            <div title="Toggle expand" class="post-collapsible-anchor">[+]</div>
            {post_has_file_html}
            <div title="Post points" class="post-complexity-number">{score}</div>
            <div title="Reply points" class="post-complexity">{"+" * complexity_hashes_int}</div>
            <div title="Post number" class="post-no" class="post-a" id="{post["no"]}">#{post["no"]}</div>
        </div>
        {post_file_html}
        <div class="post">{post_com}</div>
        <div class="post-details-2">
            {post_name_html}
            {post_id_html}
            {post_country_name_html}
            <div title="Post time" class="post-time">{post_time}</div>
            <div title="Post replies not directly below post" class="post-succ">{post_succ_html}</div>
        </div>
    </div>
    '''


# print an entire board
def print_board(board: dict, threads_sorted : list, board_names: list, board_index: int):
    datetime_now = datetime.now().timestamp()
    version_number = chv_config.version_number
    board_name = board_names[board_index]

    # get latest post time
    latest_post_time = 0  # if latest post is before 1970, then I'm Santa Claus and this code deserves to break
    for thread_no in threads_sorted:
        thread = board[thread_no]
        if 'last_modified' in thread:
            if thread['last_modified'] > latest_post_time:
                latest_post_time = thread['last_modified']

    # add greeter links to all boards
    board_links_html = '[]'
    if len(board_names) != 0:
        board_links_html = '[ ' + ' / '.join([f'<a href="{b[0]}.html" title="{b[1]}" class="greeter-element">{b[0]}</a>' for b in board_names]) + ' ]'

    # get stylesheet filename
    all_stylesheets = chv_config.all_stylesheets
    selected_style = chv_config.selected_style
    selected_stylesheet = chv_config.selected_stylesheet

    # create style-selector dropbox
    style_selector_html = '<select autocomplete="off" id="style-selector" class="style-selector" onchange="set_style();">'
    for style in all_stylesheets:
        style_selector_html += f'<option value="{all_stylesheets[style]}"'
        if style == selected_style:
            style_selector_html += f' selected="selected"'
        style_selector_html += f'>{style}</option>'
    style_selector_html += '</select>'

    # the main string list
    html_string = list()
    html_string.append(f'''
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="robots" content="noindex">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:locale" content="en_US">
            <meta property="og:type" content="website">
            <link rel='stylesheet' id="stylesheet" type='text/css' href='resources/stylesheets/{selected_stylesheet}?v={version_number}'>
            <script src='resources/js/script.js?v={version_number}' defer></script>
            <link rel="icon" type="image/x-icon" href="resources/images/favicon.png?v={version_number}">
            <title>/{board_name[0]}/ - 4CHV</title>
        </head>
        <body>
            <div class="wrapper">
                <div class="greeter-links">
                    {board_links_html}
                </div>
                <hr>
                <div class="greeter-logo">
                    <img title="4CHV logo" loading="lazy" src="./resources/images/logo.png"></img>
                </div>
                <h1 class="page-title">
                    <a title="Board title" href="">/{board_name[0]}/ - {board_name[1]}</a>
                </h1>
                <div class="greeter-subtitle">
                Board updated <div title="Time since board was last built" class="board-time">{int(datetime_now)}</div>,
                Latest post <div title="Time since most recent post" class="board-time">{int(latest_post_time)}</div>
                </div>
                <div class="greeter-info">
                    <hr>
                    <div class="greeter-usage-parent">
                        <b>Basic usage</b>
                        <ul class="greeter-usage-list">
                            <li><a>[+]</a> to expand posts</li>
                            <li><a>&gt;&gt;1234567</a> to jump to posts</li>
                            <li>Archived threads marked yellow</li>
                        </ul>
                    </div>
                    <div class="greeter-style-selector-parent">
                        <b>Options</b>
                        <ul class="greeter-options-list">
                            <li>
                                <label class="input-label" for="style-selector">Style: </label>
                                {style_selector_html}
                            </li>
                            <li>
                                <label class="input-label" for="whitelist-words">Whitelist: </label>
                                <input class="input-blacklist-whitelist" id="whitelist-words"></input>
                            </li>
                            <li>
                                <label class="input-label" for="blacklist-words">Blacklist: </label>
                                <input class="input-blacklist-whitelist" id="blacklist-words"></input>
                            </li>
                        </ul>
                    </div>
                    <div class="greeter-shortcut-parent">
                        <b>Keyboard shortcuts</b>
                        <table class="greeter-shortcut-table">
                            <thead>
                                <tr>
                                    <td>Navigate across posts</td>
                                    <td>Interact with post</td>
                                    <td>Browser history</td>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>n</code> = next</td>
                                    <td><code>t</code> = toggle expand post</td>
                                    <td><code>b</code> = go back</td>
                                </tr>
                                <tr>
                                    <td><code>N</code> = previous</td>
                                    <td><code>i</code> = open post file</td>
                                    <td><code>f</code> = go forward</td>
                                </tr>
                                <tr>
                                    <td><code>p</code> = parent</td>
                                    <td></td>
                                    <td></td>
                                </tr>
                                <tr>
                                    <td><code>c</code> = child</td>
                                    <td></td>
                                    <td></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <hr>
                <div class="all-threads">
    ''')

    for thread_no in threads_sorted:
        thread = board[thread_no]

        thread_replies = None
        if 'replies' in thread:
            thread_replies = thread['replies']
        else:
            thread_replies = len(thread['thread']) - 1

        thread_images_html = ''
        if 'images' in thread:
            thread_images = thread['images']
            thread_images_html = f' / <div title="Thread image count" class="thread-images">I: <b>{thread_images}</b></div>'

        thread_thumbnail_html = '''
        <a>
            <img loading="lazy" src="./resources/images/thumbnail_not_found.png"></img>
        </a>
        '''
        if 'thread' in thread:
            op_post = thread['thread'][min(thread['thread'])]

            if 'file' in op_post:
                thread_thumbnail_url = op_post['file']

                thumbnail_file = pathlib.Path(f'html/thumbs/{board_name[0]}/{op_post["no"]}.jpg')
                if thumbnail_file.is_file():
                    thread_thumbnail_html = f'''
                    <a href="{thread_thumbnail_url}" rel="noreferrer" target="_blank">
                        <img loading="lazy" src="thumbs/{board_name[0]}/{op_post["no"]}.jpg"></img>
                    </a>
                    '''
                elif 'thumbnail' in thread:
                    # handle legacy method where thumbnail used to be stored in db
                    thread_thumbnail = thread['thumbnail'].decode()
                    thread_thumbnail_html = f'''
                        <a href="{thread_thumbnail_url}" rel="noreferrer" target="_blank">
                            <img loading="lazy" src="data:image/png;base64, {thread_thumbnail}"></img>
                        </a>
                    '''

        thread_sub = ''
        if 'sub' in thread:
            thread_sub = thread['sub']
            thread_sub = html.escape(thread_sub)
            # thread_sub = filter_post_post(thread_sub)

            if thread_sub != '':
                thread_sub += ': '

        thread_com = ''
        if 'com' in thread:
            thread_com = thread['com']
            thread_com = html.escape(thread_com)
            thread_com = filter_post(thread_com)

        thread_time = ''
        if 'last_modified' in thread:
            thread_time = thread['last_modified']

        thread_extra_classes = ''
        if 'is_archived' in thread:
            thread_extra_classes += ' thread-is-archived'
        if 'is_404d' in thread:
            thread_extra_classes += ' thread-is-404d'

        # append the thread header to the main string list
        html_string.append(f'''
        <div class="thread-parent collapsed-thread-parent {thread_extra_classes}">
            <div class="thread-details">
                <div title="Toggle expand" class="thread-collapsible-anchor">[+]</div>
                <div title="See thread on 4chan.org" class="thread-op">
                    <a href="https://boards.4chan.org/{board_name[0]}/thread/{thread_no}" rel="noreferrer" target="_blank">
                        ~
                    </a>
                </div>
            </div>
            <div class="thread-options">
                <div class="thread-maximize-replies">Expand all posts</div>
                <div class="thread-files-all">List all files</div>
                <div class="thread-reset">Reset thread</div>
            </div>
            <div title="Thread attachment" class="thread-thumbnail">
                {thread_thumbnail_html}
            </div>
            <div class="thread-details-2">
                <div title="Time since last reply" class="thread-time">{thread_time}</div>
                <div class="thread-replies-parent">
                    <div title="Thread reply count" class="thread-replies">R: <b>{thread_replies}</b></div>
                    {thread_images_html}
                </div>
            </div>
            <div class="thread-sub-description">
                <div title="Thread subject" class="thread-sub">{thread_sub}</div>
                <div class="thread-description">{thread_com}</div>
            </div>
            <div class="thread-files-dump"></div>
        ''')

        # create a sorted and nested post list for the thread
        post_list = list()
        post_list_set = set()
        if 'thread' in thread:
            posts = thread['thread']
            for post_no in posts:
                create_post_list_r(board, thread_no, post_no, 0, post_list, post_list_set)

        # go through the created post list and start building the html
        posts_string = list()
        curr_tabbing = 0
        for post_element in post_list:
            post = post_element["post"]
            tabbing = post_element["tabbing"]

            posts_string.append(f'''
            {'</div>' * max(curr_tabbing - tabbing + 1, 0)}
            <div class="post-parent-r {'collapsed-parent collapsed-parent-originally' if ('hidden' in post) else ''}">
                {print_post(board_name, post)}
            ''')

            curr_tabbing = tabbing

        # append the posts html to the main string list
        html_string.append(f'''
            <div>
                {''.join(posts_string)}
            {'</div>' * curr_tabbing}
            </div>
        </div>
        ''')

    html_string.append('''
                </div>
                <div class="mobile-controls">
                    <div class="mobile-controls-button mobile-controls-button-next">Next</div>
                    <div class="mobile-controls-button mobile-controls-button-child">Child</div>
                    <div class="mobile-controls-button mobile-controls-button-toggle-collapse">Toggle</div>
                    <div class="mobile-controls-button mobile-controls-button-previous">Previous</div>
                    <div class="mobile-controls-button mobile-controls-button-parent">Parent</div>
                    <div class="mobile-controls-button mobile-controls-button-forward">Forward</div>
                </div>
                <hr>
                <div class="greeter-footer">
                    <ul class="greeter-footer-list">
                        <li><a href="#">Go to top</a></li>
                        <li><a href="https://github.com/Infinitifall/4chv" target="_blank" rel=“noreferrer”>4CHV</a> is free and open source software!</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    ''')

    return_string = ''.join(html_string)

    # trim whitespaces and newlines between html tags
    return_string = re.sub(r'>[\n ]+<', r'><' , return_string)

    return return_string


# wrapper function to make html page for a board
def make_html(board_names: list, board_index: int, thread_count: int):
    datetime_now = datetime.now().timestamp()
    board_name = board_names[board_index]

    # check if db file exists
    if not pathlib.Path(f'threads/{board_name[0]}.sqlite').is_file():
        print(f'skipping html/{board_name[0]}.html, no database yet', flush=True)
        return

    # connect to board db
    db_connection = sqlite3.connect(f'threads/{board_name[0]}.sqlite')

    # initialize board db in case it doesn't exist or is on an older version
    chv_database.startup_boards_db(db_connection)

    # Strategy to filter out high traffic low quality threads:
    # 1. Choose the newest created (thread_count // 10) thread files
    # 2. Choose the most replied to (thread_count // 40) thread files in the past 24 hours
    # 3. Choose the last modified (thread_count * 1) thread files with at least 10 replies ordered by replies
    # 4. Choose the last modified (thread_count * 1) thread files
    # 5. Combine the above lists in that order, limiting elements to (thread_count * 1)
    all_thread_groups = list()
    all_thread_groups.append(chv_database.get_thread_nos_by_created(db_connection, thread_count // 10))
    all_thread_groups.append(chv_database.get_thread_nos_custom_2(db_connection, datetime_now - 24 * 60 * 60, thread_count // 40))
    all_thread_groups.append(chv_database.get_thread_nos_custom_1(db_connection, 10, thread_count))
    all_thread_groups.append(chv_database.get_thread_nos_custom_1(db_connection, 0, thread_count))

    all_threads = set()
    for thread_group in all_thread_groups:
        for thread_no in thread_group:
            if len(all_threads) < thread_count:
                all_threads.add(thread_no)

    all_threads = list(all_threads)
    my_board = chv_database.get_threads(db_connection, all_threads)

    # skip if board has no threads
    if len(my_board) == 0:
        print(f'skipping html/{board_name[0]}.html, no threads to be made yet', flush=True)
        return

    print(f'making html/{board_name[0]}.html with {len(my_board)} threads', flush=True)
    calculate_board_complexity(my_board)  # calculate complexity for board (medium)
    threads_sorted = sort_board_cumulative_complexity(my_board)  # sort threads by cumulative complexity (fast)
    html_string = print_board(my_board, threads_sorted, board_names, board_index)  # print the entire board to html (slow)

    # write board html to file (fast)
    with open(f'html/{board_name[0]}.html', 'w') as f:
        f.write(html_string)
        print(f'built html/{board_name[0]}.html', flush=True)
    return


def make_index(board_names: list):
    datetime_now = datetime.now().timestamp()
    version_number = chv_config.version_number

    # add greeter links to index
    board_links_html = '[]'
    if len(board_names) != 0:
        board_links_html = '[ ' + ' / '.join([f'<a href="{b[0]}.html" title="{b[1]}" class="greeter-element">{b[0]}</a>' for b in board_names]) + ' ]'

    # get stylesheet filename
    all_stylesheets = chv_config.all_stylesheets
    selected_style = chv_config.selected_style
    selected_stylesheet = chv_config.selected_stylesheet

    # create style-selector dropbox
    style_selector_html = '<select autocomplete="off" id="style-selector" onchange="set_style();">'
    for style in all_stylesheets:
        style_selector_html += f'<option value="{all_stylesheets[style]}"'
        if style == selected_style:
            style_selector_html += f' selected="selected"'
        style_selector_html += f'>{style}</option>'
    style_selector_html += '</select>'

    all_boards_html = '<ul class="all-boards-list">'
    for board_name in board_names:
        all_boards_html += f'<li><a href="{board_name[0]}.html">{board_name[0]} - {board_name[1]}</a></li>'
    all_boards_html += '</ul>'

    index_file = f'''
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="robots" content="noindex">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:locale" content="en_US">
            <meta property="og:type" content="website">
            <link rel='stylesheet' id="stylesheet" type='text/css' href='resources/stylesheets/{selected_stylesheet}?v={version_number}'>
            <script src='resources/js/script.js?v={version_number}' defer></script>
            <link rel="icon" type="image/x-icon" href="resources/images/favicon.png?v={version_number}">
            <title>Index - 4CHV</title>
        </head>
        <body>
            <div class="wrapper">
                <div class="greeter-links">
                    {board_links_html}
                </div>
                <hr>
                <div class="greeter-logo">
                    <img title="4CHV logo" loading="lazy" src="./resources/images/logo.png"></img>
                </div>
                <h1 class="page-title">
                    <a title="Page title" href="">Index</a>
                </h1>
                <div class="greeter-subtitle">
                Index updated <div title="Time since index was last built" class="board-time">{int(datetime_now)}</div>
                </div>
                <div class="greeter-info">
                    <hr>
                    <div class="greeter-style-selector-parent">
                        <b>Options</b>
                        <label for="style-selector">Style: </label>
                        {style_selector_html}
                    </div>
                </div>
                <hr>
                <div class="all-boards">
                    {all_boards_html}
                </div>
                <hr>
                <div class="greeter-footer">
                    <ul class="greeter-footer-list">
                        <li><a href="https://github.com/Infinitifall/4chv" target="_blank" rel=“noreferrer”>4CHV</a> is free and open source software!</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    '''

    # write index html to file (fast)
    with open(f'html/index.html', 'w') as f:
        f.write(index_file)
        print(f'built html/index.html', flush=True)
    return


def make_html_wrapper(wait_time: float, thread_count: int):
    first_time = True
    while True:
        try:
            # get list of board names
            board_names = chv_config.boards_active
            # avoid busy wait if no active boards
            if len(board_names) == 0:
                print(f'no active boards! Uncomment lines in main/chv_config.py!', flush=True)
                time.sleep(10)
                continue
            print(f'making: {", ".join([b[0] for b in board_names])}', flush=True)

            # delete old html files
            if (first_time):
                for filename in pathlib.Path("html/").glob("*.html"):
                    filename.unlink()
                print(f'deleted any old html files', flush=True)
            first_time = False

            # make index.html
            try:
                make_index(board_names)
            except Exception as e:
                print(f'failed to make html/index.html', flush=True)
                print(e, flush=True)
                time.sleep(10)

            # make all boards
            for board_index, board_name in enumerate(board_names):
                try:
                    make_html(board_names, board_index, thread_count)
                    time.sleep(chv_config.view_wait_time_internal)
                except Exception as e:
                    print(f'failed to make html/{board_name[0]}.html', flush=True)
                    print(e, flush=True)
                    time.sleep(10)

            time.sleep(wait_time)

        except Exception as e:
            print('an error occurred!', flush=True)
            print(e, flush=True)
            time.sleep(10)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 3)
        wait_time = int(sys.argv[1])
        thread_count = int(sys.argv[2])
        make_html_wrapper(wait_time, thread_count)

    except Exception as e:
        print('Usage: python3 view.py <wait_time> <max_latest_posts>', flush=True)
