import sys
import pathlib
import re
import time
from datetime import datetime
import html
import sqlite3

# local imports
import chv_boards
import chv_database


# filter post text pre html escaping
def filter_post_pre(content : str):
    clean_dict = {
        r'[^!@#\$%\^&*\(\)-_=\+\[\]\{\};:\'",<.>\/\?\|\\\s\w]': '_',  # weird unicode
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


# filter post text post html escaping
def filter_post_post(content : str):
    clean_dict = {
        r'(\&gt;)+(\d{5,20})': r'<div class="reply-text">&gt;&gt;\2</div>',  # reply quotes
        r'^(\&gt;.+)': r'<div class="green-text">\1</div>',  # greentext
        r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@;:%_\+.~#?&\/=]*))': r'<a href="\1" rel="noreferrer" target="_blank">\1</a>',  # links
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
        words = [w.lower() for w in re.findall(r'[\w\']+', sentence)]
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
    post : dict = board[thread_no]['thread'][post_no]

    # base case
    if 'cumulative_complexity' in post:
        return post['cumulative_complexity']

    # recursive case
    cumulative_post_complexity = 0
    norm = 1
    if len(post['succ']) > 0:
        for succ in post['succ']:
            if succ != post_no:
                cumulative_post_complexity += calculate_post_cumulative_complexity(board, thread_no, succ)
        norm = (len(post['succ'])) ** (1 - 1/3)
    cumulative_post_complexity += post['complexity']

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
    decay_limit_hours = 24 * 4  # no more decrease after this
    for thread_no in board:
        if 'last_modified' not in board[thread_no]:
            board[thread_no]['last_modified'] = 0
        time_delta_hours = (datetime_now - board[thread_no]['last_modified']) // (60 * 60)
        board[thread_no]['cumulative_complexity_normalized_timed'] = board[thread_no]['cumulative_complexity_normalized'] * (0.15 + max(0, decay_limit_hours - time_delta_hours) / decay_limit_hours) ** 2
    threads_sorted = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity_normalized_timed'], reverse=True)
    # threads_sorted2 = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity_normalized'], reverse=True)

    return threads_sorted


# create a list of posts in the order they should be printed
def create_post_list_r(board : dict, thread_id : int, post_id : int, tabbing: int, post_list: list):
    if post_id not in board[thread_id]['thread']:
        # post might have been deleted
        return

    post = board[thread_id]['thread'][post_id]

    # logic for how many occurrences are allowed
    if 'occurrences' not in post:
        post['occurrences'] = 1
    else:
        post['occurrences'] += 1
    occurrences_max = 1
    if (post['occurrences'] > 1 and tabbing <= 1) or \
        (post['occurrences'] > occurrences_max):
        return

    # logic for hiding a post by default
    post_complexity_int = int((post['complexity'] / 100) ** 0.8)
    if (post_complexity_int <= 10 + 2 * tabbing) and (tabbing > 0):
        post['hidden'] = True

    post_list.append({"post": post, "tabbing": tabbing})

    # recursively call succs
    for succ in post['succ']:
        create_post_list_r(board, thread_id, succ, tabbing + 1, post_list)

    return post_list


# print a single post
def print_post(post: dict):
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

    post_name = ''
    if 'name' in post:
        post_name = html.escape(post['name'])
        post_name = f'<div title="Poster\'s name" class="post-name">{post_name}</div>'

    post_id = ''
    if 'id' in post:
        post_id = post['id']
        post_id = f'<div title="Poster\'s id" class="post-id">{post_id}</div>'

    post_country_name = ''
    if 'country_name' in post:
        post_country_name = post['country_name']
        post_country_name = f'<div title="Poster\'s country" class="post-country-name">{post_country_name}</div>'

    post_file = ''
    if 'file' in post:
        post_file = post['file']
        post_filename = post['filename']
        post_ext = post['ext']
        post_file = f'<div title="Post attachment" class="post-file"><a href="{post_file}" rel="noreferrer" target="_blank">{post_filename}{post_ext}</a></div>'

    post_com = ''
    if 'com' in post and len(post['com']) > 0:
        post_com = post['com']
        # post_com = filter_post_pre(post['com'])
        post_com = html.escape(post_com)
        post_com = filter_post_post(post_com)

    post_succ = ''
    if 'succ' in post and len(post['succ']) > 0:
        for succ in post['succ']:
            post_succ += f'<div class="post-a">&gt;&gt;{succ}</div>  '  # whitespace after is important

    return f'''
    <div class="post-parent {'collapsed collapsed-originally' if ('hidden' in post) else ''}">
        <div class="post-details">
            <div title="Toggle folding" class="post-collapsible-anchor">[+]</div>
            <div title="Post points" class="post-complexity-number">{score}</div>
            <div title="Reply points" class="post-complexity">{"+" * complexity_hashes_int}</div>
            <div title="Post number" class="post-no" class="post-a" id="{post["no"]}">#{post["no"]}</div>
        </div>
        {post_file}
        <div class="post">{post_com}</div>
        <div class="post-details-2">
            {post_name}
            {post_id}
            {post_country_name}
            <div title="Unix time: {post_time}" class="post-time">{post_time}</div>
            <div class="post-succ">{post_succ}</div>
        </div>
    </div>
    '''


# print an entire board
def print_board(board: dict, threads_sorted : list, board_name : str):
    datetime_now = datetime.now().timestamp()

    # update version when you update css, js, images to bypass browser cache
    version_number = "21"

    # get all local board html files and add greeter links to them
    all_board_names = list()
    for each_file in pathlib.Path('.').glob('*.html'):
        if each_file.is_file():
            all_board_names.append(each_file.stem)
    all_board_names.sort()
    all_board_names_links = ''
    for each_board_name in all_board_names:
        all_board_names_links += f'<a href="{each_board_name}.html" class="greeter-element">/{each_board_name}/</a>'

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
            <link rel='stylesheet' type='text/css' href='resources/style.css?v={version_number}'>
            <script src='resources/script.js?v={version_number}' defer></script>
            <link rel="icon" type="image/x-icon" href="resources/favicon.png?v={version_number}">
            <title>/{board_name}/ - 4CHV</title>
        </head>
        <body>
            <div class="wrapper">
                <h1 class="page-title">
                    <a href="">/{board_name}/</a> - 4CHV
                </h1>
                <div class="greeter-3">
                Board updated <div title="Time since board was last built" class="board-time">{datetime_now}</div>
                </div>
                <hr>
                <div class="greeter">
                    {all_board_names_links}
                </div>
                <hr>
                <div class="greeter-2">
                    <ul class="greeter-2-list">
                        <li>Click <a>[+]</a> to fold / unfold threads and posts</li>
                        <li>Click <a>&gt;&gt;1234567</a> to jump to that post</li>
                        <li>Use browser / phone back-button to jump back</li>
                    </ul>
                </div>
                <hr>
                <div class="all-threads">
    ''')

    for thread_id in threads_sorted:
        thread = board[thread_id]

        thread_replies = 0
        if 'replies' in thread:
            thread_replies = thread['replies'] - 1

        thread_thumbnail_html = '''
        <a>
            <img src="./resources/thumbnail_not_found.png"></img>
        </a>
        '''
        if 'thumbnail' in thread and 'thread' in thread:
            op_post = thread['thread'][min(thread['thread'])]
            thread_thumbnail_url = op_post['file']
            thread_thumbnail = thread['thumbnail'].decode()
            thread_thumbnail_html = f'''
                <a href="{thread_thumbnail_url}" rel="noreferrer" target="_blank">
                    <img src="data:image/png;base64, {thread_thumbnail}"></img>
                </a>
            '''

        thread_sub = ''
        if 'sub' in thread:
            thread_sub = thread['sub']
            # thread_sub = filter_post_pre(thread_sub)
            thread_sub = html.escape(thread_sub)
            # thread_sub = filter_post_post(thread_sub)

            if thread_sub != '':
                thread_sub += ': '

        thread_com = ''
        if 'com' in thread:
            thread_com = thread['com']
            # thread_com = filter_post_pre(thread_com)
            thread_com = html.escape(thread_com)
            thread_com = filter_post_post(thread_com)

        thread_time = ''
        if 'last_modified' in thread:
            thread_time = thread['last_modified']

        # append the thread header to the main string list
        html_string.append(f'''
        <div class="thread-parent collapsed-thread-parent">
            <div class="thread-details">
                <div title="Toggle folding" class="thread-collapsible-anchor">[+]</div>
                <div title="See thread on 4chan.org" class="thread-op">
                    <a href="https://boards.4chan.org/{board_name}/thread/{thread_id}" rel="noreferrer" target="_blank">
                        -
                    </a>
                </div>
            </div>
            <div class="thread-options">
                <div class="thread-maximize-replies">Unfold all replies</div>
                <div class="thread-files-all">List all files</div>
                <div class="thread-reset">Reset</div>
            </div>
            <div title="Thread attachment" class="thread-thumbnail">
                {thread_thumbnail_html}
            </div>
            <div class="thread-details-2">
                <div title="Time since last reply" class="thread-time">{thread_time}</div>
                <div title="Thread replies" class="thread-replies">{thread_replies} replies</div>
            </div>
            <div class="thread-sub-description">
                <div title="Thread subject" class="thread-sub">{thread_sub}</div>
                <div class="thread-description">{thread_com}</div>
            </div>
            <div class="thread-files-dump"></div>
        ''')

        # create a sorted and nested post list for the thread
        post_list = list()
        if 'thread' in thread:
            posts = thread['thread']
            for post_id in posts:
                create_post_list_r(board, thread_id, post_id, 0, post_list)

        # go through the created post list and start building the html
        posts_string = list()
        curr_tabbing = 0
        for post_element in post_list:
            post = post_element["post"]
            tabbing = post_element["tabbing"]

            posts_string.append(f'''
            {'</div>' * max(curr_tabbing - tabbing + 1, 0)}
            <div class="post-parent-r {'collapsed-parent collapsed-parent-originally' if ('hidden' in post) else ''}">
                {print_post(post)}
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
                <hr>
                <div class="greeter-2">
                    <ul class="greeter-2-list">
                        <li><a href="#">Go to top</a></li>
                        <li>4CHV is free and open source software! (<a href="https://github.com/Infinitifall/4chv" target="_blank" rel=“noreferrer”>source repo</a>)</li>
                    </ul>
                </div>
                <hr>
            </div>
        </body>
    </html>
    ''')

    return ''.join(html_string)


# wrapper function to make html page for a board
def make_html(board_name: str, file_count: int):
    # check if db file exists
    if not pathlib.Path(f'threads/{board_name}.sqlite').is_file():
        print(f'skipping {board_name}.html, no database yet', flush=True)
        return

    # connect to board db
    db_connection = sqlite3.connect(f'threads/{board_name}.sqlite')

    # Strategy to filter out high traffic low quality threads:
    # 1. Choose the newest created (file_count // 4) thread files
    # 2. Choose the last modified (file_count * 1) with at least 10 replies ordered by replies
    # 3. Combine the second list with the first, limiting elements to (file_count * 1)
    tail_threads = chv_database.get_thread_nos_by_created(db_connection, file_count // 4)
    latest_files = chv_database.get_thread_nos_custom_1(db_connection, 10, file_count)
    all_threads = set()
    for thread_no in tail_threads:
        all_threads.add(thread_no)
    for thread_no in latest_files:
        if thread_no not in all_threads and len(all_threads) <= file_count:
            all_threads.add(thread_no)

    all_threads = list(all_threads)
    my_board = chv_database.get_threads(db_connection, all_threads)

    # skip if board has no threads
    if len(my_board) == 0:
        print(f'skipping {board_name}.html, no threads to be made yet', flush=True)
        return

    print(f'making {board_name}.html with {len(my_board)} threads', flush=True)
    # calculate complexity for board (medium)
    calculate_board_complexity(my_board)
    # sort threads by cumulative complexity (fast)
    threads_sorted = sort_board_cumulative_complexity(my_board)
    # print the entire board to html (slow)
    html_string = print_board(my_board, threads_sorted, board_name)

    # write board html to file (fast)
    with open(f'{board_name}.html', 'w') as f:
        f.write(html_string)
        print(f'built {board_name}.html', flush=True)
    return


def make_html_wrapper(wait_time: float, file_count: int):
    while True:
        try:
            # get list of board names
            board_names = chv_boards.boards_active
            # avoid busy wait if no active boards
            if len(board_names) == 0:
                print(f'no active boards! Uncomment lines in scripts/chv_boards.py!', flush=True)
                time.sleep(10)
                continue
            print(f'making: {", ".join(board_names)}', flush=True)

            # make all boards
            better_wait_time = max(wait_time // len(board_names), 10)
            for board_name in board_names:
                try:
                    make_html(board_name, file_count)
                    time.sleep(better_wait_time)
                except Exception as e:
                    print(f'failed to make {board_name}.html', flush=True)
                    print(e, flush=True)
                    time.sleep(10)

        except Exception as e:
            print('an error occurred!', flush=True)
            print(e, flush=True)
            time.sleep(10)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 3)
        wait_time = int(sys.argv[1])
        file_count = int(sys.argv[2])
        make_html_wrapper(wait_time, file_count)

    except Exception as e:
        print('Usage: python3 view.py <wait_time> <max_latest_posts>', flush=True)