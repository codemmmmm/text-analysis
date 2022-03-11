import psycopg2
import json

def create_connection():
    """ create a database connection to the postgresql database
        specified by db_file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="sumviz_to_insert", # sumviz_no_summary db has api_summary table truncated
            user="postgres",)
        return conn
    except Error as e:
        print(e)
    return conn

conn = create_connection()
cur = conn.cursor()
#cur.execute()

# insert model data
# describe the model version in the abstract column
model_name = 'sumex1'
title = 'Simple sentence extraction summarization using word frequency'
abstract = 'First version, before fixing a big bug in the word count function, probably used sentence_scores[sentence] = score + 2 * (score / count)'
sql_insert_model = '''INSERT INTO api_smodel (name, title, abstract, human_evaluation, url)
            VALUES
            (%s, %s, %s,
            '',
            '');'''
#cur.execute(sql_insert_model, (model_name, title, abstract))

# rougeL must be in double quotes because case sensitive
sql_insert_summary = '''INSERT INTO api_summary (raw, article_id, smodel_id,
            bert, compression, factual_consistency, length, novelty, rouge1,
            rouge2, "rougeL", dataset_id, entity_factuality, bi_gram_abs,
            tri_gram_abs, uni_gram_abs, four_gram_abs)
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s);'''

# read jsonl
f = 'summary-explorer/text-processing/data/document-overlap-metrics/sumex.jsonl'
model_file_lines = open(f, "r", encoding="utf-8").readlines()
model_records = [json.loads(a.strip("\n")) for a in model_file_lines]
#print(model_records[0].keys())
article_id = 0
for record in model_records:
    raw = json.dumps(record)
    #raw = record
    article_id += 1 # FK(article_id) REFERENCES api_article(id)
    bert = record['bert_score']['fmeasure']
    compression = record['compression']
    factual_consistency = 0 # what is it?
    length = 0
    novelty = 0 # for now ignored
    rouge1 = record['rouge_score']['rouge1']['fmeasure']
    rouge2 = record['rouge_score']['rouge2']['fmeasure']
    rougeL = record['rouge_score']['rougeL']['fmeasure']
    dataset_id = 1
    entity_factuality = record['entity_level_factuality']
    if entity_factuality == None:
        entity_factuality = 0
    n_gram_abs = record['ngram_abstractiveness']
    bi_gram_abs = n_gram_abs['bi_gram_abs']
    tri_gram_abs = n_gram_abs['tri_gram_abs']
    uni_gram_abs = n_gram_abs['uni_gram_abs']
    four_gram_abs = n_gram_abs['four_gram_abs']
    #print(record)
    for key, value in record.items():
        if key == 'sentences':
            #for x in value:
            #    print(x)
            for sentence in value:
                length += len([a for a in sentence['is_alpha'] if a == True])
                #for key, value in sentence.items():
                #    print(f'KEY = {key}: ', )
                #    print(value)
                #    print('"' * 10)                
        # else:
        #     print(f'KEY = {key}: ', )
        #     print(value)
        #     print('"' * 20)

    # cur.execute(sql_insert_summary, (raw, article_id, model_name, bert, compression,
    #         factual_consistency, length, novelty, rouge1, rouge2, rougeL,
    #         dataset_id, entity_factuality, bi_gram_abs, tri_gram_abs,
    #         uni_gram_abs, four_gram_abs))
    #break # for testing




conn.commit()
conn.close()




