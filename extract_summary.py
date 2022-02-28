# https://www.analyticsvidhya.com/blog/2020/12/tired-of-reading-long-articles-text-summarization-will-make-your-task-easier/#wait_approval

import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
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

def prepare_text(text):
    # add whitespace after punctuation so it tokenizes sentences properly
    # this is rarely or never needed because the data usually has space after period
    text = re.sub(r'([.?!])([a-zA-Z])', r'\1 \2', text) 

    # add period before linebreaks
    return re.sub(r'([a-zA-Z"):/])\n', r'\1.\n', text) # or maybe ([^.!?\n])(\n)

def count_words(sentence):
    # all words except stopwords
    sentence = re.sub('[^a-zA-Z]', ' ', sentence)
    sentence_list = sentence.strip()
    stopword_count = 0
    for word in sentence_list:
        if word.lower() in stopwords:
            stopword_count += 1

    return len(sentence_list) - stopword_count

database = 'db/data.db'
conn = create_connection(database)
cur = conn.cursor()

text = ''
post = 2166 # 1014 1041 41? 2166
for row in cur.execute('''SELECT reply_body FROM replies WHERE post_id = ? ORDER BY reply_id''', (post, )):
    # get text with stripped whitespaces
    #print([x.strip() for x in row[0].split('\n')])
    lines = row[0].split('\n')
    for line in lines:
        text += line.strip() + '\n'
cur.execute('''SELECT post_title, post_body FROM posts WHERE post_id = ?''', (post, ))
post_data = cur.fetchone()
post_text = post_data[0] + '\n' + post_data[1]
conn.close()

# replace everything except letters for counting frequency
cleaned_text = re.sub('[^a-zA-Z]', ' ', text)

text = prepare_text(text)
stemmer = PorterStemmer()
stopwords = set(stopwords.words("english"))

# count word frequency
frequencies = dict()
for word in word_tokenize(cleaned_text):
    word = word.lower()    
    if not word in stopwords:
        word = stemmer.stem(word, to_lowercase=False)
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
    # turn sentence into list of stemmed words
    stemmed_sentence = [stemmer.stem(token, to_lowercase=True) for token in word_tokenize(sentence)]    
    # score = 0
    for word, freq in frequencies.items():        
        if word in stemmed_sentence: # e.g. 'guy' will not return true for ['guys', ], which should be fine because stemmed?
            if sentence in sentence_scores:
                sentence_scores[sentence] += freq
            else:
                sentence_scores[sentence] = freq
    if sentence in sentence_scores:
        score = sentence_scores[sentence]
        count = count_words(sentence)
        #count = len(sentence.strip())
        #print(sentence, str(score) , str(count))            
        sentence_scores[sentence] = score + 2 * (score / count)
        #print(sentence, sentence_scores[sentence], (len(sentence.split())), end='\n\n')            
#for key, value in sorted(sentence_scores.items(), key=lambda item: item[1]):
#    print(key, value) 
#print(sentence_scores.items())

n = 6
# might throw an error if there happens to be the same sentence twice
summary_sentences = [x[0] for x in sorted(sentence_scores.items(), reverse=True, key=lambda item: item[1])]
summary = '\n'.join(summary_sentences[:n])
print(summary)



