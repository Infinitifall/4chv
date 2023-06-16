# 4CHV

A 4chan downloader/viewer for a more civilized age. Builds offline html pages for a /comfy/ browsing experience.

- Threads and posts are assigned points based on quality\*
- High quality\* posts on top, low quality\* replies hidden
- Catalog view, nested replies
- Highly minimal

\*see bottom for explanation on how quality is calculated

# Installation for Windows

1. Install [Python](https://www.python.org/downloads/) if you haven't already, then [download this project](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip the folder
2. Edit `boards.txt` and with the boards you want, one board per line
3. Double click on the `run.py` file to start the program

This will start downloading threads and creating html files which you can open in your browser. New threads are downloaded every two seconds, so you'll have to wait a minute the first time.


# Screenshots

![screenshot](resources/screenshot.png)


![screenshot](resources/screenshot2.png)


# Installation for Linux/macOS/BSD

First time setup involves cloning the repo and creating a [virtualenv](https://docs.python.org/3/tutorial/venv.html)

```bash
git clone https://github.com/Infinitifall/4chv
cd 4chv
python -m venv myvenv
```

Running the script hereafter is as simple as activating the venv and running `run.py`

```bash
source myvenv/bin/activate
python run.py

# when you are done
deactivate
```


# Advanced usage

You can individually download and build boards insteading of using the `run.py` wrapper

```bash
# download threads from /g/ every 5 seconds
python scripts/download.py "g" 5

# build sci.html with the latest 300 posts
python scripts/view.html "sci" 300
```

# How quality is calculated

- Each word is assigned points based on the frequency with which it appears on a board
- Common words get fewer points, unique words get higher points
- The points a post gets is the sum of the points of each of its words, slightly averaged against its length
- Points are also recursively added from a post's replies
- This whole process is done independently for each board
