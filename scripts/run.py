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
    download_wait_time = 2
    download_thread = threading.Thread(target=download.get_boards_wrapper, args=[download_wait_time])

    # create a new thread to create html pages for the boards
    view_max_threads_per_board = 300
    view_wait_time = 10
    view_thread = threading.Thread(target=view.make_html_wrapper, args=[view_wait_time, view_max_threads_per_board])
    
    # run the threads
    while True:
        if not download_thread.is_alive():
            print("Started download_thread")
            sys.stdout.flush()
            download_thread.start()
        
        if not view_thread.is_alive():
            print("Started view_thread")
            sys.stdout.flush()
            view_thread.start()
        
        time.sleep(60)


if __name__ == '__main__':
    main();

