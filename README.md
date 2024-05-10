# 4CHV

A 4chan downloader/viewer. Downloads threads and builds offline HTML pages for a /comfy/ browsing experience.

- Catalog view with nested replies
- Threads and posts ordered by quality
- Keyboard shortcuts
- Tiny download size (1MB)


## Install

- **Windows (without Git)**
  1. Have [Python](https://www.python.org/downloads/) installed (can check by running `python --version` in cmd)
  2. Download the [latest version of 4CHV](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip
  3. Double click to run `run_on_windows.bat`


- **Linux/BSD/macOS**

  ```bash
  # clone repo
  git clone https://github.com/Infinitifall/4chv
  cd 4chv

  # run
  ./run_on_linux.sh
  ```


## Screenshots

![screenshot](screenshots/screenshot2.png)

![screenshot](screenshots/screenshot.png)

![screenshot](screenshots/screenshot3.png)


## Usage

Once 4CHV is running, HTML files will be created in `html/`. Open these in your web browser.

While running, threads are downloaded every few seconds and HTML files are updated every few minutes. It can be kept running in the background, run intermittently or run whenever you wish.


- **How to configure 4chv?**

  Config files are located in `main/custom/`
  - [chv_boards.py](./main/custom/chv_boards.py): choose /boards/ to download (remove leading `#`)
  - [chv_params.py](./main/custom/chv_params.py): all other config

- **Where are threads downloaded?**
  - `threads/`: threads stored as sqlite files
  - `html/thumbs/`: thumbnails stored as png files

- **What is thread, post quality?**

  Threads and replies are ordered by "quality"
    - `points` measure the uniqueness of words used in a post
    - `+` measure the quality of the replies to a post

- **How to delete all downloaded threads, thumbnails?**
  - Stop 4chv if it is running
  - Delete the folders:
    - `threads/`
    - `html/thumbs/`

- **How to uninstall 4CHV?**

  Delete the entire `4chv/` folder


## Contribute

- Report bugs or make suggestions in "Issues"
- All contributions are welcome! Create a fork and pull request.