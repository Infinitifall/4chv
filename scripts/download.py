import sys
import pathlib
import time
import json
import re
import pickle
import base64

import requests


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
    }

    for key, value in clean_dict.items():
        content = re.sub(key, value, content, flags=re.IGNORECASE | re.MULTILINE)
    return content


def get_thread(board_name: str, thread_no: int):
    request = requests.get(thread_url(board_name, str(thread_no)))
    data: dict = json.loads(request.text)
    this_thread = dict()

    if 'posts' not in data:
        return this_thread
    
    op_post_no = data['posts'][0]['no']

    for post in data['posts']:
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
            if int(pred[1:]) not in this_thread:
                continue
            this_thread[int(pred[1:])]['succ'].append(post['no'])
        this_thread[post['no']] = this_post
            
    return this_thread


def get_board(board_name: str, wait_time: int):
    pathlib.Path(f'threads/{board_name}').mkdir(parents=True, exist_ok=True)

    request = requests.get(catalog_url(board_name))
    data: list = json.loads(request.text)
    this_board = dict()
    
    for page in data:
        page: dict

        if 'threads' not in page:
            continue
        
        for thread in page['threads']:
            thread: dict
            this_thread = dict()

            if 'replies' in thread:
                this_thread['replies'] = thread['replies']
            else:
                this_thread['replies'] = list()
            
            this_thread['thread'] = get_thread(board_name, thread['no'])
            
            op_post_no = min(this_thread['thread'])
            op_post = this_thread['thread'][op_post_no]
            if 'filename' in op_post and 'ext' in op_post and 'tim' in op_post:
                thumbnail = requests.get(
                    thumbnail_url(board_name, str(op_post['tim']))
                ).content
                this_thread['thumbnail'] = base64.b64encode(thumbnail)

            if 'sub' in op_post:
                this_thread['sub'] = op_post['sub']

            this_board[thread['no']] = this_thread
            
            with open(f'threads/{board_name}/' + str(thread['no']) + '.pkl', 'wb') as my_file:
                pickle.dump(this_thread, my_file)
            
            print(f'downloaded /{board_name}/thread/{thread["no"]}')
            time.sleep(wait_time)  # wait time between requests

    return this_board


def get_board_wrapper(board_name: str, wait_time: int):
    while True:
        try:
            get_board(board_name, wait_time)
        except Exception as e:
            print(e)
            print('something failed, trying again in 30s')
            time.sleep(30)


if __name__ == '__main__':
    try:
        assert(len(sys.argv) == 3)
        board_name = sys.argv[1]
        wait_time = int(sys.argv[2])

        get_board_wrapper(board_name, wait_time)

    except Exception as e:
        print('Usage: python download.py <board> <wait_time_between_requests>')
    
