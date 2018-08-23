# Based on: https://github.com/logicx24/Text-Search-Engine
# Described at: http://aakashjapi.com/fuckin-search-engines-how-do-they-work/

import re, math, glob, codecs, os

class BuildIndex:

  def __init__(self, paths):
    self.tf = {}
    self.df = {}
    self.idf = {}
    self.filenames = paths
    self.basename_to_content = {}
    self.file_to_terms = {}
    for path in paths:
      self.load_path(path)
    self.regdex = self.reg_index()
    self.totalIndex = self.execute()
    self.vectors = self.vectorize()
    self.mags = self.magnitudes(self.filenames)
    self.populate_scores()

  def path_to_basename(self, path):
    return os.path.splitext(os.path.basename(unicode(path, 'utf8')))[0]

  def load_path(self, path):
    basename = self.path_to_basename(path)
    with codecs.open(path, encoding='utf-8') as f:
      text = f.read()

    self.basename_to_content[basename] = text

    normalized_text = text.lower()

    # TODO: use re.split instead
    # "foo_bar   baz" -> "foo bar baz" -> ["foo", "bar", "baz"]
    between_words = re.compile(r'[\W_]+')
    normalized_text = between_words.sub(' ', normalized_text)
    self.file_to_terms[path] = normalized_text.split()

  #input = [word1, word2, ...]
  #output = {word1: [pos1, pos2], word2: [pos2, pos434], ...}
  def index_one_file(self, termlist):
    fileIndex = {}
    for index, word in enumerate(termlist):
      if word in fileIndex.keys():
        fileIndex[word].append(index)
      else:
        fileIndex[word] = [index]
    return fileIndex

  #input = {filename: [word1, word2, ...], ...}
  #res = {filename: {word: [pos1, pos2, ...]}, ...}
  def make_indices(self, termlists):
    total = {}
    for filename in termlists.keys():
      total[filename] = self.index_one_file(termlists[filename])
    return total

  #input = {filename: {word: [pos1, pos2, ...], ... }}
  #res = {word: {filename: [pos1, pos2]}, ...}, ...}
  def full_index(self):
    total_index = {}
    indie_indices = self.regdex
    for filename in indie_indices.keys():
      self.tf[filename] = {}
      for word in indie_indices[filename].keys():
        self.tf[filename][word] = len(indie_indices[filename][word])
        # TODO: use setdefault here
        if word in self.df.keys(): # TODO: remove all these .keys()
          self.df[word] += 1
        else:
          self.df[word] = 1
        if word in total_index.keys():
          # TODO: why would filename already be in total_index?
          #       even if it is, why are we appending a list to another list?
          #       just get rid of this?
          if filename in total_index[word].keys():
            total_index[word][filename].append(indie_indices[filename][word][:])
          else:
            total_index[word][filename] = indie_indices[filename][word]
        else:
          total_index[word] = {filename: indie_indices[filename][word]}
    return total_index

  def vectorize(self):
    vectors = {}
    for filename in self.filenames:
      # TODO: regdex -> reg_index
      vectors[filename] = [len(self.regdex[filename][word]) for word in self.regdex[filename].keys()]
    return vectors


  def document_frequency(self, term):
    if term in self.totalIndex.keys():
      return len(self.totalIndex[term].keys())
    else:
      return 0

  def collection_size(self):
    return len(self.filenames)

  def magnitudes(self, documents):
    # TODO: mags -> filename_to_mag
    mags = {}
    # TODO: documents -> filenames
    for document in documents:
      # TODO: vectors -> filename_to_vector
      mags[document] = pow(sum(map(lambda x: x ** 2, self.vectors[document])), .5)
    return mags

  def term_frequency(self, term, document):
    # TODO: term_frequency -> normal_term_frequency
    return self.tf[document][term] / self.mags[document] if term in self.tf[document].keys() else 0

  def populate_scores(self): #pretty sure that this is wrong and makes little sense.
    for filename in self.filenames:
      for term in self.getUniques():
        # TODO: do this normalization somewhere else
        self.tf[filename][term] = self.term_frequency(term, filename)
        if term in self.df.keys():
          self.idf[term] = self.idf_func(self.collection_size(), self.df[term])
        else:
          self.idf[term] = 0
    return self.df, self.tf, self.idf # TODO: no reason to return these values?

  def idf_func(self, N, N_t):
    if N_t != 0:
      return math.log(N / N_t)
    else:
       return 0

  def generate_score(self, term, document):
    return self.tf[document][term] * self.idf[term]

  def execute(self):
    return self.full_index()

  def reg_index(self):
    return self.make_indices(self.file_to_terms)

  def getUniques(self): # TODO: get rid of this method
    return self.totalIndex.keys()

if __name__ == '__main__':
  def test():
    index = BuildIndex(glob.glob('*.py'))
    index.basename_to_content
    print 'query mathces:', index.totalIndex['query']
    assert 0 < len(index.totalIndex['query']) < len(index.basename_to_content)

  test()
