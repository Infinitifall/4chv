import sys
import copy
import pathlib
import time
import re
import pickle
from datetime import datetime
import html
import math


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


# filter thread description post html escaping
def filter_description_post(content : str):
    clean_dict = {
        r'^(\&gt;.+)': r'<div class="green-text">\1</div>',  # greentext
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


# given a list of sentences, returns a list of the same length of their 'complexity scores'
def complexity_score(sentences_array):
    words_count = dict()
    sentences_words = dict()

    # populate words_count with global count of words
    # and sentences_words with words from each sentence
    for sentence in sentences_array:
        words = list()
        temp_words = re.findall(r'[\w\'"]+', sentence)
        for word in temp_words:
            words.append(word.lower())

        sentences_words[sentence] = words

        for word in words:
            if word in words_count:
                words_count[word] += 1
            else:
                words_count[word] = 1

    # create complexity value for each word
    words_complexity = dict()
    max_word_count = max(words_count.values())
    for word in words_count.keys():
        words_complexity[word] = max_word_count / words_count[word]

    # populate sentences_complexity
    sentences_complexity = list()
    for sentence in sentences_array:
        words = sentences_words[sentence]
        number_of_words = len(words)

        temp_list = [sentence, 0]

        # add up the complexity of each word
        for word in words:
            temp_list[1] += words_complexity[word]

        if number_of_words not in [0, 1]:
            temp_list[1] /= number_of_words ** (1 - 2/3)  # normalize by length powered to 1 - delta
        sentences_complexity.append(temp_list)

    # finally, sort sentences by their complexity in desc order
    return sorted(sentences_complexity, key=lambda x: -x[1])


# Calculate the cumulative complexity for a post, which depends on the complexities of its replies
def calculate_post_cumulative_complexity(board : dict, thread_no : int, post_no : int):
    post : dict = board[thread_no]['thread'][post_no]

    if 'cumulative_complexity' in post:
        return post['cumulative_complexity']

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

    all_posts_complexity = complexity_score(all_posts)
    all_posts_complexity_dict = dict()
    for complexity_pair in all_posts_complexity:
        all_posts_complexity_dict[complexity_pair[0]] = complexity_pair[1]

    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            if post['com'] in all_posts_complexity_dict:
                post['complexity'] = all_posts_complexity_dict[post['com']]
            else:
                post['complexity'] = 0

    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            calculate_post_cumulative_complexity(board, thread_no, post_no)


# sort a board's posts and threads by cumulative_complexity
def sort_board_cumulative_complexity(board : dict):
    threads_sorted = list()
    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            post['succ'] = sorted(post['succ'], key=lambda x: thread['thread'][x]['cumulative_complexity'], reverse=True)

        op_post_no = min(thread['thread'].keys())
        thread['cumulative_complexity_normalized'] = thread['thread'][op_post_no]['cumulative_complexity_normalized']
        threads_sorted.append(thread_no)

    threads_sorted = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity_normalized'], reverse=True)
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

    for succ in post['succ']:
        create_post_list_r(board, thread_id, succ, tabbing + 1, post_list)

    return post_list


# print a single post
def print_post(post: dict):
    complexity_int = math.floor((post['complexity'] / 100) ** 0.8)
    # cumulative_complexity_int = int((post['cumulative_complexity'] / 100) ** 0.8)
    # cumulative_complexity_diff_int = int(((post['cumulative_complexity'] - post['complexity']) / 100) ** 0.3)
    # complexity_hashes_int = int((post['complexity'] / 100) ** 0.7)
    complexity_hashes_int = math.floor((max(0, (post['cumulative_complexity_normalized'] - post['complexity'])) / 100) ** 0.3)

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
    post_filename = ''
    post_ext = ''
    if 'file' in post:
        post_file = post['file']
        post_filename = post['filename']
        post_ext = post['ext']

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
        <div title="Post attachment" class="post-file"><a href="{post_file}" rel="noreferrer" target="_blank">{post_filename}{post_ext}</a></div>
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
    # update version when you update css or js to bypass browser cache
    version_number = "18"

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
            <link rel="icon" type="image/x-icon" href="resources/favicon.png">
            <title>/{board_name}/ - 4CHV</title>
        </head>
        <body>
            <div class="wrapper">
            <h1 class="page-title">/{board_name}/ - <a href="https://github.com/Infinitifall/4chv" target="_blank" rel=“noreferrer”>4CHV</a></h1>
            <div class="greeter">
                {all_board_names_links}
            </div>
            <div class="greeter-2">
                <ul class="greeter-2-list">
                    <li>Click <a>[+]</a> to fold / unfold a post</li>
                    <li>Click <a>&gt;&gt;1234567</a> to jump to that post</li>
                    <li>Use browser / phone back-button to jump back</li>
                </ul>
            </div>
    ''')

    for thread_id in threads_sorted:
        thread = board[thread_id]

        thread_replies = 0
        if 'replies' in thread:
            thread_replies = thread['replies'] - 1

        thread_thumbnail_url = ''
        thread_thumbnail = ''
        if 'thumbnail' in thread and 'thread' in thread:
            op_post = thread['thread'][min(thread['thread'])]
            thread_thumbnail_url = op_post['file']
            thread_thumbnail = thread['thumbnail'].decode()

        thread_sub_com = ''
        if 'sub' in thread:
            thread_sub_com = thread['sub'][0:40 - math.floor(sum(0.4 for c in thread['sub'] if c.isupper()))]
            if len(thread_sub_com) < len(thread['sub']):
                thread_sub_com += '...'
            # thread_sub = filter_post_pre(thread_sub)
            thread_sub_com = html.escape(thread_sub_com)
            # thread_sub_com = filter_post_post(thread_sub_com)
            thread_sub_com = filter_description_post(thread_sub_com)

        thread_sub = ''
        if 'sub' in thread:
            thread_sub = thread['sub']
            # thread_sub = filter_post_pre(thread_sub)
            thread_sub = html.escape(thread_sub)
            # thread_sub = filter_post_post(thread_sub)

        thread_com = ''
        if 'com' in thread:
            # calculate the original comment first, for comparison
            thread_com_original = thread['com']
            # thread_com_original = filter_post_pre(thread_com_original)
            thread_com_original = html.escape(thread_com_original)
            if len(thread_com_original) > 0 and thread_com_original[-1] == '\n':
                thread_com_original = thread_com_original[:-1]
            thread_com_original = filter_description_post(thread_com_original)

            # select about the first 120 chars, take bold sub and uppercase into account
            thread_com = thread['com'][0:110 - math.floor(1.6 * (len(thread_sub_com)))]
            thread_com = thread_com[0:110 - math.floor(1.6 * (len(thread_sub_com))) - math.floor(sum(1 for c in thread_com if c.isupper()))]
            # thread_com = filter_post_pre(thread_com)
            thread_com = html.escape(thread_com)
            if len(thread_com) > 0 and thread_com[-1] == '\n':
                thread_com = thread_com[:-1]
            thread_com = filter_description_post(thread_com)

            # trailing dots if thread_com is prematurely cut off
            if len(thread_com_original) > len(thread_com):
                thread_com += '...'

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
                <div title="Thread replies" class="thread-replies">{thread_replies} replies</div>
            </div>
            <div class="thread-options">
                <div class="thread-maximize-replies">Unfold all replies</div>
                <div class="thread-files-all">List all files</div>
                <div class="thread-reset">Reset</div>
            </div>
            <div title="Thread attachment" class="thread-thumbnail">
                <a href="{thread_thumbnail_url}" rel="noreferrer" target="_blank">
                    <img src="data:image/png;base64, {thread_thumbnail}">
                    </img>
                </a>
            </div>
            <div title="Thread subject" class="thread-sub-com">{thread_sub_com}</div>
            <div title="Thread subject" class="thread-sub">{thread_sub}</div>
            <div class="thread-files-dump"></div>
            <div class="thread-description">{thread_com}</div>
            <div title="Time since last reply" class="thread-time">{thread_time}</div>
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
        </body>
    </html>
    ''')

    return ''.join(html_string)


