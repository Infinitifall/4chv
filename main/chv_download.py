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
import chv_config
import chv_database


# boards api endpoint
def boards_url():
    return 'https://a.4cdn.org/boards.json'


# thread api endpoint
def thread_url(board_name: str, thread_no: str):
    return f'https://a.4cdn.org/{board_name}/thread/{thread_no}.json'


# catalog api endpoint
def catalog_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/catalog.json'


# threadlist api endpoint
def threadlist_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/threads.json'


# archive api endpoint
def archive_url(board_name: str):
    return f'https://a.4cdn.org/{board_name}/archive.json'


# file url
def content_url(board_name: str, tim: str, ext: str):
    return f'https://i.4cdn.org/{board_name}/{tim}{ext}'


# thumbnail url
def thumbnail_url(board_name: str, tim: int):
    return f'https://i.4cdn.org/{board_name}/{tim}s.jpg'


# clean post['com'] by removing html tags
def clean_post(content: str):
    clean_dict = {
        '\\?P<replyquote>': '',

        r'</[asp]+>': '',
        '</span>': '',
        '</pre>': '',

        r'<pre [^>]+>': '',
        r'<[ap] [^>]+>': '',
        r'<span [^>]+>': '',
        '<span class="deadlink">': '',

        '&gt;': '>',
        '<wbr>': '',
        '<br>': '\n',
        '\n\n+': '\n\n',
        # r'^\n': '',
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)

    content = html.unescape(content)
    return content


