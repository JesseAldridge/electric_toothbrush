import os, glob

class Match:
  def __init__(self, basename):
    self.term_to_score = {}
    self.basename =  basename

class Searcher:
  def __init__(self, dir_path):
    print('loading files...')
    self.basename_to_content = {}
    self.basename_to_content_lower = {}
    glob_path = os.path.join(dir_path, '*.txt')
    for path in glob.glob(glob_path):
      self.load_path(path)
    print('loaded {} files'.format(len(self.basename_to_content)))

  def path_to_basename(self, path):
    return os.path.splitext(os.path.basename(path))[0]

  def delete_path(self, path):
    old_basename = self.path_to_basename(path)
    del self.basename_to_content[old_basename]
    del self.basename_to_content_lower[old_basename]

  def load_path(self, path):
    basename = self.path_to_basename(path)
    with open(path) as f:
      self.basename_to_content[basename] = f.read()
    self.basename_to_content_lower[basename] = self.basename_to_content[basename].lower()

  def score(self, query_string, match):
    if query_string == match.basename:
      return 100

    doc_score = 0
    for term, term_score in match.term_to_score.items():
      if term in self.term_to_doc_count:
        # weight rare words more heavily
        doc_score += term_score / self.term_to_doc_count[term]
    return doc_score

    # if query_string in match.basename:
    #   return len(query_string) / float(len(match.basename)) * 10 + match.order_count

    # tokens = query_string.split()
    # return len([1 for token in tokens if token in match.basename])

  def search(self, query_string, selected_index):
    terms = query_string.lower().split()

    matches = []
    self.term_to_doc_count = {}
    for basename, content_lower in self.basename_to_content_lower.items():
      remaining_basename = basename
      remaining_content = content_lower

      match = Match(basename)
      for term in terms:
        term_score = 0
        self.term_to_doc_count.setdefault(term, 0)

        if term in basename or term in content_lower:
          self.term_to_doc_count[term] += 1

          # matches in the title are more important
          if term in basename:
            term_score += 10
          else:
            term_score += 1

          # token order bonus
          if term in remaining_basename:
            term_score += 1
            remaining_basename = remaining_basename.split(term, 1)[1]
          if term in remaining_content:
            term_score += 1
            remaining_content = remaining_content.split(term, 1)[1]
          match.term_to_score[term] = term_score

      if match.term_to_score:
        matches.append(match)

    matches.sort(key=lambda match: self.score(query_string, match), reverse=True)

    max_matches = 10
    is_more = len(matches) > max_matches
    matches = matches[:max_matches]
    scores = [self.score(query_string, match) for match in matches]

    selected_content = None
    if selected_index is not None and matches and selected_index < len(matches):
      selected_content = self.basename_to_content.get(matches[selected_index].basename)

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
    # exact matches are more important
    ('x', ['x', 'x y z']),
  ]:
    print('---query---:', query)
    results = searcher.search(query, 0)
    print('results:', results)
    assert results['matched_basenames'] == expected_basenames
