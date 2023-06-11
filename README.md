# 4CHV

A 4chan viewer for a more civilized age. This downloads threads to a folder and builds offline html pages for a /comfy/ browsing experience.

- Threads and posts are assigned points and arraged based on quality*
- Catalog view
- Nested replies
- Highly minimal and dependency free, works on all platforms

\*quality is subjective

## Installation for Windows

1. Install Python if you haven't already from [here](https://www.python.org/downloads/)

2. Download this project [here](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip the folder

3. Open `boards.txt` and add/remove the boards you want, keeping one board per line

4. Double click on the `run.py` file to start the script

It will start downloading threads and creating html files which you can open in your browser. New threads are downloaded every two seconds, so you may have to wait for a few minutes the first time. 


## Screenshots

![screenshot](resources/screenshot.png)


![screenshot](resources/screenshot2.png)


## Installation for Linux

```bash
git clone https://github.com/Infinitifall/4chv
cd 4chv

# edit boards.txt with the boards you want, keeping one board per line

# run 
python run.py
```

## Advanced usage

```bash
# download only threads from /g/, one every 5 seconds
python scripts/download.py "g" 5

# only build sci.html with the latest 300 posts, every 10 seconds
python scripts/view.html "sci" 300 10
```
