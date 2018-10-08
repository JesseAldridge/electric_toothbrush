#!/usr/local/bin/python3
import os, glob, codecs, json, threading, time, sys

from watchdog import observers
from watchdog import events
import flask
from flask import request

import config

def main():
  dir_path = os.path.expanduser(config.DIR_PATH_NOTES)

  def score(query_string, basename):
    if query_string in basename:
      return len(query_string) / float(len(basename)) * 10

    tokens = query_string.split()
    return len([1 for token in tokens if token in basename])

  def path_to_basename(path):
    return os.path.splitext(os.path.basename(path))[0]

  def load_path(path):
    basename = path_to_basename(path)
    with open(path) as f:
      basename_to_content[basename] = f.read()

  print('loading files...')
  basename_to_content = {}
  glob_path = os.path.join(dir_path, '*.txt')
  for path in glob.glob(glob_path):
    load_path(path)
  print('loaded {} files'.format(len(basename_to_content)))


  app = flask.Flask(__name__)
  port = int(sys.argv[1]) if len(sys.argv) == 2 else config.PORT
  print('Starting httpserver on port', config.PORT)

  @app.route('/search', methods=['POST'])
  def search():
    post_dict = request.get_json()

    matched_basenames = []
    query_string = post_dict['query']
    selected_index = post_dict.get('selected_index')
    if selected_index is not None:
      selected_index = int(selected_index)

    terms = set(query_string.lower().split())
    for basename, content in basename_to_content.items():
      for term in terms:
        if term not in basename and term not in content.lower():
          break
      else:
        matched_basenames.append(basename)

    matched_basenames.sort(key=lambda basename: score(query_string, basename), reverse=True)

    max_matches = 10
    matched_basenames = matched_basenames[:max_matches]
    scores = [score(query_string, basename) for basename in matched_basenames]

    selected_content = None
    if(
      selected_index is not None and
      matched_basenames and
      selected_index < len(matched_basenames)
    ):
      selected_content = basename_to_content[matched_basenames[selected_index]]

    json_out = json.dumps({
      "matched_basenames": matched_basenames[:max_matches],
      "scores": scores,
      "is_more": len(matched_basenames) > max_matches,
      "selected_content": selected_content,
    }, indent=2)

    return json_out

  def monitor_filesystem():
    class MyHandler(events.PatternMatchingEventHandler):
      patterns = ["*.txt"]

      def on_any_event(self, event):
        if event.event_type == 'moved' or event.event_type == 'deleted':
          old_basename = path_to_basename(event.src_path)
          del basename_to_content[old_basename]

        if event.event_type == 'moved':
          load_path(event.dest_path)

        if event.event_type == 'created' or event.event_type == 'modified':
          load_path(event.src_path)

    event_handler = MyHandler()
    observer = observers.Observer()
    observer.schedule(event_handler, path=config.DIR_PATH_NOTES, recursive=False)
    observer.start()

    print('monitoring:', config.DIR_PATH_NOTES)

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
