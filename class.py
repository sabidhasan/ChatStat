import re, datetime, numpy, json, nltk, pickle, sys, math

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
  def __init__(self, raw_messages, mood_training_strength = 1000):
    if raw_messages is None:
      raise InputError("No messages provided")

    self.raw_messages = raw_messages
    self.authors = make_authors(raw_messages)
    self.parsed_messages = self.parse_messages()
    self.make_leave_counts()
    self.populate_enumerable_properties()
    self.message_classifier = MessageSentiment(mood_training_strength)

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
    return sorted(self.authors, key=lambda x: x.get_avg_response_time)
  
  @property
  def total_number_of_posts(self):
    return len(self.parsed_messages)

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
    return sorted([{'author': a, 'message_mood': data} for (a, data) in ret.items()], key=lambda x: x['message_mood']['negativity_ratio'])

  def classify_messages(self):
    if input("This may take awhile for a lot of messages. Proceed? [y / _n_]") == "y":
      one_bar = round(self.total_number_of_posts / 20)
      for (i, msg) in enumerate(self.parsed_messages):
        msg.mood = self.message_classifier.get_mood(msg.text)
        progress = '#' * math.floor(i / one_bar) + ' ' * (19 - (round(i / one_bar)))
        sys.stdout.write("Classifying Messages [{}]      {:06d}/{:06d}\r".format(progress, i+1, self.total_number_of_posts))
        sys.stdout.flush()
      print("\n")
    else:
      print("Aborting")
      
class Author:
  """Class representing authors"""
  def __init__(self, name):
    self.name = name
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
      return round(sum(self._time_deltas) / 0) #len(self._time_deltas))
    except:
      raise ZeroDivisionError('Cannot calculate average response time, as no messages from', self.name)

  def __repr__(self):
    return "<ChatParticipant %s>" % self.name

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

  def __repr__(self):
    return "<MessageObject %s>" % self.text

class MessageSentiment:
  """Generate mood sentiments for messages"""
  MINIMUM_CERTAINTY_PROBABILITY = 0.85
  TRAINING_SET_SIZE = 5000

  try:
    STOP_WORDS = set(nltk.corpus.stopwords.words('english'))
  except:
    nltk.download('stopwords')
    STOP_WORDS = set(nltk.corpus.stopwords.words('english'))

  def __init__(self, training_size = 5000):
    """Generates the classifier for NB analysis of messages"""
    self.TRAINING_SET_SIZE = training_size
    self.tweets = self.make_tweets()
    self.word_features = self.make_word_features()
    self.classifier = self.get_saved_classifier()
    if self.classifier is None:
      # Must generate new classifier
      self.classifier = self.generate_classfier_from_twitter()
      self.save_classifier()

  def make_tweets(self):
    raw_tweets = []
    with open('negative_tweets.json') as txt:
      for line in txt.readlines()[:self.TRAINING_SET_SIZE]:
        tup = (json.loads(line)['text'], 'negative')
        raw_tweets.append(tup)
    with open('positive_tweets.json') as txt:
      for line in txt.readlines()[:self.TRAINING_SET_SIZE]:
        tup = (json.loads(line)['text'], 'positive')
        raw_tweets.append(tup)
    # Combine negative and positive tweets
    parsed_tweets = []
    for (words, sentiment) in raw_tweets:
      words_filtered = [e.lower() for e in words.split() if self.is_real_word(e)]
      parsed_tweets.append((words_filtered, sentiment))
    # Make and return word features
    return parsed_tweets

  def is_real_word(self, word):
    return len(word) >= 3 and word not in self.STOP_WORDS

  def make_word_features(self):
    wordlist = []
    for (words, sentiment) in self.tweets:
      wordlist.extend(words)
    return nltk.FreqDist(wordlist).keys()

  def get_saved_classifier(self):
    """Return memozied data; if none exists, then make empty DB"""
    with open("classifier.pkl", "rb") as pkl_db:
      memoized_data = pickle.load(pkl_db)
      if memoized_data['classifier'] is not None:
        return memoized_data['classifier']
    return None

  def generate_classfier_from_twitter(self):
    print("Generating training set...")
    training_set = nltk.classify.apply_features(self.extract_features, self.tweets)
    return nltk.NaiveBayesClassifier.train(training_set)

  def extract_features(self, document):
    document_words = set(document)
    features = {}
    for word in self.word_features:
      features['contains(%s)' % word] = (word in document_words)
    return features

  def save_classifier(self):
    with open("classifier.pkl", "wb") as pkl_db:
      print('Pickling classifier')
      pickle.dump({'classifier': self.classifier}, pkl_db)

  def classify_text(self, text_features):
    prob = self.classifier.prob_classify(text_features)
    (prob_pos, prob_neg) = prob.prob('positive'), prob.prob('negative')
    
    if prob_neg > self.MINIMUM_CERTAINTY_PROBABILITY:
      classification = "negative"
    elif prob_pos > self.MINIMUM_CERTAINTY_PROBABILITY:
      classification = "positive"
    else:
      classification = "neutral"

    return (classification, max(prob_neg, prob_pos))

  def get_mood(self, text):
    parsed_text = [word for word in text.split() if self.is_real_word(word)]
    return self.classify_text(self.extract_features(parsed_text))



# with open('chat.txt') as data:
#   raw_data = data.readlines()
#   x = ChatStat(raw_data)
#   x.classify_messages()
#   print(x.average_author_sentiment)
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
