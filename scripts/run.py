import view
import download

import time
import sys
import threading


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

    thread_list = list()

    # download boards
    wait_time_integer = 2
    wait_time = len(board_names) * wait_time_integer
    for board_name in board_names:
        t = threading.Thread(
            target=download.get_board_wrapper,
            args=(
                board_name,
                wait_time
            )
        )
        t.start()
        thread_list.append(t)
        time.sleep(wait_time_integer)

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

