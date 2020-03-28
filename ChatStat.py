from MessageSentiment import MessageSentiment
from Author import Author
from Message import Message
from HelperFunctions import find_author, make_authors
import re, datetime, numpy, json, nltk, pickle, sys, math

class ChatStat:
  """Base class for ChatStat"""
  __version__ = '1.0'

  def __init__(self, raw_messages, mood_training_strength = 1000):
    if raw_messages is None:
      raise ValueError("No messages provided")

    # Parse messages from bytes-like objects to string, and remove whitespace
    self.raw_messages = [msg.decode("utf-8").strip() for msg in raw_messages]
    self.authors = make_authors(self.raw_messages)
    self.parsed_messages = self.parse_messages()
    self.make_leave_counts()
    self.populate_enumerable_properties()
    self.message_classifier = MessageSentiment(mood_training_strength)

  def parse_messages(self):
    """Combines multi line messages into one line. Returns array of Message objects."""
    ret = []
    for line in self.raw_messages:
      try:
        # Check for non-time stamped lines (so a multi-line message), add to prev msg
        if not(re.match(r'\d{4}', line)):
          ret[-1] += line
        # check for author (denoted by "Author: Message Text")
        elif ':' in line.split(' - ')[1]:
          ret.append(line)
      except TypeError:
        continue
      except IndexError:
        # Occurs for special messages like addresses that start with new line
        ret[-1] += line
    return [Message(idx, message_text, self.authors) for (idx, message_text) in enumerate(ret)]

  def make_leave_counts(self):
    """Takes raw messages, and returns dictionary of leave counts by author."""
    for line in self.raw_messages:
      if re.match(r'\d{4}', line) and ' left' in line and not(':' in line.split(' - ')[1]):
        try:
          author = find_author(line.split(' - ')[1].split(' left')[0].strip(), self.authors)
          author.leave_count += 1
        except ValueError:
          # This was a person who never sent any messages, so ignore
          pass

  def populate_enumerable_properties(self):
    """Loop through messages, find who kills conversation, update author messages,
    and update mentions for that author
    """

    for (idx, msg) in enumerate(self.parsed_messages):
      # Update messages for author
      msg.author._messages.append(msg)

      # Ignore first message, and if prev msg was same person
      if idx == 0: continue
      prev_msg = self.parsed_messages[idx-1]
      if msg.author == prev_msg.author: continue

      msg_dt = datetime.datetime.strptime(msg.get_date_time_text, '%Y-%m-%d %I:%M %p')
      prev_msg_dt = datetime.datetime.strptime(prev_msg.get_date_time_text, '%Y-%m-%d %I:%M %p')
      time_delta = (msg_dt - prev_msg_dt).total_seconds()
      prev_msg.author._time_deltas.append(time_delta)

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

  @property
  def convo_killer(self):
    sorted_authors = sorted(self.authors, key=lambda x: x.get_avg_response_time)
    return [{'author': a, 'avg_response_time': a.get_avg_response_time} for a in sorted_authors]
  
  @property
  def total_number_of_posts(self):
    return len(self.parsed_messages)

  def ashton(self):
    ret = {}
    last_auth = None
    for a in self.parsed_messages:
      if not(a.author in ret):
        ret[a.author] = 0
      if last_auth is None or last_auth != a.author:
        last_auth = a.author
        ret[a.author] += 1
    return sorted([{'author': a, 'ashton_adjusted_count': ct} for (a, ct) in ret.items()], key=lambda x: x['ashton_adjusted_count'], reverse=True)

  @property
  def post_count_by_author(self):
    return list(map(lambda x: {'author': x, 'count': x.message_count},
        sorted(self.authors, key=lambda x: x.message_count, reverse=True)))

  @property
  def longest_messages(self):
    return list(
      map(lambda x: {'author': x, 'longest_msg': x.longest_message, 'longest_msg_len': len(x.longest_message.text)},
        sorted(self.authors, key=lambda x: len(x.longest_message.text), reverse=True)))

  @property
  def shortest_messages(self):
    return list(
      map(lambda x: {'author': x, 'shortest_msg': x.shortest_message, 'shortest_msg_len': len(x.shortest_message.text)},
        sorted(self.authors, key=lambda x: len(x.shortest_message.text), reverse=False)))

  @property
  def average_author_sentiment(self):
    ret = {}
    skip_count = 0

    for author in self.authors:
      ret[author] = {'positive': 0, 'negative': 0, 'neutral': 0, 'negativity_ratio': 0}
      for msg in author._messages:
        if msg.mood is None:
          skip_count += 1
        else:
          ret[author][msg.mood[0]] += 1
      try:
        ret[author]['negativity_ratio'] = ret[author]['negative'] / ret[author]['positive']
      except ZeroDivisionError:
        ret[author]['negativity_ratio'] = 0
    if skip_count != 0:
      print("{} messages were skipped, as they have not been classified".format(skip_count))
    return sorted([{'author': a, 'message_mood': data} for (a, data) in ret.items()], key=lambda x: x['message_mood']['negativity_ratio'], reverse=True)

  @property
  def leave_counts(self):
    x = [{'author': a.name, 'rage_quit_count': a.leave_count} for a in self.authors]
    return sorted(x, key=lambda x: x['rage_quit_count'])

  def classify_messages(self):
    if input("This may take awhile for a lot of messages. Proceed? [y / (n)]") == "y":
      one_bar = round(self.total_number_of_posts / 20)
      for (i, msg) in enumerate(self.parsed_messages):
        msg.mood = self.message_classifier.get_mood(msg.text)
        progress = '#' * math.floor(i / one_bar) + ' ' * (19 - (round(i / one_bar)))
        sys.stdout.write("Classifying Messages [{}]      {:06d}/{:06d}\r".format(progress, i+1, self.total_number_of_posts))
        sys.stdout.flush()
      print("\n")
    else:
      print("Aborting message classification")

  def __repr__(self):
    return "<ChatStat Object: {} messages>".format(len(self))


  def __len__(self):
    return self.total_number_of_posts

# with open('chat.txt') as data:
#   raw_data = data.readlines()
#   x = ChatStat(raw_data)
#   print(x.messages_by_month)
#   x.classify_messages()
  # print(x.average_author_sentiment)
  # for msg in x.parsed_messages:
  #   print (msg.text[0:50], "\t", msg.mood)
  # print(x.authors[7].message_length_histogram)
  # print (len(x.authors[7].message_length_histogram))
  # y = MessageSentiment()
  # print (x.authors[7].message_length_stdev)
  # for author in x.authors:
  #   print(author.name, "\n", len(author.longest_message.text), "\n", author.longest_message.text,"\n\n")



# What can be done:

# messages_by_month
# messages_by_day
# messages_by_time
# convo_killer
# total_number_of_posts
# post_count_by_author

# for any author::::
# message_count
# longest_message
# shortest_message
# get_max_response_time
# get_min_response_time
# get_avg_response_time


# plot leave count vs messages sent

# import matplotlib.pyplot as plt
# with open('chat2.txt') as data:
#   raw_data = data.readlines()
#   messages = ChatStat(raw_data)

# print(messages.ashton())