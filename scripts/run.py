import view
import download

import time
import sys
import threading
import pathlib


def main():
    # get list of board names from boards.txt
    board_names = list()
    with open('boards.txt', 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            if line != '':
                board_names.append(line)
    
    # pretty (ugly) print console message
    print('-' * 40)
    print('4CHV: a viewer for a more civilized age ')
    print(f'selected boards {board_names}')
    print('-' * 40)
    print('leave this script running in the background to keep')
    print('downloading threads and updating the html files')
    print('-' * 40)
    sys.stdout.flush()

    # delete old html files
    for each_file in pathlib.Path('.').glob('*.html'):
        each_file.unlink()

    # create a new thread to download threads
    wait_time = 2
    download_thread = threading.Thread(target=download.get_boards_wrapper, args=(board_names, wait_time ))
    download_thread.start()

    # cycle through boards, creating html pages
    max_threads_per_board = 300
    wait_time_integer = 10
    while True:
        for board_name in board_names:
            view.make_html_wrapper(board_name, max_threads_per_board)
            time.sleep(wait_time_integer)


if __name__ == '__main__':
    main();

