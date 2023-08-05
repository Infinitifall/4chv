import view
import download

import time
import sys
import threading
import pathlib


def main():
    
    # pretty (ugly) print console message
    print('-' * 40)
    print('4CHV: a viewer for a more civilized age ')
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
    download_thread = threading.Thread(target=download.get_boards_wrapper, args=[wait_time])
    download_thread.start()

    # create a new thread to create html pages for the boards
    max_threads_per_board = 300
    wait_time_integer = 10
    download_thread = threading.Thread(target=view.make_html_wrapper, args=[wait_time, max_threads_per_board])
    download_thread.start()


if __name__ == '__main__':
    main();

