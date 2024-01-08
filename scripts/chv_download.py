import sys
import pathlib
import random
import re
import time
from datetime import datetime
import requests
import urllib3
import base64
import json
import html
import sqlite3

# local imports
import chv_boards
import chv_database


# thread api endpoint
def thread_url(board_name: str, thread_no: str):
    return f'https://a.4cdn.org/{board_name}/thread/{thread_no}.json'


# catalog api endpoint
def catalog_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/catalog.json'


# threadlist api endpoint
def threadlist_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/threads.json'


# file url
def content_url(board_name: str, tim: str, ext: str):
    return f'https://i.4cdn.org/{board_name}/{tim}{ext}'


# thumbnail url
def thumbnail_url(board_name: str, tim: int):
    return f'https://i.4cdn.org/{board_name}/{tim}s.jpg'


# clean post['com'] by removing html tags
def clean_post(content: str):
    clean_dict = {
        '\?P<replyquote>>': '>>',

        r'</[asp]+>': '',
        '</span>': '',
        '</pre>': '',

        r'<pre [^>]+>': '',
        r'<[ap] [^>]+>': '>',
        r'<span [^>]+>': '>',
        '<span class="deadlink">': '',

        '&gt;': '',
        '<wbr>': '',
        '(<br>)+': '\n',
        '\n+': '\n',
        r'^\n': '',
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)

    content = html.unescape(content)
    return content


# get request with retries in case of
def get_url_custom(custom_url):
    session = requests.Session()
    retry = urllib3.util.retry.Retry(
        connect=3,
        backoff_factor=random.randint(10,30) / 10
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    request = session.get(custom_url)
    return request


def download_all_boards(board_names: list, wait_time: float):
    datetime_now = datetime.now().timestamp()

    # ensure threads folder is created
    pathlib.Path(f'threads/').mkdir(parents=True, exist_ok=True)

    db_connections = dict()
    all_threads = list()
    for board_name in board_names:
        all_threads_2 = list()

        # get active threadlist on board
        request = get_url_custom(threadlist_url(board_name[0]))
        threadlist = json.loads(request.text)
        for page in threadlist:
            for thread in page['threads']:
                thread['board_name'] = board_name[0]
                all_threads_2.append(thread)

        # add board db connection to db_connections dict
        db_connections[board_name[0]] = sqlite3.connect(f'threads/{board_name[0]}.sqlite')

        # initialize board db in case it doesn't exist
        chv_database.create_board_db(db_connections[board_name[0]])

        # get threads if in db
        db_thread = chv_database.get_threads(
            db_connections[board_name[0]],
            [t['no'] for t in all_threads_2]
        )

        # remove threads not modified since last download
        all_threads_2 = [
            t for t in all_threads_2
            if t['no'] not in db_thread
                or db_thread[t['no']]['last_modified'] != t['last_modified']
        ]
        all_threads.extend(all_threads_2)

        print(f'fetched threadlist for /{board_name[0]}/', flush=True)
        time.sleep(random.randint(wait_time // 2, (wait_time * 3) // 2))

    # sort to prioritize "hot" threads, weighing a reply as a 5 min bonus
    all_threads.sort(
        key=lambda x: (datetime_now - x['last_modified']) // (60 * 5) - x['replies']
    )

    for thread_index, thread in enumerate(all_threads):
        # if modified since, download the thread
        try:
            download_thread(thread['board_name'], thread['no'], db_connections[thread['board_name']])
            print(f'[{thread_index + 1}/{len(all_threads)}] downloaded /{thread["board_name"]}/thread/{thread["no"]}', flush=True)
            time.sleep(random.randint(wait_time // 2, (wait_time * 3) // 2))

        except Exception as e:
            print(f'[{thread_index + 1}/{len(all_threads)}] failed!    /{thread["board_name"]}/thread/{thread["no"]}', flush=True)
            print(e, flush=True)
            time.sleep(10)


def download_thread(board_name: str, thread_no: int, db_connection):
    request = get_url_custom(thread_url(board_name, str(thread_no)))
    thread: dict = json.loads(request.text)
    this_thread = dict()

    if 'posts' not in thread:
        return

    # op post_no is same as thread_no
    op_post_no = thread_no

    this_thread['thread'] = dict()
    for post in thread['posts']:
        post: dict
        this_post = dict()

        this_post['no'] = int(post['no'])
        this_post['time'] = int(post['time'])

        this_post['pred'] = list()
        if 'com' in post:
            this_post['pred'] = re.findall(r'href="#p(\d+)"', post['com'])
            this_post['pred'] = [int(p) for p in this_post['pred'] if int(p) != this_post['no']]

            this_post['com'] = clean_post(post['com'])
        else:
            this_post['com'] = ''

        if 'sub' in post:
            this_post['sub'] = clean_post(post['sub'])

        if 'name' in post:
            if post['name'] != 'Anonymous':
                this_post['name'] = clean_post(post['name'])

        if 'id' in post:
            this_post['id'] = post['id']

        if 'filename' in post and 'ext' in post:
            this_post['file'] = content_url(board_name, str(post['tim']), str(post['ext']))
            this_post['tim'] = post['tim']
            this_post['filename'] = post['filename']
            this_post['ext'] = post['ext']

        if 'country' in post and 'country_name' in post:
            this_post['country'] = post['country']
            this_post['country_name'] = post['country_name']

        # link preds and succs
        this_post['succ'] = list()
        # if no preds, op is likely the pred (also helps with complexity calculation)
        if len(this_post['pred']) == 0:
            this_post['pred'].append(op_post_no)
        for pred in this_post['pred']:
            if pred in this_thread['thread']:
                # avoid duplicates
                if post['no'] not in this_thread['thread'][pred]['succ']:
                    this_thread['thread'][pred]['succ'].append(post['no'])
        this_thread['thread'][post['no']] = this_post

    # more thread details
    last_post_no = max(this_thread['thread'])
    this_thread['replies'] = len(this_thread['thread'])
    if op_post_no in this_thread['thread']:
        op_post = this_thread['thread'][op_post_no]

        this_thread['last_modified'] = this_thread['thread'][last_post_no]['time']
        this_thread['no'] = op_post['no']

        if 'filename' in op_post and 'ext' in op_post and 'tim' in op_post:
            thumbnail = get_url_custom(thumbnail_url(board_name, op_post['tim']))
            thumbnail = thumbnail.content
            this_thread['thumbnail'] = base64.b64encode(thumbnail)

        if 'sub' in op_post:
            this_thread['sub'] = op_post['sub']

        if 'com' in op_post:
            this_thread['com'] = op_post['com']

    chv_database.save_thread(db_connection, this_thread)
    return


def download_all_boards_wrapper(wait_time: float):
    while True:
        try:
            # get list of board names
            board_names = chv_boards.boards_active
            if len(board_names) == 0:
                print(f'no active boards! Uncomment lines in scripts/chv_boards.py!', flush=True)
                time.sleep(10)
                continue
            print(f'downloading: {", ".join([b[0] for b in board_names])}', flush=True)

            # download them all
            download_all_boards(board_names, wait_time)
            time.sleep(random.randint(wait_time // 2, (wait_time * 3) // 2))

        except Exception as e:
            print('an error occurred!', flush=True)
            print(e, flush=True)
            time.sleep(10)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 2)
        wait_time = float(sys.argv[1])
        download_all_boards_wrapper(wait_time)

    except Exception as e:
        print('Usage: python3 download.py <wait_time_between_requests>', flush=True)

