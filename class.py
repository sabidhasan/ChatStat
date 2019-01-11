import re

def make_authors(raw_messages):
  """Returns array of author objects"""
  ret = set([])
  for line in raw_messages:
    try:
      if re.match(r'\d{4}', line) and ':' in line.split(' - ')[1]:
        ret.add(line.split(' - ')[1].split(':')[0].strip())
    except IndexError:
      # line starts with 4 digits (like addresses, etc.)
      pass
  return [Author(author) for author in ret]

def find_author(name, authors):
  """ Find the author with the provided name, in the list of authors"""
  for author in authors:
    if author.name == name: return author
  raise ValueError('Author', name, 'not found.')

# def get_leave_count(raw_messages):
#   """Takes raw messages, and returns dictionary of leave counts by author."""
#   ret = {}
#   for line in raw_messages:
#     line = line.strip()
#     if re.match(r'\d{4}', line) and ' left' in line and not(':' in line.split(' - ')[1]):
#       author = line.split(' - ')[1].split(' left')[0].strip()
#       if not(author in ret):
#         ret[author] = 0
#       ret[author] += 1
#   return ret


class ChatStat:
  """Base class for ChatStat"""
  def __init__(self, raw_messages):
    if raw_messages is None:
      raise InputError("No messages provided")

    self.raw_messages = raw_messages
    self.authors = make_authors(raw_messages)
    self.parsed_messages = self.parse_messages()
    # self.leave_count = get_leave_count(raw_messages)

  def parse_messages(self):
    """Combines multi line messages into one line. Returns array of Message objects."""
    ret = []
    for line in self.raw_messages:
      line = line.strip()
      try:
        # Check for non-time stamped lines (so a multi-line message), add to prev msg
        if not(re.match(r'\d{4}', line)):
          ret[-1] += line
        # check for author (denoted by "Author: Message Text")
        elif ':' in line.split(' - ')[1]:
          ret.append(line)
      except IndexError:
        # Occurs for special messages like addresses that start with new line
        ret[-1] += line
    return [Message(idx, message_text, self.authors) for (idx, message_text) in enumerate(ret)]

class Author:
  """Class representing authors"""
  def __init__(self, name):
    self.name = name
    self.leave_count = None

  # def __str__(self):
  #   return self.name

class Message():
  """Class for individual message: date, time, mood, author, etc. """
  def __init__(self, index, raw_text, authors):
    raw_text = raw_text.split(' - ')
    datetime = raw_text[0].split(', ')
    self.index = index
    self.date = datetime[0].strip()
    # the replace is to convert "a.m." to "am"
    self.time = datetime[1].strip().replace('.', '')
    self.author = find_author(raw_text[1].split(':')[0], authors)
    try:
      self.text = raw_text[1].split(':')[1].strip()
    except IndexError:
      # System message (subject changed, etc.) so ignore
      pass
    
with open('chat.txt') as data:
  raw_data = data.readlines()
  x = ChatStat(raw_data)
  print(x.parsed_messages[5].author)