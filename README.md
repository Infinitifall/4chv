# 4CHV

A 4chan downloader/viewer. Downloads threads and builds offline HTML pages for a /comfy/ browsing experience.

- Catalog view
- Nested replies
- Threads and posts ordered by quality
- Fly through posts with keyboard shortcuts
- Tiny download size (1MB)


## Install

- **Windows**
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

## Usage

Once 4CHV is running, HTML files will be created in `html/`. Open these in your web browser.

While running, threads are downloaded every few seconds and HTML files are updated every few minutes. It can be kept running in the background, run intermittently or run whenever you wish.


## Screenshots

![screenshot](screenshots/screenshot2.png)

![screenshot](screenshots/screenshot.png)

![screenshot](screenshots/screenshot3.png)


## FAQs

- **How to choose which /boards/ to download?**

  Uncomment lines in [main/custom/chv_boards.py](./main/custom/chv_boards.py) by removing the leading `#`

- **Where are threads downloaded?**
  - Threads are saved in sqlite files in `threads/`
  - Thumbnails are downloaded to `html/thumbs/`

- **What are points and +?**

  Threads and replies are ordered by "quality"
    - `points` measure the uniqueness of words used in a post
    - `+` measure the quality of the replies to a post

- **How to delete all threads and thumbnails?**
  - Delete `.sqlite` files in `threads/`
  - Delete `html/thumbs/`
  - Restart 4CHV

- **How to uninstall 4CHV?**

  Simply delete the entire `4chv/` folder. Everything is contained inside.


## Contribute

- Report bugs or make suggestions in "Issues"
- All contributions are welcome! Create a fork and pull request.