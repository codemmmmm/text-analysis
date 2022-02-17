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
        conn.execute("PRAGMA foreign_keys = 1")
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def create_tables(conn):
    sql_create_posts_table = '''CREATE TABLE IF NOT EXISTS posts (
                                        post_id integer PRIMARY KEY,
                                        post_title text NOT NULL,
                                        post_body text,
                                        post_reddit_id text UNIQUE NOT NULL
                                    ); '''

    sql_create_replies_table = '''CREATE TABLE IF NOT EXISTS replies (
                                        reply_id integer PRIMARY KEY,
                                        reply_body text NOT NULL,
                                        reply_reddit_id text UNIQUE NOT NULL,
                                        post_id integer NOT NULL,
                                        FOREIGN KEY (post_id) REFERENCES posts(post_id)
                                    ); '''                                  
    create_table(conn, sql_create_posts_table)
    create_table(conn, sql_create_replies_table)

def insert_post(post):
    # return post_id of inserted row
    sql = '''INSERT INTO posts(post_title, post_body, post_reddit_id)
            VALUES(?,?,?) RETURNING post_id'''
    cur = conn.cursor()
    cur.execute(sql, post)
    return cur.fetchone()[0]

def insert_comment(reply):
    sql = '''INSERT INTO replies(reply_body, reply_reddit_id, post_id)
            VALUES(?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, reply)

DEBUG = True

# load .env file variables
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
if not DEBUG:
    create_tables(conn)

min_comments = 30 # includes whole comment forest
max_comments = 150 # top level comments only

try:
    for post in reddit.subreddit('history').top(limit=6000):
        if DEBUG:
            print(post)
        if not post.stickied and post.num_comments >= min_comments:
            # either commits or rolls back
            with conn: 
                try:
                    post_id = insert_post((post.title, post.selftext, post.id))
                    if DEBUG:
                        print('Inserted post')
                except sqlite3.IntegrityError:
                    if DEBUG:
                        print("Post already exists in database.")
                    continue
            
                post.comment_sort = 'top'
                post.comments.replace_more(limit=max_comments - 10) 
                comments = post.comments
                if len(comments) < min_comments: # len(comments) = number of top_level_comments
                    conn.rollback() # without this, post would get commited but not replies
                else:
                    for top_level_comment in comments[:max_comments]:
                        if top_level_comment.stickied or top_level_comment.body in ('[removed]', '[deleted]'): # because stickied comments tend to be the same bot comment etc.
                            continue                    
                        #if top_level_comment.score < 0:
                        #    break
                        insert_comment((top_level_comment.body, top_level_comment.id, post_id))
                    if DEBUG:
                        print('Inserted comments')
    conn.close()     
except KeyboardInterrupt:
    conn.rollback()
    conn.close()         
    print("Quit by user")  

