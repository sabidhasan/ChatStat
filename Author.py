class Author:
  """Class representing authors"""
  def __init__(self, name):
    self.name = name#.replace("\u202a+1 ", "").replace("\u202c", "")
    self.leave_count = 0
    # List of time deltas from messages
    self._time_deltas = []
    # Message objects for all messages from this author
    self._messages = []
    # How many times this person has mentioned other people (keys are author objects)
    self.mentions = {}
  
  @property
  def message_count(self):
    return len(self._messages)

  @property
  def longest_message(self):
    return max(self._messages, key=lambda msg: len(msg.text))

  @property
  def message_length_histogram(self):
    return [len(x.text) for x in self._messages]
  
  @property
  def message_length_stdev(self):
    return round(numpy.std(numpy.array(self.message_length_histogram)), 1)

  @property
  def shortest_message(self):
    return min(self._messages, key=lambda msg: len(msg.text))

  @property
  def get_max_response_time(self):
    return max(self._time_deltas)
  
  @property
  def get_min_response_time(self):
    return min(self._time_deltas)

  @property
  def get_avg_response_time(self):
    try:
      return round(sum(self._time_deltas) / len(self._time_deltas))
    except:
      raise ZeroDivisionError('Cannot calculate average response time, as no messages from', self.name)

  def __repr__(self):
    return "<ChatParticipant %s>" % self.name
