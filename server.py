#!/usr/local/bin/python3
import os, glob, codecs, json, threading, time, sys

from watchdog import observers
from watchdog import events
import flask
from flask import request

import searcher

def main():
  DIR_PATH_NOTES = os.path.expanduser("~/Dropbox/tbrush_notes")
  PORT = 38906

  dir_path = os.path.expanduser(DIR_PATH_NOTES)
  search_inst = searcher.Searcher(dir_path)

  app = flask.Flask(__name__)
  port = int(sys.argv[1]) if len(sys.argv) == 2 else PORT
  print('Starting httpserver on port', PORT)

  @app.route('/search', methods=['POST'])
  def search():
    post_dict = request.get_json()
    query_string = post_dict['query']
    selected_index = post_dict.get('selected_index')
    if selected_index is not None:
      selected_index = int(selected_index)
    print('searching for:', query_string)
    result_dict = search_inst.search(query_string, selected_index)
    print('results:', result_dict)
    return json.dumps(result_dict, indent=2)

  def monitor_filesystem():
    class MyHandler(events.PatternMatchingEventHandler):
      patterns = ["*.txt"]

      def on_any_event(self, event):
        if event.event_type == 'moved' or event.event_type == 'deleted':
          search_inst.delete_path(event.src_path)

        if event.event_type == 'moved':
          search_inst.load_path(event.dest_path)

        if event.event_type == 'created' or event.event_type == 'modified':
          search_inst.load_path(event.src_path)

    event_handler = MyHandler()
    observer = observers.Observer()
    observer.schedule(event_handler, path=DIR_PATH_NOTES, recursive=False)
    observer.start()

    print('monitoring:', DIR_PATH_NOTES)

    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      observer.stop()
    observer.join()

  t = threading.Thread(target=monitor_filesystem)
  t.daemon = True  # allow parent process to kill it
  t.start()

  app.jinja_env.auto_reload = True
  app.config['TEMPLATES_AUTO_RELOAD'] = True
  app.run(host='0.0.0.0', port=port, debug=(port != 80))

if __name__ == '__main__':
  main()
