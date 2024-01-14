# 4CHV

A 4chan downloader/viewer. Downloads threads and builds offline html pages for a /comfy/ browsing experience.

- Catalog view
- Nested replies
- Threads posts ordered by quality
- Fly through posts with keyboard shortcuts
- Tiny download size (1MB)

## Install

- **Windows**
  1. Have [Python](https://www.python.org/downloads/) installed
  2. Download the latest version of 4CHV [from here](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip it
  3. Double click on `run_on_windows.bat`


- **Linux/BSD/macOS**

  ```bash
  # clone repo
  git clone https://github.com/Infinitifall/4chv
  cd 4chv

  # run
  ./run_on_linux.sh
  ```


## Screenshots

![screenshot](resources/screenshot2.png)

![screenshot](resources/screenshot.png)

![screenshot](resources/screenshot3.png)


## Usage

After following the install instructions above, you can keep 4chv running in the background whenever and however long you like. While running it will

1. Keep downloading new threads
2. Keep updating the board html files

Open the board html files in your web browser :)


## FAQs

- **Choose which /boards/ to download**
  - Uncomment your boards in [scripts/chv_boards.py](./scripts/chv_boards.py) (remove the `#` character at the start of the line)

- **Slow downloads?**
  - A new thread is downloaded every 2 seconds
  - You will have to wait 5 min the very first time you run 4chv to see a good number of threads

- **Post quality**
  - 4chv automatically sorts threads and replies by quality ("points" and "+"s)
    - "points" depend on the uniqueness of the words used in the post
    - "+"s depend on the quality of the replies to the post

- **Where threads are stored**
  - Threads are downloaded to the `threads` folder as SQLite files
  - They can be deleted or even copied it to another installation of 4chv

- **How to uninstall 4CHV**
  - Simply delete the `4chv` folder (everything is contained inside)
