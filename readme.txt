Installation
---

Something like this:
```
git clone git@github.com:JesseAldridge/electric_toothbrush.git
cd electric_toothbrush
pip install -r requirements.txt
# symlink the client
ln -s /Users/jesse_aldridge/Dropbox/electric_toothbrush/client.py /usr/local/bin/t
# symlink the server
ln -s /Users/jesse_aldridge/Dropbox/electric_toothbrush/server.py /usr/local/bin/etoothbrush_server
```

Set DIR_PATH_NOTES in config.py to the directory that you will use to store your notes.

Usage
---

Run the server:
`python serve.py`

In another terminal, run the client:
`t`

Just start typing to search your notes.
Press the up/down arrows to select a note.
Hit return to either open the matching file or create a new file if there are no matches.

ctrl+n will also create a new note from the current query

License
---
MIT
