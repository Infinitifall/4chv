# 4CHV

A 4chan downloader/viewer for a more civilized age. Builds offline html pages for a /comfy/ browsing experience.

- Catalog view, nested replies
- Threads and replies are assigned points and sorted based on quality
- Tiny download size (1MB)


# Run on Windows

1. Have [Python](https://www.python.org/downloads/) installed
2. [Download this project](https://github.com/Infinitifall/4chv/archive/refs/heads/main.zip) and unzip the folder
3. Double click on `run_on_windows.bat`

This will start downloading threads and creating local html files which you can open in your browser. New threads are downloaded every two seconds, so you'll have to wait a few minutes the very first time.


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

- **What is this program doing?**

  It downloads threads from [4chan's public api](https://github.com/4chan/4chan-API) to a `threads` folder and creates html files such as `sci.html` and `g.html` which you can view in your browser.


- **How do I add boards?**

  Edit the `boards.txt` file and add one board per line.


- **Why is downloading so slow?**

  A new thread is downloaded every two seconds, which is within 4chan's api rate limit. Unfortunately this means you will have to wait a few minutes the very first time to see a good number of threads.


- **How is quality calculated?**

  Threads and replies are sorted on the basis of points and the amount of discussion they generate. The points a thread or reply gets depends on the words it uses, with unique words getting higher points and common words getting lower points. Points are also recursively added from replies. Low quality replied are minimized.


- **How do I uninstall this?**

  Simply delete the folder, everything is self contained.

