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
    self.enumerate_convo_killers()

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

  def enumerate_convo_killers(self):
    """Loop through messages, find who kills conversation"""

    for (idx, msg) in enumerate(self.parsed_messages):
      # Ignore first message, and if prev msg was same person
      if idx == 0: continue
      prev_msg = self.parsed_messages[idx-1]
      if msg.author == prev_msg.author: continue

      msg_dt = datetime.datetime.strptime(msg.get_date_time_text, '%Y-%m-%d %I:%M %p')
      prev_msg_dt = datetime.datetime.strptime(prev_msg.get_date_time_text, '%Y-%m-%d %I:%M %p')
      time_delta = (msg_dt - prev_msg_dt).total_seconds()
      prev_msg.author._time_deltas.append(time_delta)

  @property
  def convo_killer(self):
    return sorted(self.authors, key=lambda x: x.get_avg_response_time)

class Author:
  """Class representing authors"""
  def __init__(self, name):
    self.name = name
    self.leave_count = 0
    # List of time deltas from messages
    self._time_deltas = []
  
  @property
  def get_max_response_time(self):
    return max(self._time_deltas)
  
  @property
  def get_min_response_time(self):
    return min(self._time_deltas)

  @property
  def get_avg_response_time(self):
    try:
      return round(sum(self._time_deltas) / 0) #len(self._time_deltas))
    except:
      raise ZeroDivisionError('Cannot calculate average response time, as no messages from', self.name)

  def __str__(self):
    return self.name

class Message():
  """Class for individual message: date, time, mood, author, etc. """
  def __init__(self, index, raw_text, authors):
    raw_text = raw_text.split(' - ')
    self.index = index
    
    # DATE AND TIME RELATED STUFF
    date_time_text = raw_text[0].split(', ')
    self.raw_date = date_time_text[0].strip()
    # the replace is to convert "a.m." to "am"
    self.raw_time = date_time_text[1].strip().replace('.', '')
    self.day_of_week = datetime.datetime.strptime(self.raw_date, '%Y-%m-%d').strftime('%A')
    self.month = int(self.raw_date.split('-')[1]) - 1
    self.time = int(datetime.datetime.strptime(self.raw_time, '%I:%M %p').strftime('%H'))

    # AUTHOR
    self.author = find_author(raw_text[1].split(':')[0], authors)

    # TEXT
    self.text = None
    try:
      self.text = raw_text[1].split(':')[1].strip()
    except IndexError:
      # System message (subject changed, etc.) so ignore
      pass
    
  @property
  def get_date_time_text(self):
    return self.raw_date + ' ' + self.raw_time

with open('chat.txt') as data:
  raw_data = data.readlines()
  x = ChatStat(raw_data)
  y = (x.convo_killer)
  for author in y:
    print (author, author.get_avg_response_time)