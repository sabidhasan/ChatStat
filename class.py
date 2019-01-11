import re
# def format_message(msg, idx):
#   # return dictionary of message with author, text, date and time
#   ret = {}
#   datetime = msg.split(' - ')[0].split(', ')
#   ret['index'] = idx
#   ret['date'] = datetime[0].strip()
#   ret['time'] = datetime[1].strip().replace('.', '')
#   # the encode/decode is to remove hex characters
#   ret['author'] = strip_ascii_chars(msg.split(' - ')[1].split(':')[0])
#   try:
#     ret['text'] = msg.split(' - ')[1].split(':')[1].strip()
#   except IndexError:
#     # This is a special kind of message, so ignore it (added someone, joined, left, subject change)
#     pass
#   return ret

def parse_messages(raw_messages):
  ret = []
  for line in raw_messages:
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
  return [Message(idx, message_text) for (idx, message_text) in enumerate(ret)]

class Message:
  """Class for individual message: date, time, mood, author, etc. """
  def __init__(self):
    pass

class ChatStat:
  """Base class for ChatStat"""

  def __init__(self, raw_messages):
    if raw_messages is None:
      raise InputError("No messages provided")

    self.raw_messages = raw_messages
    # Create all messages
    self.parsed_messages = parse_messages(raw_messages)

with open('chat.txt') as data:
  raw_data = data.readlines()
  ChatStat(raw_data)