# wrapper function to make html page for a board
def make_html(board_name: str, file_count: int):

    # our strategy to filter out high traffic low quality posts is as follows:
    #
    # 1. Choose the most recent 30 * file_count thread files and unpickle them
    #
    # 2. The most recent 1/4 * file_count are selected immediately, giving new threads a chance
    #
    # 3. For the rest (30 - 1/4) * file_count threads aka "tail_threads", we pick the threads 
    #    with the highest time adjusted cumulative complexity scores

    # get list of latest thread files for board
    if not pathlib.Path(f'threads/{board_name}').is_dir():
        print(f'skipping {board_name}.html, no folder found', flush=True)
        return

    thread_files = sorted(pathlib.Path(f'threads/{board_name}').iterdir())
    latest_files = sorted(list(thread_files), reverse=True)[:(10 * file_count)]

    # read the files
    my_board = dict()
    for each_file in latest_files:
        if not each_file.is_file():
            continue
        try:
            with open(each_file, 'rb') as f:
                my_board[int(each_file.stem)] = pickle.load(f)
        except:
            continue

    # skip if board has no threads
    if len(my_board) == 0:
        print(f'skipping {board_name}.html, no files found', flush=True)
        return

    print(f'making {board_name}.html', flush=True)
    
    #########################################################################################
    # Too slow for Python :(
    #########################################################################################
    #
    # # calculate time adjusted complexity scores for the threads
    # # i.e, a thread loses points for every hour old it is
    # thread_cumulative_complexity_time_decay = dict()
    # # my_board_copy = copy.deepcopy(my_board)  # make a deep copy in case of tampering
    # my_board_copy = my_board  # deep copy not strictly needed, since complexity gets overwritten
    # calculate_board_complexity(my_board_copy)
    # for thread_no in my_board_copy:
    #     op_post_no = min(my_board_copy[thread_no]['thread'].keys())
    #     datetime_now = datetime.utcnow().timestamp()
    #     last_modified = my_board_copy[thread_no]['last_modified'] if 'last_modified' in my_board_copy[thread_no] else datetime_now
    #     thread_cumulative_complexity_time_decay[thread_no] = (my_board_copy[thread_no]['thread'][op_post_no]['cumulative_complexity_normalized'] / 100) ** 0.3 - (datetime_now - last_modified) / (60 * 60) * 6

    # tail_threads = sorted(list(my_board.keys()), reverse=True)[:math.floor(1/4 * file_count)]
    # complexity_sorted_threads = sorted(list(my_board.keys()), key=lambda x: thread_cumulative_complexity_time_decay[x], reverse=True)
    # thread_count = 0
    # for thread_no in complexity_sorted_threads:
    #     if thread_count >= file_count:
    #         my_board.pop(thread_no, None)
    #     elif thread_no in tail_threads:
    #         thread_count += 1
    #     elif my_board[thread_no]['replies'] > 10:
    #         thread_count += 1
    #     else:
    #         my_board.pop(thread_no, None)
    #
    #########################################################################################
    
    # calculate time adjusted complexity scores for the threads
    # i.e, a thread loses points for every hour old it is
    tail_threads = sorted(list(my_board.keys()), reverse=True)[:math.floor(1/4 * file_count)]
    complexity_sorted_threads = sorted(list(my_board.keys()), reverse=True)
    thread_count = 0
    for thread_no in complexity_sorted_threads:
        if thread_count >= file_count:
            my_board.pop(thread_no, None)
        elif thread_no in tail_threads:
            thread_count += 1
        elif my_board[thread_no]['replies'] > 10:
            thread_count += 1
        else:
            my_board.pop(thread_no, None)

    print(f'populating {board_name}.html with {len(my_board)} threads', flush=True)
    # calculate complexity for board (fast)
    # sort threads by cumulative complexity (fast)
    # print the entire board to html (slow)
    # write board html to file (fast)
    calculate_board_complexity(my_board)
    threads_sorted = sort_board_cumulative_complexity(my_board)
    html_string = print_board(my_board, threads_sorted, board_name)
    with open(f'{board_name}.html', 'w') as f:
        f.write(html_string)
    print(f'built {board_name}.html', flush=True)


def make_html_wrapper(wait_time: float, file_count: int):
    while True:
        try:
            # get list of board names from boards.txt
            board_names = list()
            with open('boards.txt', 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    if line == '':
                        continue
                    board_names.append(line)

            # avoid busy spinning by waiting a bit if the list is empty
            if len(board_names) == 0:
                print(f'no boards to make!', flush=True)
                time.sleep(10)
                continue

            print(f'making: {", ".join(board_names)}', flush=True)

            # dont make the same board more frequently than once every 2 min
            better_wait_time = max(wait_time, 120/len(board_names))

            for board_name in board_names:
                try:
                    make_html(board_name, file_count)
                    time.sleep(better_wait_time)
                except Exception as e:
                    print(f'failed to make {board_name}.html', flush=True)
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
