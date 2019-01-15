from HelperFunctions import find_author
import datetime

class Message:
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
    self.mood = None
    try:
      self.text = raw_text[1].split(':')[1].strip()
    except IndexError:
      # System message (subject changed, etc.) so ignore
      self.text = ""
  
  @property
  def get_date_time_text(self):
    return self.raw_date + ' ' + self.raw_time
