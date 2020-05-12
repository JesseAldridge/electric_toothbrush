Installation
---

Something like this:
```
git clone git@github.com:JesseAldridge/electric_toothbrush.git
cd electric_toothbrush

# install dependencies
go get github.com/atotto/clipboard
go get github.com/gdamore/tcell
go get github.com/rivo/tview

# build the client
go build client.go

# move the client onto your path
mv client /usr/local/bin/td

# install the server requirements
pip3 install -r requirements.txt
```

Set `dir_path` in client.go and `DIR_PATH_NOTES` in server.py to the directory that you will use to
store your notes.

By default it's "~/Dropbox/tbrush_diagrams"

Usage
---

Run the server (I like to just leave it running in a minimized terminal window.)
`python3 server.py`

In another terminal, run the client:
`t`

Just start typing to search your notes.
Press the up/down arrows to select a note.
Press return to open the selected note or create a new note.

License
---
MIT
