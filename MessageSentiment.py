import nltk, json, pickle
from HelperFunctions import find_author

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
    return len(word) >= 3 #and word not in self.STOP_WORDS

  def make_word_features(self):
    wordlist = []
    for (words, sentiment) in self.tweets:
      wordlist.extend(words)
    return nltk.FreqDist(wordlist).keys()

  def get_saved_classifier(self):
    """Return memozied data; if none exists, then make empty DB"""
    with open("classifier.pkl", "rb") as pkl_db:
      try:
        memoized_data = pickle.load(pkl_db)
        if memoized_data['classifier'] is not None:
          return memoized_data['classifier']
      except:
        print("Saved classifier not found. Regenerating classifier...")
        return None
    print("Saved classifier not found. Regenerating classifier...")
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

