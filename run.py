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
    
    print('4CHV: A viewer for a more civilized age ')
    print(f'Boards selected: {board_names} (from boards.txt)')
    print('Starting downloads')

    thread_list = list()

    # download boards
    wait_time = len(board_names) * 2
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
        time.sleep(3)
    
    # create board pages
    max_threads_per_board = 200
    wait_time_between_builds = 300
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
        time.sleep(random.randint(20,30))


if __name__ == '__main__':
    main();

