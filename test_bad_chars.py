import unicodedata

# from lxml import etree
import xml.etree.ElementTree as ET

tree = ET.parse('test_notes/bad-chars.drawio')

# with open('test_notes/bad-chars.drawio') as f:
#   text = f.read()

# print(text[:1000])
# text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
# print(text[:1000])

# for i in range(1000):
#   print(text[i], unicodedata.category(text[i]))

# tree = etree.XML(text)
