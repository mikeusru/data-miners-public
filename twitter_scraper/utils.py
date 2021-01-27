import tweepy
import re
import dataset
import json
import datetime as dt
import sys
import sqlite3

def get_api():
    with open("api_tokens.json") as json_file:
        api_keys = json.load(json_file)
    auth = tweepy.OAuthHandler(api_keys['api_key'],api_keys['api_secret_key'])
    auth.set_access_token(api_keys['access_token'],api_keys['access_token_secret'])
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return api

def connect_dataset():
    db = dataset.connect("sqlite:///tweets.db")
    return db

def clean_tweet(tweet):
    tweet = re.sub(r"Twitter for iPhone","",tweet)
    return tweet

def check_tweet(status):
    if hasattr(status, "retweeted_status"):
        return False
    if status.user.followers_count < 50:
        return False
    return True


class MyTweetCursor():

    def __init__(self, api, keywords, db):
        self.keywords = keywords
        self.db = db
        self.db_table = "tweets"
        self.dataset = "tweets.db"
        self.api = api
        self.keyword_tally = {key:0 for key in keywords}
        self.tweet_tally = 0

    def check_tweet(self, status):
        if hasattr(status, "retweeted_status"):
            return False
        if status.user.followers_count < 50:
            return False
        table = self.db[self.db_table]
        if table.find_one(id_str=status.id_str) is not None:
            return False
        return True

    def scrape_tweets(self):
        query = " OR ".join(self.keywords)
        until = dt.datetime.now().strftime("%Y-%m-%d")
        max_id, created_date = self.get_latest_id_and_date()
        print(f'Scraping Tweets until id: {max_id}, date: {created_date}')
        for status in tweepy.Cursor(self.api.search, q=query, count=100000, lang="en", since_id=max_id).items():
            self.write_to_sql(status)
        print(f'Finished scraping {self.tweet_tally} tweets. Byeee')

    def update_keyword_tally(self, tweet_keywords):
        rl = '\r'
        for key in tweet_keywords:
            self.keyword_tally[key] += 1
        if self.tweet_tally % 100 == 0:
            count_update = "".join([f'{key}: {count}\n' for key, count in self.keyword_tally.items()])
            sys.stdout.write(count_update)
            sys.stdout.write("\033[F" * len(self.keywords))

    def write_to_sql(self, status):
        if not self.check_tweet(status):
            return
        tweet_text = clean_tweet(status.text)
        tweet_keywords = self.match_keywords(tweet_text)
        if not tweet_keywords:
            return
        self.tweet_tally += 1
        self.update_keyword_tally(tweet_keywords)
        table = self.db[self.db_table]
        table.insert(dict(
            text=status.text,
            retweet_count=status.retweet_count,
            created=status.created_at,
            keywords=",".join(tweet_keywords),
            id_str=status.id_str
            ))

    def match_keywords(self, tweet_text):
            tweet_keywords = []
            for keyword in self.keywords:
                if keyword.lower() in tweet_text.lower():
                    tweet_keywords.append(keyword)
            return tweet_keywords

    def get_latest_id_and_date(self):
        conn = sqlite3.connect(self.dataset)
        c = conn.cursor()
        c.execute("SELECT id_str, created FROM tweets ORDER BY id_str DESC LIMIT 1")
        id_str, created_date = c.fetchone()
        conn.close()
        return id_str, created_date


class MyStreamListener(tweepy.StreamListener):

    def __init__(self, keywords):
        super(MyStreamListener, self).__init__()
        self.keywords = keywords
        self.db = connect_dataset()

    def on_status(self, status):
        if not check_tweet(status):
            return
        self.write_to_sql(status)

    def on_error(self, status_code):
        print(status)
        if status_code == 420:
            return False

    def write_to_sql(self, status):
        tweet_keywords = []
        has_keyword = False
        tweet_text = clean_tweet(status.text)
        for keyword in self.keywords:
            if keyword.lower() in tweet_text.lower():
                tweet_keywords.append(keyword)
                has_keyword = True
        if not has_keyword:
            return
        print(",".join(tweet_keywords))
        table = self.db["tweets"]
        table.insert(dict(
            text=status.text,
            retweet_count=status.retweet_count,
            created=status.created_at,
            keywords=",".join(tweet_keywords),
            id_str=status.id_str
            ))
