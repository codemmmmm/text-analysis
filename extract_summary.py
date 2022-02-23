# https://www.analyticsvidhya.com/blog/2020/12/tired-of-reading-long-articles-text-summarization-will-make-your-task-easier/#wait_approval

import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import re

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("PRAGMA foreign_keys = 1")
        return conn
    except Error as e:
        print(e)

    return conn

database = 'db/data.db'
conn = create_connection(database)
cur = conn.cursor()

text = ''
# 1014 1041 41? 2166
for row in cur.execute('''SELECT reply_body FROM replies WHERE post_id = 2166 ORDER BY reply_id'''):
    # get text with stripped whitespaces
    #print([x.strip() for x in row[0].split('\n')])
    lines = row[0].split('\n')
    for line in lines:
        text += line.strip() + '\n'
conn.close()

# replace everything except letters for counting frequency
cleaned_text = re.sub('[^a-zA-Z]', ' ', text)

# add whitespace after punctuation so it tokenizes sentences properly
# this is rarely or never needed because the data usually has space after period
text = re.sub(r'([.?!])([a-zA-Z])', r'\1 \2', text) 

# add period before linebreaks
text = re.sub(r'([a-zA-Z"):/])\n', r'\1.\n', text) # or maybe ([^.!?\n])(\n)

# count word frequency
stopwords = set(stopwords.words("english"))
frequencies = dict()
for word in word_tokenize(cleaned_text):
    word = word.lower()
    if not word in stopwords:
        if word in frequencies:
            frequencies[word] += 1
        else:
            frequencies[word] = 1
#for key, value in sorted(frequencies.items(), key=lambda item: item[1]):
#    print(key, value)    
max_frequency = max(frequencies.values())     
for word in frequencies.keys():
    frequencies[word] = frequencies[word] / max_frequency
#for key, value in sorted(frequencies.items(), key=lambda item: item[1]):
#    print(key, value)    


# sentence scores
sentences = sent_tokenize(text)
sentence_scores = dict()
for sentence in sentences:
    for word, freq in frequencies.items():
        if word in sentence.lower():
            if sentence in sentence_scores:
                sentence_scores[sentence] += freq
            else:
                sentence_scores[sentence] = freq
#for key, value in sorted(sentence_scores.items(), key=lambda item: item[1]):
#    print(key, value) 

n = 6
summary_sentences = [x[0] for x in sorted(sentence_scores.items(), reverse=True, key=lambda item: item[1])]
summary = '\n============\n'.join(summary_sentences[:n])
print(summary)



