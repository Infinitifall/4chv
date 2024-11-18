import sys
import pathlib
import time
import threading

# local imports
import chv_view
import chv_download
import chv_config


def main():

    # display pretty (ugly) start message
    print(chv_config.pretty_ugly_start_message)
    sys.stdout.flush()

    # thread to download threads
    download_thread = threading.Thread(
        target=chv_download.download_all_boards_wrapper,
        args=[
            chv_config.download_wait_time
        ]
    )

    # thread to create boards html pages
    view_thread = threading.Thread(
        target=chv_view.make_html_wrapper,
        args=[
            chv_config.view_wait_time,
            chv_config.view_max_threads_per_board
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
    main()

