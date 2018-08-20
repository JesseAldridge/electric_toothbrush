#!/usr/bin/python
import sys, tty, termios, subprocess, os, json, glob, time

import requests

import config

def getch():
  # Return a single character from stdin.

  fd = sys.stdin.fileno()
  old_settings = termios.tcgetattr(fd)
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
  return ch

def open_selected():
  if selected_index is None:
    for i in range(len(matched_basenames)):
      open_index(i)
    return
  open_index(selected_index)

def open_index(index, matched_basenames):
  basename = matched_basenames[index]
  path = os.path.join(config.DIR_PATH_NOTES, basename) + '.txt'
  open_path(path)

def open_path(path):
  print 'opening:'
  print '"{}"'.format(path)
  subprocess.call(['open', path])

def new_note(query_string):
  new_path = os.path.join(config.DIR_PATH_NOTES, query_string) + '.txt'
  if not os.path.exists(new_path):
    with open(new_path, 'w') as f:
      f.write('')
  open_path(new_path)

def adjust_selected_index(amount, selected_index, matched_basenames):
  if not matched_basenames:
    selected_index = None
    return

  if selected_index is None:
    selected_index = 0
  else:
    selected_index += amount
  selected_index %= min(len(matched_basenames), 10)
  return selected_index

def main_loop():
  # Load notes and saved_query.

  if not os.path.exists(config.DIR_PATH_META):
    os.mkdir(config.DIR_PATH_META)

  query_string = ' '.join(sys.argv[1:])
  query_path = os.path.join(config.DIR_PATH_META, 'saved_query.txt')
  if not query_string.strip() and os.path.exists(query_path):
    with open(query_path) as f:
      query_string = f.read()

  # Wait for a key, build up the query string.

  is_first_key = True
  selected_index = None
  while True:
    post_json = json.dumps({'query': query_string, 'selected_index': selected_index})
    for _ in range(2):
      try:
        resp = requests.post('http://127.0.0.1:{}'.format(config.PORT), data=post_json)
      except requests.exceptions.ConnectionError:
        server_path = os.path.join(os.path.dirname(__file__), 'etoothbrush_server')
        print 'failed to connect, launching server:', server_path, '...'
        subprocess.Popen(['nohup', server_path],
                         stdout=open('/dev/null', 'w'),
                         stderr=open('etoothbrush_err.log', 'a'),
                         preexec_fn=os.setpgrp
                         )
        time.sleep(3)
      else:
        break

    print '\nquery: [{}]\n'.format(query_string)

    if resp.status_code != 200:
      print 'error from server'
      print 'resp.content:', resp.content
      break

    resp_dict = resp.json()
    selected_content = resp_dict.get('selected_content')
    matched_basenames = resp_dict.get('matched_basenames') or []

    for i, basename in enumerate(matched_basenames):
      print '{}{}'.format('> ' if i == selected_index else '  ', basename)
      if i == selected_index:
        lines = selected_content.splitlines()
        lines = lines[:10] + (['...'] if len(lines) > 10 else [])
        indented_lines = ['    ' + line for line in lines]
        content_preview = '\n'.join(indented_lines)
        print content_preview

    ch = getch()

    if ord(ch) == 3:  # ctrl+c
      raise KeyboardInterrupt
    elif ord(ch) == 14:  # ctrl+n
      new_note(query_string)
    elif ord(ch) == 23:  # ctrl+w
      stripped = query_string.strip()
      query_string = (stripped.rsplit(' ', 1)[0] + ' ') if ' ' in stripped else ''
    elif ord(ch) == 127:  # backspace
      query_string = query_string[:-1]
    elif ord(ch) == 13:  # return
      if selected_index is None or selected_index >= len(matched_basenames):
        new_note(query_string)
      else:
        open_index(selected_index, matched_basenames)
      break
    elif ord(ch) == 27:  # esc code
      ch = getch() # skip the [
      ch = getch()
      if ord(ch) == 66 or ord(ch) == 65: # up/down arrows
        selected_index = adjust_selected_index(
          1 if ord(ch) == 66 else -1,
          selected_index,
          matched_basenames,
        )
    else:
      if is_first_key:
        query_string = ''
      query_string += ch

    is_first_key = False

    with open(query_path, 'w') as f:
      f.write(query_string)

if __name__ == '__main__':
  main_loop()
