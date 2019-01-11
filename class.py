import re, datetime

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

class ChatStat:
  """Base class for ChatStat"""
  def __init__(self, raw_messages):
    if raw_messages is None:
      raise InputError("No messages provided")

    self.raw_messages = raw_messages
    self.authors = make_authors(raw_messages)
    self.parsed_messages = self.parse_messages()
    self.make_leave_counts()

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

  def make_leave_counts(self):
    """Takes raw messages, and returns dictionary of leave counts by author."""
    for line in self.raw_messages:
      line = line.strip()
      if re.match(r'\d{4}', line) and ' left' in line and not(':' in line.split(' - ')[1]):
        try:
          author = find_author(line.split(' - ')[1].split(' left')[0].strip(), self.authors)
          author.leave_count += 1
        except ValueError:
          # This was a person who never sent any messages, so ignore
          pass

  @property
  def messages_by_month(self):
    months = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0}
    for m in self.parsed_messages:
      months[m.month] += 1
    return months

  @property
  def messages_by_day(self):
    days = {}
    for m in self.parsed_messages:
      if not(m.day_of_week in days):
        days[m.day_of_week] = 0
      days[m.day_of_week] += 1
    return days

  @property
  def messages_by_time(self):
    times = {}
    for m in self.parsed_messages:
      if not(m.time in times):
        times[m.time] = 0
      times[m.time] += 1
    return times

class Author:
  """Class representing authors"""
  def __init__(self, name):
    self.name = name
    self.leave_count = 0

  def __str__(self):
    return self.name

class Message():
  """Class for individual message: date, time, mood, author, etc. """
  def __init__(self, index, raw_text, authors):
    raw_text = raw_text.split(' - ')
    self.index = index
    
    # DATE AND TIME RELATED STUFF
    date_time_text = raw_text[0].split(', ')
    raw_date = date_time_text[0].strip()
    # the replace is to convert "a.m." to "am"
    raw_time = date_time_text[1].strip().replace('.', '')
    self.day_of_week = datetime.datetime.strptime(raw_date, '%Y-%m-%d').strftime('%A')
    self.month = int(raw_date.split('-')[1]) - 1
    self.time = int(datetime.datetime.strptime(raw_time, '%I:%M %p').strftime('%H'))

    # AUTHOR
    self.author = find_author(raw_text[1].split(':')[0], authors)

    # TEXT
    self.text = None
    try:
      self.text = raw_text[1].split(':')[1].strip()
    except IndexError:
      # System message (subject changed, etc.) so ignore
      pass
    
with open('chat.txt') as data:
  raw_data = data.readlines()
  x = ChatStat(raw_data)
  print(x.messages_by_day)