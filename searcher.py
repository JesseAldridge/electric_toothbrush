import os, glob

class Match:
  def __init__(self, basename, order_match):
    self.basename =  basename
    self.order_match = order_match

class Searcher:
  def __init__(self, dir_path):
    def path_to_basename(path):
      return os.path.splitext(os.path.basename(path))[0]

    def load_path(path):
      basename = path_to_basename(path)
      with open(path) as f:
        self.basename_to_content[basename] = f.read()

    print('loading files...')
    self.basename_to_content = {}
    glob_path = os.path.join(dir_path, '*.txt')
    for path in glob.glob(glob_path):
      load_path(path)
    print('loaded {} files'.format(len(self.basename_to_content)))

  def score(self, query_string, match):
    if query_string in match.basename:
      return len(query_string) / float(len(match.basename)) * 10 + match.order_match

    tokens = query_string.split()
    return len([1 for token in tokens if token in match.basename])

  def search(self, query_string, selected_index):
    terms = set(query_string.lower().split())

    matches = []
    for basename, content in self.basename_to_content.items():
      remaining_basename = basename.lower()
      remaining_content = content_lower = content.lower()
      order_match = 0

      for term in terms:
        if term in basename or term in content_lower:
          if term in remaining_basename or term in remaining_content:
            order_match += 1
            if term in remaining_basename:
              remaining_basename = remaining_basename.split(term, 1)[1]
            else:
              remaining_content = remaining_content.split(term, 1)[1]
        else:
          break
      else:
        matches.append(Match(basename, order_match))

    matches.sort(key=lambda match: self.score(query_string, match), reverse=True)

    max_matches = 10
    is_more = len(matches) > max_matches
    matches = matches[:max_matches]
    scores = [self.score(query_string, match) for match in matches]

    selected_content = None
    if selected_index is not None and matches and selected_index < len(matches):
      selected_content = self.basename_to_content[matches[selected_index].basename]

    matched_basenames = [match.basename for match in matches]

    return {
      "matched_basenames": matched_basenames,
      "scores": scores,
      "is_more": is_more,
      "selected_content": selected_content,
    }

if __name__ == '__main__':
  searcher = Searcher('test_notes')
  for query, expected_basenames in [
    # if a query doesn't match, should return no results
    ('non-matching-query', []),
     # prefer title to body matches
    ('foo bar', ['foo bar baz', 'bar foo baz', 'estimates (estimation)']),
    # order matters
    ('bar foo', ['bar foo baz', 'foo bar baz', 'estimates (estimation)']),
    # matches against content
    ('zzz', ['something else']),
  ]:
    results = searcher.search(query, 0)
    print('results:', results)
    assert results['matched_basenames'] == expected_basenames
