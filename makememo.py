import pickle

with open('classifier.pkl', 'rb') as f:
  old_classifier = pickle.load(f).get('classifier', None)

v = {
  'classifier': old_classifier,
  'messages': {}
}

with open('classifier.pkl', 'wb') as db:
  pickle.dump(v, db)