REQUEST_HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3' }
# get request with retries in case of
def get_url_custom(custom_url):
    session = requests.Session()
    retry = urllib3.util.retry.Retry(
        connect=3,
        backoff_factor=random.uniform(10,30)/10
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    request = session.get(custom_url, headers=REQUEST_HEADERS)
    return request


def download_all_boards(board_names: list, wait_time: float):
    datetime_now = datetime.now().timestamp()

    # ensure threads folder is created
    pathlib.Path(f'threads/').mkdir(parents=True, exist_ok=True)
    db_connections = dict()

    # get threads to download
    modified_and_new_threads = list()
    all_thread_nos = dict()
    for board_name in board_names:
        # ensure thumbs folder is created
        pathlib.Path(f'html/thumbs/{board_name[0]}/').mkdir(parents=True, exist_ok=True)

        all_threads_board = list()

        # get active threadlist on board
        request = get_url_custom(threadlist_url(board_name[0]))
        threadlist_json = json.loads(request.text)
        for page in threadlist_json:
            for thread in page['threads']:
                thread['board_name'] = board_name[0]
                all_threads_board.append(thread)
        all_thread_nos[board_name[0]] = [t['no'] for t in all_threads_board]

        # add board db connection to db_connections dict
        db_connections[board_name[0]] = sqlite3.connect(f'threads/{board_name[0]}.sqlite')

        # initialize board db in case it doesn't exist or is on an older version
        chv_database.startup_boards_db(db_connections[board_name[0]])

        # delete very old threads
        post_nos_deleted = chv_database.delete_very_old_threads(db_connections[board_name[0]], chv_config.db_max_threads_per_board)
        for op_post_no_deleted in post_nos_deleted:
            pathlib.Path.unlink(f'html/thumbs/{board_name[0]}/{op_post_no_deleted}.jpg', missing_ok=True)
        if len(post_nos_deleted) != 0:
            print(f'removed {len(post_nos_deleted)} very old posts for /{board_name[0]}/', flush=True)

        # get threads present in db
        db_threads = chv_database.get_threads_shallow(
            db_connections[board_name[0]],
            [t['no'] for t in all_threads_board]
        )

        # filter for modified and new threads
        modified_and_new_threads_board = [
            t for t in all_threads_board
            if t['no'] not in db_threads
                or db_threads[t['no']]['last_modified'] != t['last_modified']
        ]
        modified_and_new_threads.extend(modified_and_new_threads_board)

        print(f'fetched threadlist for /{board_name[0]}/', flush=True)
        time.sleep(random.uniform(wait_time/2, wait_time*3/2))

    # mark threads as archived
    archived_boards = set()
    archived_thread_nos = dict()
    request = get_url_custom(boards_url())
    boards_json: dict = json.loads(request.text)
    for board_json in boards_json['boards']:
        if 'is_archived' in board_json and board_json['is_archived'] == 1:
            archived_boards.add(board_json['board'])
    for board_name in board_names:
        if board_name[0] not in archived_boards:
            continue
        request = get_url_custom(archive_url(board_name[0]))
        archives_json: list = json.loads(request.text)
        archived_thread_nos[board_name[0]] = archives_json

        # mark threads as archived
        chv_database.archive_threads(db_connections[board_name[0]], archived_thread_nos[board_name[0]])
        print(f'archived threads on /{board_name[0]}/', flush=True)
        time.sleep(random.uniform(wait_time/2, wait_time*3/2))

    # mark threads as 404d
    for board_name in board_names:
        four_o_four_thread_nos = list()
        non_four_o_four_yet_thread_nos = chv_database.non_four_o_four_threads(db_connections[board_name[0]])
        for thread_no in non_four_o_four_yet_thread_nos:
            if thread_no not in all_thread_nos[board_name[0]] and thread_no not in archived_thread_nos[board_name[0]]:
                # thread has been 404d
                four_o_four_thread_nos.append(thread_no)
        chv_database.four_o_four_threads(db_connections[board_name[0]], four_o_four_thread_nos)
        print(f'404d threads on /{board_name[0]}/', flush=True)

    # sort to prioritize "hot" threads, weighing a reply as a 5 min bonus
    modified_and_new_threads.sort(
        key=lambda x: (datetime_now - x['last_modified']) // (60 * 5) - x['replies']
    )

    # filter threads to be downloaded
    threads_to_be_downloaded = list()
    for thread in modified_and_new_threads:
        if thread['replies'] >= chv_config.minimum_replies_before_download:
            threads_to_be_downloaded.append(thread)

    for thread_index, thread in enumerate(threads_to_be_downloaded):
        # download the thread
        try:
            download_thread(thread['board_name'], thread['no'], db_connections[thread['board_name']])
            print(f'[{thread_index + 1}/{len(threads_to_be_downloaded)}] downloaded /{thread["board_name"]}/thread/{thread["no"]}', flush=True)
            time.sleep(random.uniform(wait_time/2, wait_time*3/2))

        except Exception as e:
            print(f'[{thread_index + 1}/{len(threads_to_be_downloaded)}] failed!    /{thread["board_name"]}/thread/{thread["no"]}', flush=True)
            print(e, flush=True)

            # check if thread was 404d
            time.sleep(2)
            request = get_url_custom(thread_url(thread['board_name'], str(thread["no"])))
            if request.status_code == 404:
                chv_database.four_o_four_thread(db_connections[thread['board_name']], [thread["no"]])
                print(f'[{thread_index + 1}/{len(threads_to_be_downloaded)}] 404d     /{thread["board_name"]}/thread/{thread["no"]}', flush=True)
            time.sleep(10)

    # remember kids, always close your db connections!
    for board_name in db_connections:
        db_connections[board_name].close()


def download_thread(board_name: str, thread_no: int, db_connection):
    request = get_url_custom(thread_url(board_name, str(thread_no)))
    thread_json: dict = json.loads(request.text)
    this_thread = dict()

    if 'posts' not in thread_json:
        return

    # op post_no is same as thread_no
    op_post_no = thread_no
    op_post_index = 0

    this_thread['thread'] = dict()
    if 'replies' in thread_json['posts'][op_post_index]:
        this_thread['replies'] = thread_json['posts'][op_post_index]['replies']
    if 'images' in thread_json['posts'][op_post_index]:
        this_thread['images'] = thread_json['posts'][op_post_index]['images']

    for post in thread_json['posts']:
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

        if 'filename' in post and 'ext' in post and 'tim' in post:
            this_post['file'] = content_url(board_name, str(post['tim']), str(post['ext']))
            this_post['tim'] = post['tim']
            this_post['filename'] = post['filename']
            this_post['ext'] = post['ext']

            # save thumbnail in folder
            thumbnail_file = pathlib.Path(f'html/thumbs/{board_name}/{post["no"]}.jpg')
            if not thumbnail_file.is_file():
                thumbnail = get_url_custom(thumbnail_url(board_name, post['tim']))
                # time.sleep(0.1)  # probably not needed since browsers load all instantly

                thumbnail_content = thumbnail.content
                with thumbnail_file.open('wb') as f:
                    f.write(thumbnail_content)

            # alternatively, save thumbnail in db
            # this_thread['thumbnail'] = base64.b64encode(thumbnail_content)

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
    if op_post_no in this_thread['thread']:
        op_post = this_thread['thread'][op_post_no]

        this_thread['last_modified'] = this_thread['thread'][last_post_no]['time']
        this_thread['no'] = op_post['no']

        if 'sub' in op_post:
            this_thread['sub'] = op_post['sub']

        if 'com' in op_post:
            this_thread['com'] = op_post['com']

    chv_database.save_thread(db_connection, this_thread)


def download_all_boards_wrapper(wait_time: float):
    while True:
        try:
            # get list of board names
            board_names = chv_config.boards_active
            if len(board_names) == 0:
                print(f'no active boards! Uncomment lines in main/chv_config.py!', flush=True)
                time.sleep(10)
                continue
            print(f'downloading: {", ".join([b[0] for b in board_names])}', flush=True)

            # download them all
            download_all_boards(board_names, wait_time)
            print('downloading: sleeping for a bit :)')
            time.sleep(20 * wait_time)

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

