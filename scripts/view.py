import sys
import pathlib
import re
import pickle
import time
import base64
from datetime import datetime
import html


# filter post text pre html escaping
def filter_post_pre(content : str):
    clean_dict = {
        r'[^\x00-\x7F]+': '',  # weird unicode symbols
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


# filter post text post html escaping
def filter_post_post(content : str):
    clean_dict = {
        r'\&gt;(\d{5,20})': r'<a class="reply-text" href="#\1">&gt;\1</a>',  # reply quotes
        r'^(\&gt;.+)': r'<div class="green-text">\1</div>',  # greentext
        r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))': r'<a href="\1">\1</a>',  # links
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


"""
The following function has been sourced from other software (licenses below):

1. From Infinitifall/complexity-sort, MIT License, Copyright (c) 2022 Infinitifall


MIT License

Copyright (c) 2022 Infinitifall

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# given a list of sentences, returns a list of the same length of their 'complexity scores'
def complexity_score(sentences_array):
    words_count = dict()
    sentences_words = dict()

    # populate words_count with global count of words
    # and sentences_words with words from each sentence
    for sentence in sentences_array:
        words = list()
        temp_words = re.findall(r'(\w[\w\']+\w|\w+)',sentence)
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
    cumulative_post_complexity = 0

    if len(post['succ']) > 0:
        for succ in post['succ']:
            cumulative_post_complexity += calculate_post_cumulative_complexity(board, thread_no, succ)

        cumulative_post_complexity /= (len(post['succ'])) ** (1 - 2/3)

    cumulative_post_complexity += post['complexity']
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
            post['cumulative_complexity'] = calculate_post_cumulative_complexity(board, thread_no, post_no)


# sort a board's posts and threads by cumulative_complexity
def sort_board_cumulative_complexity(board : dict):
    threads_sorted = list()
    for thread_no, thread in board.items():
        for post_no, post in thread['thread'].items():
            post['succ'] = sorted(post['succ'], key=lambda x: thread['thread'][x]['cumulative_complexity'], reverse=True)
        thread['complexity'] = thread['thread'][min(thread['thread'].keys())]['complexity']
        thread['cumulative_complexity'] = thread['thread'][min(thread['thread'].keys())]['cumulative_complexity']
        threads_sorted.append(thread_no)
    threads_sorted = sorted(threads_sorted, key=lambda x: board[x]['cumulative_complexity'], reverse=True)
    return threads_sorted


# recursively print all posts in thread with appropriate tabbing
def print_posts_r(board : dict, thread_id : int, post_id : int, tabbing : int, html_string : str):
    html_string += '<div class="post-parent-r">'

    if post_id not in board[thread_id]['thread']:
        # post might have been deleted
        html_string += f'<div class="post-parent></div>'
        html_string += '</div>'
        return html_string

    post = board[thread_id]['thread'][post_id]

    if 'printed_once' in post:
        html_string += '</div>'
        return html_string
    
    # logic for hiding a post by default
    hidden = False
    post_complexity_int = int((post['complexity'] / 100) ** 0.8)
    if (post_complexity_int <= 10 + 2 * tabbing) and not (tabbing == 0):
        hidden = True
        html_string = html_string[:-2] + ' collapsed-parent">'
    
    html_string += print_post(post, tabbing, hidden)
    post['printed_once'] = True

    for succ in post['succ']:
        html_string = print_posts_r(board, thread_id, succ, tabbing + 1, html_string)
    
    html_string += '</div>'
    return html_string


# print a single post
def print_post(post: dict, tabs: int, hidden: bool):
    html_string = ""

    if hidden:
        html_string += f'<div class="post-parent collapsed">'
    else:
        html_string += f'<div class="post-parent">'

    html_string += '<a class="post-collapsible-anchor">[+]</a>'
    
    html_string += f'<a class="post-no" id="{post["no"]}" href="#{post["no"]}">#{post["no"]}</a>'
    
    complexity_int = int((post['complexity'] / 100) ** 0.8)
    # cumulative_complexity_int = int((post['cumulative_complexity'] / 100) ** 0.8)
    # cumulative_complexity_diff_int = int(((post['cumulative_complexity'] - post['complexity']) / 100) ** 0.8)
    complexity_hashes_int = int((post['complexity'] / 100) ** 0.7)
    
    html_string += f'<div class="post-complexity-number">{complexity_int} points</div>'
    html_string += f'<div class="post-complexity">{"#" * complexity_hashes_int}</div>'
    
    time_delta = datetime.now() - datetime.fromtimestamp(post['time'])
    time_delta_days = time_delta.days
    time_delta_hours = int(time_delta.total_seconds() // 3600)
    time_delta_minutes = int((time_delta.total_seconds() % 3600) // 60)
    if time_delta_days == 0:
        if time_delta_hours == 0:
            html_string += f'<div class="post-time">{time_delta_minutes}m ago</div>'
        else:
            html_string += f'<div class="post-time">{time_delta_hours}h {time_delta_minutes}m ago</div>'
    else:
        html_string += f'<div class="post-time">{time_delta_days}d {time_delta_hours}h ago</div>'

    if 'name' in post:
        post_name = html.escape(post["name"])
        html_string += f'<div class="post-name">~{post_name}</div>'
    
    if 'country_name' in post:
        html_string += f'<div class="post-country-name">{post["country_name"]}</div>'

    if 'file' in post:
        html_string += f'''<div class="post-file"><a href="{post['file']}" target="_blank">{post['filename'] + post['ext']}</a></div>'''

    if 'com' in post and len(post['com']) > 0:
        post_com = filter_post_pre(post['com'])
        post_com = html.escape(post_com)
        post_com = filter_post_post(post_com)
        html_string += f'<div class="post">{post_com}</div>'
    else:
        html_string += '<div class="post">???</div>'

    html_string += '</div>'
    
    return html_string


# print an entire board
def print_board(board: dict, threads_sorted : list, board_name : str):
    version_number = "4.1"
    html_string = f'''
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <meta name="robots" content="noindex">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta property="og:locale" content="en_US">
            <meta property="og:type" content="website">
            <link rel='stylesheet' type='text/css' href='resources/style.css?v={version_number}'>
            <script src='resources/collapsible.js?v={version_number}' defer></script>
            <link rel="icon" type="image/x-icon" href="resources/favicon.png">
            <title>4CHV</title> 
        </head>
        <body>
            <div class="wrapper">
            <h1 class="page-title">4CHV: a viewer for a more civilized age</h1>
            <div class="greeter">
                <a href="sci.html" class="greeter-element">/sci/</a>
                <a href="g.html" class="greeter-element">/g/</a>
                <a href="lit.html" class="greeter-element">/lit/</a>
                <a href="his.html" class="greeter-element">/his/</a>
                <a href="tv.html" class="greeter-element">/tv/</a>
                <a href="mu.html" class="greeter-element">/mu/</a>
                <a href="x.html" class="greeter-element">/x/</a>
            </div>
    '''

    thread_count = 0
    for thread_id in threads_sorted:
        if (thread_count >= 0):
            html_string += '<div class="thread-parent collapsed-thread-parent">'
        else:
            html_string += '<div class="thread-parent">'
        
        thread = board[thread_id]
        html_string += '<a class="thread-collapsible-anchor">[+]</a>'
        html_string += f'<div class="thread"><a href="https://boards.4chan.org/{board_name}/thread/{thread_id}" target="_blank">Permalink</a></div>'

        if 'replies' in thread:
            html_string += f'<div class="thread-replies">{thread["replies"]} replies</div>'
        else:
            html_string += f'<div class="thread-replies">0 replies</div>'
        
        if 'thumbnail' in thread and 'thread' in thread:
            op_post = thread['thread'][min(thread['thread'])]
            html_string += f'''<div class="thread-thumbnail"><a href="{op_post['file']}" target="_blank"><img src="data:image/png;base64, {thread['thumbnail'].decode()}"></img></a></div>'''

        if 'sub' in thread:
            thread_sub = filter_post_pre(thread["sub"][0:100])
            thread_sub = html.escape(thread_sub)
            thread_sub = filter_post_post(thread_sub)
            html_string += f'<div class="thread-sub">{thread_sub}</div>'

        if 'com' in thread:
            thread_com = filter_post_pre(thread['com'][0:100])
            thread_com = html.escape(thread_com)
            thread_com = filter_post_post(thread_com)
            html_string += f'<div class="thread-description">{thread_com}...</div>'
        
        if 'thread' in thread:
            posts = thread['thread']
            for post_id in posts:
                html_string = print_posts_r(board, thread_id, post_id, 0, html_string)
    
        html_string += '</div>'

        thread_count += 1

    html_string += '''
        </div>
        </body>
    </html>
    '''

    return html_string


def make_html(board_name: str, file_count: int, wait_time: int):
    while(True):
        if not pathlib.Path(f'threads/{board_name}').is_dir():
            print(f'Board /{board_name}/ not found found locally, have you downloaded it?')
            return

        thread_files = pathlib.Path(f'threads/{board_name}').glob('*')
        latest_files = sorted(thread_files, reverse=True)[:file_count]

        my_board = dict()

        for file in latest_files:
            with open(file, 'rb') as f:
                my_board[int(file.name[:-4])] = pickle.load(f)
        
        calculate_board_complexity(my_board)
        threads_sorted = sort_board_cumulative_complexity(my_board)
        html_string = print_board(my_board, threads_sorted, board_name)

        with open(f'{board_name}.html', 'w') as f:
            f.write(html_string)
    
        print(f'built {board_name}.html')
        time.sleep(wait_time)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 4)
        board_name = sys.argv[1] # eg. mu, sci, tv
        file_count = int(sys.argv[2])
        wait_time = int(sys.argv[3])

        make_html(board_name, file_count, wait_time)

    except Exception as e:
        print('Usage: python view.py <board> <max_latest_posts> <wait_time>')
