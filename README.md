ChatStat
========

What is ChatStat?
-------------------
ChatStat is a Python module for getting some statistics about WhatsApp group chats. It helps answer questions such as:

- What days of the week, or months of the year was chat most active?
- Who sent the most messages?
- Who wrote the longest and shortest messages?
- Who 'killed' the chat with their messages?

Also, a *machine learning* training set and model are included to classify messages as positive, negative or neutral. This answers questions like:

- When was the chat sentiment the most positive/negative?
- Who are the most positive/negative people in chat?
 

Requirements
--------------
ChatStat was developed and tested on Python 3.7, but should run fine on any Python 3.x version. You can easily have multiple Python versions (2 and 3) installed on the same system.

The required `tensorflow` dependency is most easily installed using Anaconda. Obtain Anaconda from https://www.anaconda.com/download/, and install according to its instructions. Then install `tensorflow` (if needed, create an environment and activate it first):
```
conda install -c conda-forge nltk_data
```

Other requirements are:
- nltk
- numpy
- matplotlib
- jupyter (comes with Anaconda)

These requirements must be installed before using ChatStat. After cd-ing into the working directory, install the requirements using:

```
pip install -r requirements.txt
```


Quick Start
-------------
Clone the repository into your working directory:

```
git clone https://github.com/sabidhasan/ChatStat.git
```

Install the requirements (see above, using `pip install -r requirements.txt`). Demonstration with a sample chat is shown in `Sample Usage.ipynb`, which may be run by running *jupyter* (Anaconda comes with jupyter installed). Alternatively, it may be installed separately using:

```conda install jupyter```

To instantiate ChatStat, use raw data from a WhatsApp chat backup. This may be generated on the Android/iOS versions of WhatsApp by **Exporting** the chat. The ChatStat object contains numerous properties and methods for working with messages.

```python
# Read raw data from file
with open('chat_text.txt', 'rb') as data:
  raw_data = data.readlines()

# instantiate ChatStat object
chat_data = ChatStat(raw_data)

# Some of the properties available
chat_data.authors                         # List of all participants in chat
chat_data.messages_by_month               # Message count by month (or messages_by_day / time)
chat_data.convo_killer                    # List of participants by average silence time
chat_data.leave_counts                    # How often people leave?
```

To work with the message classification, the messages must be classified first. This may take ~5 minutes, depending on number of messages.

```
chat_data.classify_messages()
chat_stat.average_author_sentiment        # Returns list of authors by positive vs. negative sentiment
```


To Do
-----
- Plot sample time vs. average mood (pos/neg sentiment) graph
- If the pickle file does not exist, then error occurs; instead, the pickle file should be regenerated
- Tests


License
---------
ChatStat is licensed under the terms of the MIT License (see the file LICENSE).