import re, glob

import build_index

#input = [file1, file2, ...]
#res = {word: {filename: {pos1, pos2}, ...}, ...}
class Query:
  def __init__(self, filenames, index):
    self.filenames = filenames
    self.index = index
    self.invertedIndex = self.index.totalIndex
    self.regularIndex = self.index.regdex

  def one_word_query(self, word):
    pattern = re.compile(r'[\W_]+')
    word = pattern.sub(' ',word)
    if word in self.invertedIndex:
      return self.rank_results([filename for filename in self.invertedIndex[word]], word)
    else:
      return []

  def free_text_query(self, string):
    pattern = re.compile(r'[\W_]+')
    string = pattern.sub(' ',string)
    result = []
    for word in string.split():
      result += self.one_word_query(word)
    return self.rank_results(list(set(result)), string)

  #inputs = 'query string', {word: {filename: [pos1, pos2, ...], ...}, ...}
  #inter = {filename: [pos1, pos2]}
  def phrase_query(self, string):
    pattern = re.compile(r'[\W_]+')
    string = pattern.sub(' ',string)
    listOfLists, result = [],[]
    for word in string.split():
      listOfLists.append(self.one_word_query(word))
    setted = set(listOfLists[0]).intersection(*listOfLists)
    for filename in setted:
      temp = []
      for word in string.split():
        temp.append(self.invertedIndex[word][filename][:])
      for i in range(len(temp)):
        for ind in range(len(temp[i])):
          temp[i][ind] -= i
      if set(temp[0]).intersection(*temp):
        result.append(filename)
    return self.rank_results(result, string)

  def make_vectors(self, documents):
    vecs = {}
    for doc in documents:
      docVec = [0] * len(self.index.totalIndex)
      for ind, term in enumerate(self.index.totalIndex):
        docVec[ind] = self.index.generate_score(term, doc)
      vecs[doc] = docVec
    return vecs

  def query_vec(self, query):
    if not query.strip():
      return []
    pattern = re.compile(r'[\W_]+')
    query = pattern.sub(' ',query)
    queryList = query.split()
    queryVec = [0] * len(queryList)
    index = 0 # TODO: use ind from the loop instead
    for ind, word in enumerate(queryList):
      queryVec[index] = self.query_freq(word, query)
      index += 1
    # TODO: why cloning index.idf here?  should be `for word in queryList`?
    #       just using index.idf below should work
    queryIdf = [self.index.idf[word] for word in self.index.totalIndex]
    magnitude = pow(sum(map(lambda x: x ** 2, queryVec)), .5)
    # TODO: freq -> query_vector
    freq = self.term_freq(self.index.totalIndex, query)
    #print('THIS IS THE FREQ')
    tf = [x / magnitude for x in freq]
    final = [tf[i] * queryIdf[i] for i in range(len(self.index.totalIndex))]
    #print(len([x for x in queryIdf if x != 0]) - len(queryIdf))
    return final

  def query_freq(self, term, query):
    count = 0
    #print(query)
    #print(query.split())
    for word in query.split():
      if word == term:
        count += 1
    return count

  def term_freq(self, terms, query):
    temp = [0] * len(terms)
    for i, term in enumerate(terms):
      temp[i] = self.query_freq(term, query)
      #print(self.query_freq(term, query))
    return temp

  def dot_product(self, doc1, doc2):
    if len(doc1) != len(doc2):
      return 0
    return sum([x*y for x,y in zip(doc1, doc2)])

  def rank_results(self, resultDocs, query):
    # TODO: don't these vectors already exist in the index?
    vectors = self.make_vectors(resultDocs)
    queryVec = self.query_vec(query)
    # TODO: rename results to something more descriptive
    results = [[self.dot_product(vectors[result], queryVec), result] for result in resultDocs]
    results.sort(key=lambda x: x[0])
    results = [x[1] for x in results]
    return results

"""
Do this:
  Calculate a tf-idf score for every unique term in the collection, for each document. As in, find
  all unique terms, and for each document, got through each unique term and calculate a tf-idf
  score for it in the doc. You can do this already with the generate_score function. Doc becomes
  array of scores. Calculate a tf-idf score for every unique term in the collection for the query.
  Find the cosine distance between each document and the query, and put the results in descending
  order.
"""

if __name__ == '__main__':
  def test():
    paths = glob.glob('*.py')
    index = build_index.BuildIndex(paths)
    q = Query(paths, index)
    results1 = q.free_text_query('query dot')
    print 'results1:', results1
    assert len(results1) > 0
    results2 = q.free_text_query('query')
    print 'results2:', results2
    assert len(results2) > 0
    assert results1 != results2
  test()
