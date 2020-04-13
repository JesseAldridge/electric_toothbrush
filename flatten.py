import os, shutil


def flatten_drawio_files(dir_path, parent_dir_names):
  print('flattening:', dir_path)
  for child_name in os.listdir(dir_path):
    child_path = os.path.join(dir_path, child_name)
    if os.path.isdir(child_path):
      flatten_drawio_files(child_path, parent_dir_names + [child_name])
    elif child_path.endswith('.drawio'):
      new_dir_path = os.path.expanduser('~/Dropbox/tbrush_diagrams')
      new_file_name = '_'.join(parent_dir_names + [child_name])
      target_path = os.path.join(new_dir_path, new_file_name)
      shutil.copyfile(child_path, target_path)

def main():
  root_dir_path = os.path.expanduser('~/Dropbox/diagrams')
  flatten_drawio_files(root_dir_path, [])

if __name__ == '__main__':
  main()
