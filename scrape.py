import praw
import pandas as pd
import sqlite3
from sqlite3 import Error
import os
from dotenv import load_dotenv

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def insert_post(post):
    sql = '''INSERT INTO posts(post_title, post_body, post_reddit_id)
            VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, post)

def insert_comment(reply):
    sql = '''INSERT INTO replies(reply_body, reply_reddit_id, reply_parent)
            VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, reply)

# load .env variables
load_dotenv()

reddit = praw.Reddit(
    client_id = os.environ.get('client_id'),
    client_secret = os.environ.get('client_secret'),
    password = os.environ.get('password'),
    user_agent = os.environ.get('user_agent'),
    username = os.environ.get('username'),
)

database = 'db/data.db'
conn = create_connection(database)

min_comments = 30 # includes whole comment forest
max_comments = 150 # top level comments only

try:
    for post in reddit.subreddit('askscience').top(limit=9000):
        print(post)
        #continue
        if not post.stickied and post.num_comments >= min_comments:
            with conn: # either commits or rolls back
                try:
                    insert_post((post.title, post.selftext, post.id))
                except sqlite3.IntegrityError:
                    print("Post already exists in database.")
                    continue
            
                post.comment_sort = 'top'     
                # not sure which amount is good for limit
                # None replaces all MoreComments instances with more comments
                # 0 *removes* all the instances?
                post.comments.replace_more(limit=max_comments - 10) 
                comments = post.comments
                if len(comments) < min_comments: # len(comments) = number of top_level_comments
                    conn.rollback() # without this, post would get commited but not replies
                else:
                    for top_level_comment in comments[:max_comments]:
                        if top_level_comment.stickied: # because stickied comments tend to be the same stuff
                            continue                    
                        #if top_level_comment.score < 0:
                        #    break
                        insert_comment((top_level_comment.body, top_level_comment.id, top_level_comment.link_id))
    conn.close()     
except KeyboardInterrupt:
    conn.rollback()
    conn.close()         
    print("Quit by user")  

# select posts that don't have any reply
# SELECT COUNT(*) FROM posts WHERE 't3_' || post_reddit_id not in (SELECT reply_parent FROM replies);
# select replies that aren't related to any post
# SELECT COUNT(*) FROM replies WHERE reply_parent not in (SELECT 't3_' || post_reddit_id FROM posts);



#posts_panda = []
#comments_panda = []   
#comments_panda.append([top_level_comment.id, top_level_comment.body])# ,top_level_comment.link_id])
#posts_panda.append([post.id, post.title, post.selftext, post.num_comments])        
#posts_panda = pd.DataFrame(posts_panda,columns=['id', 'title', 'body', 'comments'])
#comments_panda = pd.DataFrame(comments_panda, columns=['id', 'body',])# 'link_id'])     
#print(posts_panda)
#print(comments_panda)

