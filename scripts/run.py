import view
import download

import time
import sys
import threading
import os


def main():
    board_names = list()
    with open('boards.txt', 'r') as f:
        lines = f.read().splitlines()

        for line in lines:
            if line != '':
                board_names.append(line)
                
    print('\n' + '-' * 40 + '\n', end = '')
    print('4CHV: a viewer for a more civilized age ')
    print(f'selected boards {board_names}')
    print('\n' + '-' * 40 + '\n', end = '')
    print('leave this script running in the background to keep')
    print('downloading threads and updating the html files')
    print('\n' + '-' * 40 + '\n', end = '')
    sys.stdout.flush()

    # delete old html files
    for f in os.listdir('.'):
        if f.endswith(".html"):
            os.remove(os.path.join('.', f))

    # download boards
    wait_time = 2
    download_thread = threading.Thread(
        target=download.get_boards_wrapper,
        args=(
            board_names,
            wait_time
        )
    )
    download_thread.start()

    # create board pages
    max_threads_per_board = 400
    wait_time_integer = 10
    while True:
        for board_name in board_names:
            view.make_html(
                board_name,
                max_threads_per_board
            )

            time.sleep(wait_time_integer)


if __name__ == '__main__':
    main();

