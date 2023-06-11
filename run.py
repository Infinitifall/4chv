import subprocess
import sys


def pip_install_requests():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])


if __name__ == '__main__':
    pip_install_requests()
    print('\n' * 20)


import scripts.view
import scripts.download

import time
import random
import threading


def main():
    board_names = list()
    with open('boards.txt', 'r') as f:
        lines = f.read().splitlines()

        for line in lines:
            if line != '':
                board_names.append(line)
    
    print('4CHV: a viewer for a more civilized age ')
    print(f'selected boards {board_names}')
    print('')
    print('leave this script running in the background to keep')
    print('downloading threads and updating the html files')
    print('')

    thread_list = list()

    # download boards
    wait_time_integer = 2
    wait_time = len(board_names) * wait_time_integer
    for board_name in board_names:
        t = threading.Thread(
            target=scripts.download.get_board_wrapper,
            args=(
                board_name,
                wait_time
            )
        )
        t.start()
        thread_list.append(t)
        time.sleep(random.randint(1, wait_time_integer))
    
    # create board pages
    max_threads_per_board = 400
    wait_time_between_builds = 10
    for board_name in board_names:
        t = threading.Thread(
            target=scripts.view.make_html,
            args=(
                board_name,
                max_threads_per_board,
                wait_time_between_builds
            )
        )
        t.start()
        thread_list.append(t)
        time.sleep(random.randint(1, wait_time_between_builds))


if __name__ == '__main__':
    main();

