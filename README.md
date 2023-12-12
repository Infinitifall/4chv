# 4CHV

A 4chan downloader/viewer for a more civilized age.

Downloads threads and builds offline html pages for a /comfy/ browsing experience.

- Catalog view
- Nested reply threads
- Posts are assigned points and sorted based on quality
- Tiny download size (1MB)


![screenshot](resources/screenshot2.png)

![screenshot](resources/screenshot.png)


## Install on Windows

1. Have [Python](https://www.python.org/downloads/) installed
2. [Download 4CHV](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip the folder
3. Double click on `run_on_windows.bat`


## Install on Linux/macOS/BSD

```bash
# verify python is installed
python3 --version

# clone repo
git clone https://github.com/Infinitifall/4chv
cd 4chv

# run
./run_on_linux.sh
```

## FAQs

- **How do I use 4CHV?**
  - Follow the "install" instructions above
  - Keep the program running in the background, it will download threads and update the html files
  - Open any of the html files in your browser

- **How to change what boards are downloaded?**
  - Edit the `boards.txt` file, add one board per line

- **Why is downloading so slow?**
  - A new thread is downloaded every 2 seconds (to stay within the api rate limit)
  - Unfortunately this means you will have to wait 5 min the first time you run this program

- **How is post quality calculated?**
  - 4chv automatically sorts threads and replies by "quality"
  - Quality is calculated in terms of "points" and "+"s
  - The "points" depends on the uniqueness of the words used in a post
  - The "+"s depends on the quality the replies to a post

- **How to uninstall 4CHV?**
  - Just delete the `4CHV` folder, everything is inside it


