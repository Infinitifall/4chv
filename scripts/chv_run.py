import sys
import pathlib
import time
import threading

# local imports
import chv_view
import chv_download


def main():

    # pretty (ugly) print console message
    print('-' * 50)
    print('4CHV: a viewer for a more civilized age ')
    print('-' * 50)
    print('Leave this running in the background for')
    print('however long you like. While running, it will')
    print('1. Keep downloading new threads')
    print('2. Keep updating the board html files')
    print('')
    print('Open the board html files in your web browser :)')
    print('-' * 50)
    sys.stdout.flush()

    # thread to download threads
    download_wait_time = 2
    download_thread = threading.Thread(
        target=chv_download.download_all_boards_wrapper,
        args=[
            download_wait_time
        ]
    )

    # thread to create boards html pages
    view_max_threads_per_board = 300
    view_wait_time = 300
    view_thread = threading.Thread(
        target=chv_view.make_html_wrapper,
        args=[
            view_wait_time,
            view_max_threads_per_board
        ]
    )

    while True:
        print("checking if threads are alive...")

        if not download_thread.is_alive():
            print("started download_thread")
            download_thread.start()

        if not view_thread.is_alive():
            print("started view_thread")
            view_thread.start()

        sys.stdout.flush()
        time.sleep(300)


if __name__ == '__main__':
    main();

