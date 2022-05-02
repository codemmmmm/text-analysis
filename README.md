# text-analysis
reddit scraper, simple text summarizer

## summarizer

* for counting word frequency: 
  * remove everything except letters
  * count frequency of words (tokenized, stemmed), except stopwords
  * normalize frequency values
  
* tokenize text into sentences
* sentence -> list of stemmed words
* for each sentence:
  * sum up the frequency values for all frequent words -> score
  * CHANGES TO TRY:
    * score = score + 2 * (score / word count)
    * score = score / word count
