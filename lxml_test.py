from os.path import join

from lxml import etree

# string to Element
with open('test_notes/test.drawio') as f:
  xml = f.read()
tree = etree.XML(xml)
print('last child: (%s) (%s)' % (tree[-1].tag, tree[-1].text))
print()

# filename to ElementTree


def recurse(root, depth):
  line = '{}{}'.format('  ' * depth, root.attrib.get('value'))
  print(line)
  for child in root:
    recurse(child, depth + 1)
print('recurse tree:')
recurse(tree, 0)
