# 4CHV

A 4chan downloader/viewer for a more civilized age. Downloads threads and builds offline html pages for a /comfy/ browsing experience.

- Catalog view, nested replies
- Threads and replies are assigned points and sorted based on quality
- Tiny download size (1MB)


# Run on Windows

1. Have [Python](https://www.python.org/downloads/) installed
2. [Download this project](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip the folder
3. Double click on `run_on_windows.bat`


# Run on Linux/macOS/BSD

```bash
git clone https://github.com/Infinitifall/4chv
cd 4chv
./run_on_linux.sh
```


# Screenshots

![screenshot](resources/screenshot.png)

![screenshot](resources/screenshot2.png)


# FAQs

### What is this program doing?

It downloads threads from [4chan's public api](https://github.com/4chan/4chan-API) to a `threads` folder and creates html files such as `sci.html` and `g.html` which you can view in your browser.


### How do I add/remove boards?

Edit the `boards.txt` file and add one board per line.


### Why is downloading so slow?

A new thread is downloaded every two seconds, which is within 4chan's api rate limit. Unfortunately this means you will have to wait a few minutes the very first time to see a good number of threads.


### How is quality calculated?

Threads and replies are sorted on the basis of points and the amount of discussion they generate. The points a thread or reply gets depends on its words - unique words get higher points, common words get lower points. Points are also (invisibly) added from quote replies. Low quality replies are minimized by default, providing a distraction free browsing experience.


### How do I uninstall this?

Simply delete the folder, everything is self contained.

