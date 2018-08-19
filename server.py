#!/usr/bin/python
import BaseHTTPServer, os, glob, codecs, json, threading, time

from watchdog import observers
from watchdog import events

import config

def main():
  port = 8080
  dir_path = os.path.expanduser(config.DIR_PATH_NOTES)

  def score(basename, query_string):
    return 10 if query_string == basename else 0

  def path_to_basename(path):
    return os.path.splitext(os.path.basename(unicode(path, 'utf8')))[0]

  def load_path(path):
    basename = path_to_basename(path)
    with codecs.open(path, encoding='utf-8') as f:
      basename_to_content[basename] = f.read()
    basename_to_content_lower[basename] = basename_to_content[basename].lower()

  print 'loading files...'
  basename_to_content = {}
  basename_to_content_lower = {}
  glob_path = os.path.join(dir_path, '*.txt')
  for path in glob.glob(glob_path):
    load_path(path)
  print 'loaded {} files'.format(len(basename_to_content))

  class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
      content_length = int(self.headers['Content-Length'])
      post_dict = json.loads(self.rfile.read(content_length))

      matched_basenames = []
      query_string = unicode(post_dict['query'])
      selected_index = post_dict.get('selected_index')
      if selected_index is not None:
        selected_index = int(selected_index)

      terms = set(query_string.lower().split())
      for basename, content in basename_to_content_lower.iteritems():
        for term in terms:
          if term not in basename and term not in content:
            break
        else:
          matched_basenames.append(basename)

      matched_basenames.sort(key=lambda basename: score(query_string, basename), reverse=True)

      selected_content = None
      if selected_index is not None:
        selected_content = basename_to_content[matched_basenames[selected_index]]

      max_matches = 10
      json_out = json.dumps({
        "matched_basenames": matched_basenames[:10],
        "is_more": len(matched_basenames) > max_matches,
        "selected_content": selected_content,
      }, indent=2)

      self.send_response(200)
      self.send_header('Content-type', 'application/json')
      self.end_headers()
      self.wfile.write(json_out)

  def monitor_filesystem():
    class MyHandler(events.PatternMatchingEventHandler):
      patterns = ["*.txt"]

      def on_any_event(self, event):
        if event.event_type == 'moved' or event.event_type == 'deleted':
          old_basename = path_to_basename(event.src_path)
          del basename_to_content[old_basename]
          del basename_to_content_lower[old_basename]

        if event.event_type == 'moved':
          load_path(event.dest_path)

        if event.event_type == 'created' or event.event_type == 'modified':
          load_path(event.src_path)

    event_handler = MyHandler()
    observer = observers.Observer()
    observer.schedule(event_handler, path=config.DIR_PATH_NOTES, recursive=False)
    observer.start()

    print 'monitoring:', config.DIR_PATH_NOTES

    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      observer.stop()
    observer.join()

  t = threading.Thread(target=monitor_filesystem)
  t.daemon = True  # allow parent process to kill it
  t.start()

  server = BaseHTTPServer.HTTPServer(('', port), MyHandler)
  print 'Starting httpserver on port', port

  try:
    server.serve_forever()
  except KeyboardInterrupt:
    server.socket.close()

if __name__ == '__main__':
  main()
