import sys
import pathlib
import time
import json
import re
import pickle
import base64
import random

import requests
import urllib3


# api urls
def thread_url(board_name: str, thread_no: str):
    return f'https://a.4cdn.org/{board_name}/thread/{thread_no}.json'


def catalog_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/catalog.json'


def threadlist_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/threads.json'


def content_url(board_name: str, tim: str, ext: str):
    return f'https://i.4cdn.org/{board_name}/{tim}{ext}'


def thumbnail_url(board_name: str, tim: int):
    return f'https://i.4cdn.org/{board_name}/{tim}s.jpg'


# clean post text
def clean_post(content: str):
    clean_dict = {
        r'<[ap] [^>]+>': '>',
        r'<span [^>]+>': '>',
        '<span class="deadlink">': '',
        '&quot;': '\"',
        '&amp;': '&',
        '&#039;': "'",
        '(<br>)+': '\n',
        '&gt;': '',
        '<wbr>': '',
        '\?P<replyquote>>': '>',
        '</span>': '',
        '</[asp]+>': '',
        '\n+': '\n',
        r'^\n': '',
        r'<pre [^>]+>': '',
        '</pre>': '',
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


def get_url_custom(custom_url):
    session = requests.Session()
    retry = urllib3.util.retry.Retry(connect=3, backoff_factor=random.randint(10,30) / 10)
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    request = session.get(custom_url)
    return request


def get_boards(board_names: list, wait_time: float, threads_last_accessed: dict):
    # get the threads list
    massive_threads_list_sorted = list()
    for board_name in board_names:
        # create local folder and initialize last accessed dict
        pathlib.Path(f'threads/{board_name}').mkdir(parents=True, exist_ok=True)
        if board_name not in threads_last_accessed:
            threads_last_accessed[board_name] = dict()
        
        # fetch threadlist
        request = get_url_custom(threadlist_url(board_name))
        threadlist = json.loads(request.text)
        print(f'downloaded /{board_name}/ threadlist')
        sys.stdout.flush()
        time.sleep(random.randint(wait_time // 2, (wait_time * 3) // 2))

        for page in threadlist:
            if 'threads' not in page:
                continue
            for thread in page['threads']:
                thread['board_name'] = board_name
                massive_threads_list_sorted.append(thread)
    
    # sort the threads list
    massive_threads_list_sorted.sort(key=lambda x: x['last_modified'], reverse=True)
    massive_threads_list_sorted_2 = list()
    massive_threads_list_sorted_3 = list()
    for thread in massive_threads_list_sorted:
        if thread['replies'] > 10:
            massive_threads_list_sorted_2.append(thread)
        else:
            massive_threads_list_sorted_3.append(thread)
    massive_threads_list_sorted = massive_threads_list_sorted_2 + massive_threads_list_sorted_3

    # check memory for last modified
    massive_threads_list_sorted_4 = list()
    for thread in massive_threads_list_sorted:
        # check memory for last modified
        if thread['no'] in threads_last_accessed[board_name]:
            if threads_last_accessed[board_name][thread['no']] == thread['last_modified']:
                continue
        threads_last_accessed[board_name][thread['no']] = thread['last_modified']
        massive_threads_list_sorted_4.append(thread)
    massive_threads_list_sorted = massive_threads_list_sorted_4

    i = 0
    for thread in massive_threads_list_sorted:
        i += 1
        
        # check local file for last modified
        local_thread_file = pathlib.Path(f'threads/{thread["board_name"]}/' + str(thread['no']) + '.pkl')
        if local_thread_file.is_file():
            with open(f'threads/{thread["board_name"]}/' + str(thread['no']) + '.pkl', 'rb') as my_file:
                local_thread = pickle.load(my_file)
                if 'last_modified' in local_thread and thread['last_modified'] == local_thread['last_modified']:
                    print(f'[{i}/{len(massive_threads_list_sorted)}] skipping   /{thread["board_name"]}/thread/{thread["no"]}')
                    continue
        
        # if modified since, download the thread
        try:
            get_thread(thread["board_name"], thread['no'])
            print(f'[{i}/{len(massive_threads_list_sorted)}] downloaded /{thread["board_name"]}/thread/{thread["no"]}')
            sys.stdout.flush()
            time.sleep(random.randint(wait_time // 2, (wait_time * 3) // 2))
        except Exception as e:
            print(f'[{i}/{len(massive_threads_list_sorted)}] failed!    /{thread["board_name"]}/thread/{thread["no"]}')
            print(e)
            time.sleep(random.randint(10,20))


def get_thread(board_name: str, thread_no: int):
    request = get_url_custom(thread_url(board_name, str(thread_no)))
    thread: dict = json.loads(request.text)
    this_thread = dict()

    if 'posts' not in thread:
        return
    
    op_post_no = thread['posts'][0]['no']
    this_thread['thread'] = dict()
    for post in thread['posts']:
        post: dict
        this_post = dict()

        this_post['no'] = int(post['no'])
        this_post['time'] = int(post['time'])
        
        if 'com' in post:
            this_post['com'] = clean_post(str(post['com']))
        else:
            this_post['com'] = ''

        if 'sub' in post:
            this_post['sub'] = clean_post(str(post['sub']))
        
        if 'name' in post:
            if post['name'] != 'Anonymous':
                this_post['name'] = post['name']
        
        if 'filename' in post and 'ext' in post:
            this_post['file'] = content_url(board_name, str(post['tim']), str(post['ext']))
            this_post['tim'] = post['tim']
            this_post['filename'] = post['filename']
            this_post['ext'] = post['ext']
        
        if 'country' in post and 'country_name' in post:
            this_post['country'] = post['country']
            this_post['country_name'] = post['country_name']

        # link preds and succs
        this_post['pred'] = re.findall(r'>\d{6,}', this_post['com'])
        this_post['succ'] = list()

        if not this_post['pred']:
            this_post['pred'].append(">" + str(op_post_no))
            # if its empty make it a succ of the op
        
        for pred in this_post['pred']:
            if int(pred[1:]) in this_thread['thread']:
                this_thread['thread'][int(pred[1:])]['succ'].append(post['no'])
        this_thread['thread'][post['no']] = this_post

    # calculate thread details
    thread_posts = list(this_thread['thread'].keys())
    this_thread['replies'] = len(thread_posts)
    if len(thread_posts) > 0:
        this_thread['last_modified'] = this_thread['thread'][thread_posts[-1]]['time']

    # get some more info from op post
    if op_post_no in this_thread['thread']:
        op_post = this_thread['thread'][op_post_no]
        this_thread['no'] = op_post['no']

        if 'filename' in op_post and 'ext' in op_post and 'tim' in op_post:
            thumbnail = requests.get(
                thumbnail_url(board_name, str(op_post['tim']))
            ).content
            this_thread['thumbnail'] = base64.b64encode(thumbnail)

        if 'sub' in op_post:
            this_thread['sub'] = op_post['sub']
        
        if 'com' in op_post:
            this_thread['com'] = op_post['com']
    
    with open(f'threads/{board_name}/' + str(this_thread['no']) + '.pkl', 'wb') as my_file:
        pickle.dump(this_thread, my_file)
    
    return


def get_boards_wrapper(board_names: list, wait_time: float):
    # dict to store last_accessed for all threads
    threads_last_accessed = dict()
    while True:
        try:
            get_boards(board_names, wait_time, threads_last_accessed)
            time.sleep(10)
        except Exception as e:
            print('an error occurred!')
            print(e)
            time.sleep(10)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 3)
        wait_time = float(sys.argv[1])
        board_names = sys.argv[2:]

        get_boards_wrapper(board_names, wait_time)

    except Exception as e:
        print('Usage: python3 download.py <wait_time_between_requests> <board-1> <board-2> ...')
    
